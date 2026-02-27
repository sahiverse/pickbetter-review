"""PostgreSQL database configuration for PickBetter application."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()

# PostgreSQL connection URL with asyncpg driver
DATABASE_URL = str(settings.DATABASE_URL).replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine for PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

from sqlmodel import SQLModel

async def init_db():
    """Initialize the database (create all tables)"""
    # Import all models to ensure they're registered with SQLModel metadata
    from app.models.product import Product, NormalizedNutrition
    from app.models.user import UserProfile
    from app.models.scan_history import ScanHistory
    from app.models.product_contribution import ProductContribution
    from app.models.user_favorite import UserFavorite
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("✅ PostgreSQL database tables created successfully")

async def close_db():
    """Close the database engine"""
    await engine.dispose()
    print("✅ PostgreSQL database connection closed")