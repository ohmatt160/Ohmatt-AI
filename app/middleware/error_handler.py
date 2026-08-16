import asyncio
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors with proper layer separation.
    
    - Users see: Generic error message (no raw details, no stack traces)
    - Developers: Full error logged internally with request context
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_error(request, exc)
    
    async def _handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle errors with proper layer separation.
        
        - Users see: Generic error message (no raw details)
        - Developers: Full error logged internally with request context
        """
        # Log the full error for developers (with request context)
        error_id = f"err_{int(time.time())}"
        import sys
        print(f"[ERROR {error_id}] {request.method} {request.url.path}", file=sys.stderr)
        print(f"  Exception: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # Return user-friendly response
        # In all environments, never expose raw errors to users
        return JSONResponse(
            {"detail": "An unexpected error occurred. Please try again later."},
            status_code=500
        )