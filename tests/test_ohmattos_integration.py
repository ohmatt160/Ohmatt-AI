import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.extensions import Base
from app.models.integration_outbox import IntegrationOutbox
from app.services.integration_outbox_service import enqueue_notification, should_route_to_ohmattos
from app.services.ohmattos_client import OhmattOSClient, OhmattOSTransientError


for model_module in (
    "app.models.user",
    "app.models.country",
    "app.models.continent",
    "app.models.language",
    "app.models.transaction",
    "app.models.task",
    "app.models.bank_connection",
    "app.models.bank_account",
    "app.models.activity",
    "app.models.activity_log",
    "app.models.bank_provider",
    "app.models.bank_transaction",
    "app.models.blacklist",
    "app.models.session",
    "app.models.messages",
    "app.models.insight",
    "app.models.finance",
):
    __import__(model_module)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def configure_client(monkeypatch):
    monkeypatch.setattr(settings, "OHMATTOS_ENABLED", True)
    monkeypatch.setattr(settings, "OHMATTOS_BASE_URL", "https://ohmattos.example")
    monkeypatch.setattr(settings, "OHMATTOS_APP_ID", "app-123")
    monkeypatch.setattr(settings, "OHMATTOS_API_KEY", "ohm_abcdefghijklmnopqrstuvwxyz123456")


def test_client_uses_server_key_and_idempotency(monkeypatch):
    configure_client(monkeypatch)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(
            202,
            {
                "success": True,
                "data": {
                    "message_id": "message-1",
                    "status": "queued",
                    "deduplicated": False,
                },
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)
    result = OhmattOSClient().queue_notification(
        user_id="42",
        channel_type="email",
        content={"to": "internal@example.com", "subject": "Verify", "body": "Body"},
        idempotency_key="verification-42",
    )

    assert result.message_id == "message-1"
    assert captured["url"] == "https://ohmattos.example/api/v1/notifications/send"
    assert captured["headers"]["X-API-Key"] == settings.OHMATTOS_API_KEY
    assert captured["headers"]["Idempotency-Key"] == "verification-42"
    assert captured["json"]["app_id"] == "app-123"
    assert captured["json"]["idempotency_key"] == "verification-42"


def test_client_classifies_provider_outage_as_retryable(monkeypatch):
    configure_client(monkeypatch)
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(503, {"error": "unavailable"}),
    )

    try:
        OhmattOSClient().queue_notification(
            user_id="42",
            channel_type="email",
            content={"to": "internal@example.com", "subject": "Verify", "body": "Body"},
            idempotency_key="verification-42",
        )
        assert False, "expected a transient error"
    except OhmattOSTransientError:
        pass


def test_notification_intent_is_persisted_in_the_outbox():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[IntegrationOutbox.__table__])
    db = sessionmaker(bind=engine)()
    try:
        event = enqueue_notification(
            db,
            user_id=42,
            purpose="email-verification",
            channel_type="email",
            content={"to": "internal@example.com", "subject": "Verify", "body": "Body"},
            idempotency_key="verification-42",
        )
        db.commit()
        db.refresh(event)

        assert event.status == "pending"
        assert event.destination == "ohmattos"
        assert event.payload["purpose"] == "email-verification"
        assert event.idempotency_key == "verification-42"
    finally:
        db.close()


def test_rollout_defaults_to_internal_canary_only(monkeypatch):
    monkeypatch.setattr(settings, "OHMATTOS_ENABLED", True)
    monkeypatch.setattr(settings, "OHMATTOS_CANARY_EMAILS", "internal@example.com")
    monkeypatch.setattr(settings, "OHMATTOS_ROLLOUT_PERCENT", 0)

    assert should_route_to_ohmattos(user_id=1, email="internal@example.com")
    assert not should_route_to_ohmattos(user_id=2, email="customer@example.com")

    monkeypatch.setattr(settings, "OHMATTOS_ROLLOUT_PERCENT", 100)
    assert should_route_to_ohmattos(user_id=2, email="customer@example.com")
