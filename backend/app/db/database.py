"""Database session and engine management supporting asyncpg (PostgreSQL) and aiosqlite (SQLite)."""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_async_database_url(url: str) -> str:
    """Safely converts standard PostgreSQL URLs (e.g. from Render) into asyncpg-compatible URLs."""
    if not url:
        return "sqlite+aiosqlite:///./uamd.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


db_url = get_async_database_url(settings.DATABASE_URL)

engine_kwargs = {"echo": False}
# Enable pre-ping for real network databases to recycle dropped/idle connections
if not db_url.startswith("sqlite"):
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(db_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    # Ensure all models are loaded and registered with Base.metadata before creating tables
    from app.db import models  # noqa: F401
    logger.info(f"Initializing database tables: {list(Base.metadata.tables.keys())}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
