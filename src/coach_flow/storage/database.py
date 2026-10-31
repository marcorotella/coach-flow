"""Database engine setup and asynchronous session management."""

import logging
from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from coach_flow.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine: Optional[AsyncEngine] = None
_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Lazily initializes and returns the SQLAlchemy AsyncEngine."""
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        # SQLite async connection args
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        _engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
            connect_args=connect_args,
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Returns the async session factory."""
    global _session_maker
    if _session_maker is None:
        engine = get_engine()
        _session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing transactional database sessions."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all schema tables if not existing."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized.")


async def close_db() -> None:
    """Close active engine and connection pools cleanly."""
    global _engine, _session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("Database engine closed.")
