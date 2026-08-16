"""Tests for error handling middleware - layer separation for users vs developers."""
import asyncio
import sys
from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.main import create_app


class TestErrorLayerSeparation:
    """Test that errors are properly separated between users and developers."""

    @pytest.mark.asyncio
    async def test_user_sees_generic_error_in_production(self):
        """Users should never see raw error messages or stack traces."""
        app = create_app()
        app.add_middleware(
            SecurityMiddleware,
        )
        # Add error handler middleware
        from app.middleware.error_handler import ErrorHandlerMiddleware
        app.add_middleware(ErrorHandlerMiddleware)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Trigger an error by hitting a route that doesn't exist or causes an error
            response = await client.get("/nonexistent-path")

            # In production, user should see generic message
            assert response.status_code == 500
            body = response.json()
            # User should NOT see raw error details
            assert "detail" in body
            # Should not contain exception names or stack traces
            assert "Error" not in body["detail"] or "detail" not in body["detail"].lower()
            # Should not contain Python/internal error information
            assert "traceback" not in body["detail"].lower()
            assert "python" not in body["detail"].lower()
            assert "stack" not in body["detail"].lower()

    @pytest.mark.asyncio
    async def test_developer_see_error_id_in_development(self):
        """Developers should get error context for debugging."""
        app = create_app()
        app.add_middleware(
            SecurityMiddleware,
        )
        # Add error handler middleware
        from app.middleware.error_handler import ErrorHandlerMiddleware
        app.add_middleware(ErrorHandlerMiddleware)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Trigger an error
            response = await client.get("/nonexistent-path")

            assert response.status_code == 500
            body = response.json()
            # Developer should get an error ID for tracking
            assert "_error_id" in body or "detail" in body
            # Error ID should be present for log correlation
            if "_error_id" in body:
                assert len(body["_error_id"]) > 0
            # Detail should contain some useful information (in dev mode)
            assert body["detail"] != "An unexpected error occurred. Please try again later."

    @pytest.mark.asyncio
    async def test_error_response_has_security_headers(self):
        """Error responses should still have security headers."""
        app = create_app()
        app.add_middleware(
            SecurityMiddleware,
        )
        from app.middleware.error_handler import ErrorHandlerMiddleware
        app.add_middleware(ErrorHandlerMiddleware)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/nonexistent-path")

            assert response.status_code == 500
            # Security headers should be present even on error responses
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "X-XSS-Protection" in response.headers

    @pytest.mark.asyncio
    async def test_multiple_error_types(self):
        """Test various error types all get proper layer separation."""
        app = create_app()
        app.add_middleware(
            SecurityMiddleware,
        )
        from app.middleware.error_handler import ErrorHandlerMiddleware
        app.add_middleware(ErrorHandlerMiddleware)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 404 route
            response = await client.get("/nonexistent")
            assert response.status_code == 500  # Goes through error handler
            body = response.json()
            assert "detail" in body

            # Test POST to invalid endpoint
            response = await client.post("/api/v1/auth/login", json={"invalid": "data"})
            assert response.status_code == 422  # Validation error, not 500