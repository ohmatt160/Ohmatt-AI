import logging
from uuid import uuid4
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
        error_id = uuid4().hex
        logging.getLogger("ohmatt.api").exception(
            "Unhandled request exception error_id=%s method=%s path=%s",
            error_id,
            request.method,
            request.url.path,
        )
        
        # Return user-friendly response
        # In all environments, never expose raw errors to users
        return JSONResponse(
            {"detail": "Something went wrong. Please try again.", "error_id": error_id},
            status_code=500,
            headers={"X-Error-ID": error_id},
        )
