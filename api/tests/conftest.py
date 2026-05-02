"""Pytest configuration and fixtures."""
import os

# Force dev settings for tests BEFORE importing the app
os.environ["SOLAR_ENV"] = "development"
os.environ["SOLAR_DATABASE_URL"] = "sqlite+aiosqlite:///./test_solar_core.db"
os.environ["SOLAR_API_KEYS"] = "test-key"
os.environ["SOLAR_DEBUG"] = "false"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from solar_core.config import get_ai_keys, get_settings
from solar_core.db import init_db, engine
from solar_core.main import app


@pytest_asyncio.fixture(autouse=True)
async def _reset_settings_cache():
    """Make sure settings are picked fresh from env."""
    get_settings.cache_clear()
    get_ai_keys.cache_clear()
    yield


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    """Initialize the test database before each test."""
    await init_db()
    yield
    # Drop all data after each test to keep tests isolated
    from solar_core.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}
