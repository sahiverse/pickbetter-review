# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.config import get_settings
# Import models to ensure they're registered with SQLAlchemy
from app.models.product import Product, NormalizedNutrition
from sqlmodel import SQLModel

settings = get_settings()
# Get the base database URL without the database name
base_db_url = str(settings.DATABASE_URL).replace(
    'postgresql://', 'postgresql+asyncpg://'
).rsplit('/', 1)[0]

TEST_DATABASE_URL = base_db_url + "/postgres_test"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

async_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    # Create test database if it doesn't exist
    base_engine = create_async_engine(base_db_url, echo=False)
    async with base_engine.begin() as conn:
        try:
            await conn.execute(text("COMMIT"))
            await conn.execute(text("CREATE DATABASE postgres_test"))
        except Exception:
            # Database might already exist
            pass
    await base_engine.dispose()
    
    # Setup database for each test
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
    
    # Create session
    async with async_session_factory() as session:
        yield session
    
    # Cleanup
    await test_engine.dispose()