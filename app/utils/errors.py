from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings


def safe_server_error_response(error_id: str, request: Request) -> JSONResponse:
    headers = {
        "X-Error-ID": error_id,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    }
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        headers["X-Request-ID"] = request_id
    if settings.is_production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return JSONResponse(
        {"detail": "Something went wrong. Please try again.", "error_id": error_id},
        status_code=500,
        headers=headers,
    )


def safe_validation_response(exc: RequestValidationError) -> JSONResponse:
    # Validation errors can contain submitted values. Return field paths and
    # stable validator codes only.
    safe_errors = [
        {"loc": list(error.get("loc", ())), "type": error.get("type", "invalid")}
        for error in exc.errors()
    ]
    return JSONResponse(
        {"detail": "The request could not be validated.", "errors": safe_errors},
        status_code=422,
    )
