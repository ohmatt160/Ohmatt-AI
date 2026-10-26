from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.utils.errors import safe_server_error_response, safe_validation_response


def make_request():
    return Request({
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test-failure",
        "raw_path": b"/test-failure",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("127.0.0.1", 1234),
    })


def test_public_server_error_is_generic_and_correlatable():
    response = safe_server_error_response("err-safe-id", make_request())
    body = response.body.decode()

    assert response.status_code == 500
    assert "err-safe-id" in body
    assert response.headers["X-Error-ID"] == "err-safe-id"
    assert "Traceback" not in body
    assert "database" not in body


def test_validation_response_does_not_echo_submitted_values():
    error = RequestValidationError([
        {"loc": ("body", "password"), "msg": "invalid", "type": "value_error"}
    ])
    response = safe_validation_response(error)

    assert response.status_code == 422
    assert b"submitted-secret" not in response.body
    assert b"The request could not be validated." in response.body
