import asyncio

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.security import SecurityMiddleware


def test_credentialed_preflight_wraps_security_middleware():
    async def run_preflight():
        app = FastAPI()
        app.add_middleware(SecurityMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://ohmatt-ai-v1-0.vercel.app"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "https://ohmatt-ai-v1-0.vercel.app",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

    response = asyncio.run(run_preflight())

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ohmatt-ai-v1-0.vercel.app"
    assert response.headers["access-control-allow-credentials"] == "true"
