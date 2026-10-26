import time
import logging
import hashlib
import re
from uuid import uuid4
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings

try:
    from redis.asyncio import Redis
except ImportError:  # Redis is required for production and optional in local dev.
    Redis = None

logger = logging.getLogger("ohmatt.http")


@dataclass(frozen=True)
class RateLimitRule:
    method: str
    path: str
    limit: int
    window_seconds: int


RATE_LIMIT_RULES = [
    RateLimitRule("POST", "/api/v1/auth/login", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/login/form", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/login/resend", 3, 60),
    RateLimitRule("POST", "/api/v1/auth/register", 3, 60),
    RateLimitRule("POST", "/api/v1/auth/verify", 5, 60),
    RateLimitRule("POST", "/api/v1/auth/password-reset/request", 3, 60),
    RateLimitRule("POST", "/api/v1/auth/password-reset/confirm", 5, 60),
    RateLimitRule("POST", "/api/v1/bank/verify-account", 10, 60),
]


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.rate_limit_checks = 0
        if settings.RATE_LIMIT_REDIS_URL and Redis is None:
            raise RuntimeError("Redis client dependency is required when RATE_LIMIT_REDIS_URL is set")
        self.redis = Redis.from_url(settings.RATE_LIMIT_REDIS_URL, decode_responses=True) if Redis and settings.RATE_LIMIT_REDIS_URL else None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = request.headers.get("x-request-id")
        if not request_id or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", request_id):
            request_id = uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        input_error = await self._validate_request_input(request)
        if input_error:
            await self._send_response(request, input_error, request_id, started, receive, send)
            return

        rate_limit_response = await self._rate_limit(request)
        if rate_limit_response:
            await self._send_response(request, rate_limit_response, request_id, started, receive, send)
            return

        response_status = 500

        async def send_with_security_headers(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
                headers = list(message.get("headers", []))
                security_headers = self._security_headers(request_id)
                security_headers.update(getattr(request.state, "rate_limit_headers", {}))
                for key, value in security_headers.items():
                    encoded_key = key.lower().encode("latin-1")
                    encoded_value = value.encode("latin-1")
                    headers = [(k, v) for k, v in headers if k.lower() != encoded_key]
                    headers.append((encoded_key, encoded_value))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_security_headers)
        finally:
            logger.info(
                "HTTP request request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                response_status,
                (time.perf_counter() - started) * 1000,
            )

    def _security_headers(self, request_id):
        headers = {
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; connect-src 'self' https:; font-src 'self' data:; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            ),
        }
        if settings.is_production:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return headers

    async def _send_response(self, request, response, request_id, started, receive, send):
        response = self._finish(request, response, request_id, started)
        await response(request.scope, receive, send)

    def _finish(self, request: Request, response, request_id: str, started: float):
        for key, value in self._security_headers(request_id).items():
            response.headers[key] = value
        for key, value in getattr(request.state, "rate_limit_headers", {}).items():
            response.headers[key] = value
        logger.info(
            "HTTP request request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    async def _validate_request_input(self, request: Request):
        content_type = request.headers.get("content-type", "")
        if request.method in {"POST", "PUT", "PATCH"} and "multipart/form-data" not in content_type:
            try:
                content_length = int(request.headers.get("content-length", "0"))
            except ValueError:
                content_length = 0
            if content_length > 1_048_576:
                return JSONResponse({"detail": "Request body is too large"}, status_code=413)
            # Do not consume the body here; route-level schemas validate content.
            # Reject oversized declared bodies before application parsing.
        return None

    async def _rate_limit(self, request: Request):
        rule = self._matching_rule(request)
        if not rule:
            return None

        client_ip = request.client.host if request.client else "unknown"
        # Only trust forwarded addresses when the immediate peer is explicitly
        # configured as a reverse proxy. Otherwise clients can spoof rate-limit IPs.
        if client_ip in settings.trusted_proxy_ips:
            forwarded = request.headers.get("x-forwarded-for", "").split(",")
            if forwarded and forwarded[0].strip():
                client_ip = forwarded[0].strip()
        ip_fingerprint = hashlib.sha256((client_ip or "unknown").encode()).hexdigest()[:24]
        key = f"ohmatt:rate:{rule.method}:{rule.path}:{ip_fingerprint}"
        now = time.time()
        if self.redis:
            window_id = int(now // rule.window_seconds)
            redis_key = f"{key}:{window_id}"
            try:
                count = await self.redis.eval(
                    "local n=redis.call('INCR',KEYS[1]); "
                    "if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; "
                    "return n",
                    1,
                    redis_key,
                    rule.window_seconds + 1,
                )
            except Exception:
                logger.exception("Shared rate limiter unavailable path=%s", rule.path)
                return JSONResponse(
                    {"detail": "Sign-in protection is temporarily unavailable. Please try again."},
                    status_code=503,
                )
            remaining = max(rule.limit - int(count), 0)
            if count > rule.limit:
                reset_at = (window_id + 1) * rule.window_seconds
                retry_after = max(1, int(reset_at - now))
                response = JSONResponse({"detail": "Too many requests. Please try again later."}, status_code=429)
                response.headers.update({
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                })
                return response
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(rule.limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int((window_id + 1) * rule.window_seconds)),
            }
            return None

        if settings.is_production:
            # Production configuration rejects this state before app startup.
            return JSONResponse({"detail": "Sign-in protection is temporarily unavailable."}, status_code=503)

        self.rate_limit_checks += 1
        if self.rate_limit_checks % 256 == 0:
            longest_window = max(item.window_seconds for item in RATE_LIMIT_RULES)
            stale_keys = [
                bucket_key
                for bucket_key, hits in self.requests.items()
                if not hits or now - hits[-1] > longest_window
            ]
            for bucket_key in stale_keys:
                self.requests.pop(bucket_key, None)
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
