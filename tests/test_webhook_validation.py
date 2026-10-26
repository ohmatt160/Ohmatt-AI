import pytest
from fastapi import HTTPException

from app.routes.webhooks import _decode_json_object


@pytest.mark.parametrize("body", [b"", b"not-json", b"[]", b"null", b"\xff"])
def test_webhook_rejects_invalid_or_non_object_json(body):
    with pytest.raises(HTTPException) as error:
        _decode_json_object(body)

    assert error.value.status_code == 400
    assert error.value.detail == "Invalid webhook payload"


def test_webhook_accepts_json_object():
    assert _decode_json_object(b'{"event":"ok"}') == {"event": "ok"}
