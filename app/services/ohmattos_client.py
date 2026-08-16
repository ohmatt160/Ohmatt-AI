from dataclasses import dataclass
from typing import Any

import requests

from app.config import settings


class OhmattOSError(RuntimeError):
    """Base error for the server-to-server OhmattOS contract."""


class OhmattOSTransientError(OhmattOSError):
    """The request is safe to retry with the same idempotency key."""


class OhmattOSPermanentError(OhmattOSError):
    """The request must be corrected before it can be retried."""


@dataclass(frozen=True)
class QueuedMessage:
    message_id: str
    status: str
    deduplicated: bool


class OhmattOSClient:
    def __init__(self):
        self.base_url = settings.OHMATTOS_BASE_URL.rstrip("/")
        self.app_id = settings.OHMATTOS_APP_ID.strip()
        self.api_key = settings.OHMATTOS_API_KEY.strip()
        self.timeout = (
            settings.OHMATTOS_CONNECT_TIMEOUT_SECONDS,
            settings.OHMATTOS_READ_TIMEOUT_SECONDS,
        )

    def queue_notification(
        self,
        *,
        user_id: str,
        channel_type: str,
        content: dict[str, Any],
        idempotency_key: str,
        template_id: str | None = None,
    ) -> QueuedMessage:
        if not settings.OHMATTOS_ENABLED:
            raise OhmattOSPermanentError("OhmattOS integration is disabled")
        if not self.base_url or not self.app_id or not self.api_key:
            raise OhmattOSPermanentError("OhmattOS integration is incomplete")

        payload = {
            "app_id": self.app_id,
            "user_id": str(user_id),
            "channel_type": channel_type,
            "template_id": template_id,
            "idempotency_key": idempotency_key,
            "content": content,
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/notifications/send",
                json=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Idempotency-Key": idempotency_key,
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise OhmattOSTransientError("OhmattOS notification request failed") from exc

        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            raise OhmattOSTransientError(
                f"OhmattOS temporarily rejected notification ({response.status_code})"
            )
        if response.status_code < 200 or response.status_code >= 300:
            raise OhmattOSPermanentError(
                f"OhmattOS rejected notification ({response.status_code})"
            )

        try:
            envelope = response.json()
            data = envelope.get("data") or {}
            message_id = str(data["message_id"])
        except (ValueError, KeyError, TypeError) as exc:
            raise OhmattOSTransientError("OhmattOS returned an invalid response") from exc

        return QueuedMessage(
            message_id=message_id,
            status=str(data.get("status") or "queued"),
            deduplicated=bool(data.get("deduplicated", False)),
        )
