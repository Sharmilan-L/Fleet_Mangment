import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://evolvex_user:evolvex_password@127.0.0.1:5433/evolvex_db"
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_postgresql_connectivity() -> None:
    """
    Real Integration Test: Verifies SELECT 1 query execution against live PostgreSQL container.
    Does NOT create tables or Alembic migrations.
    """
    database_url = os.getenv("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
    finally:
        await engine.dispose()
