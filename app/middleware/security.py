import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


SUSPICIOUS_INPUT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"'\s+or\s+'1'\s*=\s*'1",
        r"or\s+1\s*=\s*1",
        r";\s*drop\s+table",
        r"union\s+select",
        r"--",
        r"/\*",
        r"\*/",
        r"xp_cmdshell",
    ]
]


@dataclass(frozen=True)
class RateLimitRule:
    method: str
    path: str
    limit: int
    window_seconds: int


RATE_LIMIT_RULES = [
    RateLimitRule("POST", "/api/v1/auth/login", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/login/form", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/register", 3, 60),
    RateLimitRule("POST", "/api/v1/auth/verify", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/password-reset/request", 3, 60),
    RateLimitRule("POST", "/api/v1/auth/password-reset/confirm", 5, 60),
    RateLimitRule("POST", "/api/v1/bank/verify-account", 10, 60),
]


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        input_error = await self._validate_request_input(request)
        if input_error:
            return self._with_security_headers(input_error)

        rate_limit_response = self._rate_limit(request)
        if rate_limit_response:
            return self._with_security_headers(rate_limit_response)

        response = await call_next(request)
        for key, value in getattr(request.state, "rate_limit_headers", {}).items():
            response.headers[key] = value
        return self._with_security_headers(response)

    async def _validate_request_input(self, request: Request):
        values = list(request.query_params.multi_items())
        for _, value in values:
            if self._looks_suspicious(value):
                return JSONResponse(
                    {"detail": "Invalid request input"},
                    status_code=400,
                )
        content_type = request.headers.get("content-type", "")
        if request.method in {"POST", "PUT", "PATCH"} and "multipart/form-data" not in content_type:
            body = await request.body()
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request._receive = receive
            if len(body) > 65536:
                return None
            decoded = body.decode("utf-8", errors="ignore")
            if decoded and self._looks_suspicious(decoded):
                return JSONResponse(
                    {"detail": "Invalid request input"},
                    status_code=400,
                )
        return None

    def _looks_suspicious(self, value: Any) -> bool:
        value = str(value)
        if len(value) > 1000:
            return True
        return any(pattern.search(value) for pattern in SUSPICIOUS_INPUT_PATTERNS)

    def _rate_limit(self, request: Request):
        rule = self._matching_rule(request)
        if not rule:
            return None

        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host
        key = f"{rule.method}:{rule.path}:{client_ip or 'unknown'}"
        now = time.time()
        bucket = self.requests[key]

        while bucket and now - bucket[0] > rule.window_seconds:
            bucket.popleft()

        remaining = max(rule.limit - len(bucket), 0)
        if len(bucket) >= rule.limit:
            retry_after = max(1, int(rule.window_seconds - (now - bucket[0])))
            response = JSONResponse(
                {"detail": "Too many requests. Please try again later."},
                status_code=429,
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(rule.limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(now + retry_after))
            return response

        bucket.append(now)
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(rule.limit),
            "X-RateLimit-Remaining": str(max(remaining - 1, 0)),
            "X-RateLimit-Reset": str(int(now + rule.window_seconds)),
        }
        return None

    def _matching_rule(self, request: Request):
        path = request.url.path.rstrip("/") or "/"
        for rule in RATE_LIMIT_RULES:
            if request.method.upper() == rule.method and path == rule.path:
                return rule
        return None

    def _with_security_headers(self, response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response
