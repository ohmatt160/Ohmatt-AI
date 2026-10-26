import asyncio
import logging
import os
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from app.routes import api_router
from app.config import settings
from app.extensions import init_extensions, engine, Base
from app.middleware.security import SecurityMiddleware
from app.services.integration_outbox_service import run_outbox_worker
from app.utils.errors import safe_server_error_response, safe_validation_response

logger = logging.getLogger("ohmatt.api")
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


# Static paths (if you have a frontend)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[OK] Starting {settings.PROJECT_NAME}...")
    init_extensions(app)
    outbox_stop = asyncio.Event()
    outbox_task = None
    if settings.OHMATTOS_ENABLED:
        outbox_task = asyncio.create_task(run_outbox_worker(outbox_stop))
    try:
        yield
    finally:
        outbox_stop.set()
        if outbox_task:
            await outbox_task
        print("[INFO] Shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Middleware is applied in reverse registration order. Keep CORS outermost so
    # preflight, rate-limit, security, and error responses all receive CORS headers.
    app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        error_id = uuid4().hex
        logger.error(
            "Unhandled request exception error_id=%s request_id=%s method=%s path=%s",
            error_id,
            getattr(request.state, "request_id", None),
            request.method,
            request.url.path,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return safe_server_error_response(error_id, request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.info(
            "Request validation failed method=%s path=%s",
            request.method,
            request.url.path,
        )
        return safe_validation_response(exc)
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "project": settings.PROJECT_NAME}


    # @app.get("/")
    # async def root():
    #     return {
    #         "message": f"Welcome to {settings.PROJECT_NAME}",
    #         "version": settings.VERSION,
    #         "docs": "/docs"
    #     }

    # API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Static files (if frontend exists)
    # if os.path.isdir(ASSETS_DIR):
    #     app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    if os.path.isdir(STATIC_DIR):
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app


app = create_app()
