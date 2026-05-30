import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import api_router
from app.config import settings
from app.extensions import init_extensions, engine, Base


# Static paths (if you have a frontend)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[OK] Starting {settings.PROJECT_NAME}...")
    init_extensions(app)
    yield
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

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
