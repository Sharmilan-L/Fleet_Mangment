from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from evolvex.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP Client fixture bound to FastAPI application.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_engine() -> AsyncGenerator[None, None]:
    """Ensure AsyncEngine is disposed after each test to prevent loop closed errors."""
    yield
    from evolvex.core.database import close_engine

    await close_engine()
