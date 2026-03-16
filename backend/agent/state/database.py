"""Async database engine and session management.

Provides factory functions for creating the async engine and session
maker. The ``get_session`` async generator is designed for use as a
FastAPI dependency.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_engine(database_url: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL with asyncpg driver.

    Returns:
        Configured AsyncEngine with connection pooling.
    """
    if not database_url:
        raise ValueError("database_url must not be empty")

    return create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=False,
    )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine.

    Args:
        engine: The async engine to bind sessions to.

    Returns:
        An async_sessionmaker that produces AsyncSession instances.
    """
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    """Verify database connectivity at startup.

    Does NOT create tables — Alembic handles schema management.

    Args:
        engine: The async engine to test.

    Raises:
        Exception: If the database is unreachable.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("database_connection_verified")


async def get_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session, closing it when done.

    Designed for use as a FastAPI dependency via functools.partial.

    Args:
        factory: The session factory to use.

    Yields:
        An AsyncSession instance.
    """
    async with factory() as session:
        yield session
