import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.extensions import SessionLocal, database_url
from app.models.integration_outbox import IntegrationOutbox
from app.services.ohmattos_client import (
    OhmattOSClient,
    OhmattOSPermanentError,
    OhmattOSTransientError,
)


logger = logging.getLogger(__name__)
LOCK_TIMEOUT = timedelta(minutes=5)


def should_route_to_ohmattos(*, user_id: str | int, email: str) -> bool:
    if not settings.OHMATTOS_ENABLED:
        return False
    if email.strip().lower() in settings.ohmattos_canary_emails:
        return True
    if settings.OHMATTOS_ROLLOUT_PERCENT <= 0:
        return False
    if settings.OHMATTOS_ROLLOUT_PERCENT >= 100:
        return True
    digest = hashlib.sha256(str(user_id).encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    return bucket < settings.OHMATTOS_ROLLOUT_PERCENT


def enqueue_notification(
    db: Session,
    *,
    user_id: str | int,
    purpose: str,
    channel_type: str,
    content: dict,
    idempotency_key: str | None = None,
    template_id: str | None = None,
) -> IntegrationOutbox:
    event = IntegrationOutbox(
        destination="ohmattos",
        event_type="notification.send",
        aggregate_type="user",
        aggregate_id=str(user_id),
        idempotency_key=idempotency_key or f"notification:{purpose}:{user_id}:{uuid4().hex}",
        payload={
            "user_id": str(user_id),
            "purpose": purpose,
            "channel_type": channel_type,
            "template_id": template_id,
            "content": content,
        },
        status="pending",
        available_at=datetime.utcnow(),
    )
    db.add(event)
    return event


def _claim_batch(db: Session) -> list[int]:
    now = datetime.utcnow()
    stale_before = now - LOCK_TIMEOUT
    query = (
        db.query(IntegrationOutbox)
        .filter(
            IntegrationOutbox.destination == "ohmattos",
            or_(
                (
                    (IntegrationOutbox.status == "pending")
                    & (IntegrationOutbox.available_at <= now)
                ),
                (
                    (IntegrationOutbox.status == "processing")
                    & (IntegrationOutbox.locked_at < stale_before)
                ),
            ),
        )
        .order_by(IntegrationOutbox.created_at.asc())
        .limit(settings.OHMATTOS_OUTBOX_BATCH_SIZE)
    )
    if not database_url.startswith("sqlite"):
        query = query.with_for_update(skip_locked=True)

    events = query.all()
    for event in events:
        event.status = "processing"
        event.locked_at = now
        event.attempts += 1
        event.updated_at = now
    db.commit()
    return [event.id for event in events]


def _retry_at(attempts: int) -> datetime:
    delay_seconds = min(300, 2 ** min(attempts, 8))
    return datetime.utcnow() + timedelta(seconds=delay_seconds)


def _dispatch_event(event_id: int, client: OhmattOSClient) -> None:
    db = SessionLocal()
    try:
        event = db.query(IntegrationOutbox).filter(IntegrationOutbox.id == event_id).first()
        if not event or event.status != "processing":
            return
        payload = dict(event.payload or {})
        if event.event_type != "notification.send":
            raise OhmattOSPermanentError(f"Unsupported outbox event: {event.event_type}")

        client.queue_notification(
            user_id=str(payload["user_id"]),
            channel_type=str(payload["channel_type"]),
            content=dict(payload["content"]),
            template_id=payload.get("template_id"),
            idempotency_key=event.idempotency_key,
        )
        now = datetime.utcnow()
        event.status = "processed"
        event.processed_at = now
        event.locked_at = None
        event.last_error = None
        event.updated_at = now
        db.commit()
    except OhmattOSPermanentError as exc:
        db.rollback()
        event = db.query(IntegrationOutbox).filter(IntegrationOutbox.id == event_id).first()
        if event:
            event.status = "failed"
            event.locked_at = None
            event.last_error = str(exc)[:500]
            event.updated_at = datetime.utcnow()
            db.commit()
    except (OhmattOSTransientError, KeyError, TypeError, ValueError) as exc:
        db.rollback()
        event = db.query(IntegrationOutbox).filter(IntegrationOutbox.id == event_id).first()
        if event:
            event.locked_at = None
            event.last_error = str(exc)[:500]
            event.updated_at = datetime.utcnow()
            if event.attempts >= event.max_attempts:
                event.status = "failed"
            else:
                event.status = "pending"
                event.available_at = _retry_at(event.attempts)
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Unexpected OhmattOS outbox dispatch failure", extra={"event_id": event_id})
        event = db.query(IntegrationOutbox).filter(IntegrationOutbox.id == event_id).first()
        if event:
            event.locked_at = None
            event.last_error = "unexpected dispatch failure"
            event.updated_at = datetime.utcnow()
            event.status = "failed" if event.attempts >= event.max_attempts else "pending"
            event.available_at = _retry_at(event.attempts)
            db.commit()
    finally:
        db.close()


def process_outbox_batch() -> int:
    if not settings.OHMATTOS_ENABLED:
        return 0
    claim_db = SessionLocal()
    try:
        event_ids = _claim_batch(claim_db)
    finally:
        claim_db.close()

    client = OhmattOSClient()
    for event_id in event_ids:
        _dispatch_event(event_id, client)
    return len(event_ids)


async def run_outbox_worker(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(process_outbox_batch)
        except Exception:
            logger.exception("OhmattOS outbox worker iteration failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.OHMATTOS_OUTBOX_POLL_SECONDS
            )
        except asyncio.TimeoutError:
            pass
