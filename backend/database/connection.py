"""
SmartV2X-CP Ultra — Backend Database Connection
==================================================
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings
from backend.database.models import Base

logger = logging.getLogger(__name__)

_db_url = settings.DATABASE_URL
if "postgresql" in _db_url:
    try:
        import asyncpg  # noqa: F401
    except ImportError:
        logger.warning("asyncpg not installed — falling back to SQLite")
        _db_url = "sqlite+aiosqlite:///./smartv2x_cloud.db"

engine = create_async_engine(_db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Backend cloud database tables created")
