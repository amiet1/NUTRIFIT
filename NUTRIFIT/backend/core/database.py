import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(
            settings.database_url, # Ensure this is in your config.py/env
            echo=False,
            future=True
        )
        self.async_session_maker = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            # This creates the tables based on your models
            await conn.run_sync(Base.metadata.create_all)

    async def close_db(self):
        await self.engine.dispose()

# This is the "db_manager" your other files are looking for!
db_manager = DatabaseManager()
async def get_db():
    """Dependency for getting async database sessions"""
    async with db_manager.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()