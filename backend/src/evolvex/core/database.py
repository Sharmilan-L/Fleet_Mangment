from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from evolvex.core.config import settings
from evolvex.core.logging import logger

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Lazy initializer for the SQLAlchemy AsyncEngine.
    Avoids opening network connections at module import time.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Lazy initializer for the async_sessionmaker factory.
    """
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


async def close_engine() -> None:
    """
    Disposes of the AsyncEngine during FastAPI application shutdown lifespan.
    """
    global _engine, _async_session_factory
    if _engine is not None:
        logger.info("Disposing SQLAlchemy AsyncEngine...")
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


async def ping_database() -> bool:
    """
    Executes a SELECT 1 query against PostgreSQL to test connectivity.
    Used by GET /api/v1/health/database readiness check.
    """
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return result.scalar() == 1


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession for request scope.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
