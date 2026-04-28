# ==================================================================
# FORGE - DATABASE CONFIGURATION
# ==================================================================

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

# Create the asynchronous engine using the async database URL from settings
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Create an async session factory bound to the engine
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency function to get an async database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
