"""FastAPI application entrypoint for Solar Core."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from solar_core import __version__
from solar_core.api.routes import connectors as connectors_routes
from solar_core.api.routes import documents as documents_routes
from solar_core.api.routes import health as health_routes
from solar_core.api.routes import process as process_routes
from solar_core.api.routes import translate_air as translate_air_routes
from solar_core.config import get_settings
from solar_core.core.exceptions import SolarCoreError
from solar_core.core.logging import get_logger, setup_logging
from solar_core.db import init_db


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    settings = get_settings()
    logger.info(
        "solar_core_startup",
        version=__version__,
        env=settings.env,
        db=settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
    )
    # Auto-create tables on dev startup. In production: use Alembic migrations.
    if settings.env == "development":
        await init_db()
    yield
    logger.info("solar_core_shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title="Solar Core",
        description="AI operational layer for the Solar ecosystem.",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS — extension and dashboard will call us from different origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [
            "chrome-extension://",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health_routes.router)
    app.include_router(process_routes.router)
    app.include_router(translate_air_routes.router)
    app.include_router(documents_routes.router)
    app.include_router(connectors_routes.router)

    # Centralised error handler
    @app.exception_handler(SolarCoreError)
    async def _solar_error_handler(request: Request, exc: SolarCoreError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": "Solar Core",
            "version": __version__,
            "docs": "/docs",
            "health": "/v1/health",
        }

    return app


app = create_app()
