"""Integration tests for the API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
import os

from app.main import app
from app.database import get_db, Base, DATABASE_URL
from app.models.product import Product, NormalizedNutrition

# Test database URL - use SQLite for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Create test database engine and session
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Create test client
client = TestClient(app)

# Create the tables
@pytest.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create test database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Fixture to override the database dependency
@pytest.fixture(scope="function")
async def db_session():
    """Create a clean test database for each test."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a new session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        await session.close()
        # Drop all tables after test
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

# Override the get_db dependency for testing
@pytest.fixture(scope="function")
async def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    async def _get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides = {}

# Test data
TEST_PRODUCT = {
    "barcode": "1234567890123",
    "name": "Test Product",
    "brand": "Test Brand",
    "category": "test-category",
    "nutri_grade": "A",
    "image_url": "http://example.com/image.jpg",
    "normalized_nutrition": {
        "energy_kcal_100g": 150,
        "proteins_100g": 10.5,
        "sugars_100g": 5.0,
        "sodium_100g": 0.2,
        "fiber_100g": 3.0,
        "general_health_score": 85
    }
}

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_product_endpoint(override_get_db, db_session):
    """Test getting a product by barcode (integration test)."""
    # Add a test product to the database
    product = Product(**{
        k: v for k, v in TEST_PRODUCT.items() 
        if k != 'normalized_nutrition'
    })
    nutrition = NormalizedNutrition(
        **TEST_PRODUCT["normalized_nutrition"],
        product_barcode=TEST_PRODUCT["barcode"]
    )
    
    db_session.add(product)
    db_session.add(nutrition)
    await db_session.commit()
    await db_session.refresh(product)
    
    # Test the endpoint
    response = client.get("/api/v1/products/1234567890123")
    
    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert data["barcode"] == TEST_PRODUCT["barcode"]
    assert data["name"] == TEST_PRODUCT["name"]
    assert data["normalized_nutrition"] is not None

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_product_not_found(override_get_db):
    """Test getting a non-existent product returns 404."""
    response = client.get("/api/v1/products/9999999999999")
    assert response.status_code == 404
    # FastAPI returns "Not Found" for missing endpoints
    assert "Not Found" in response.json()["detail"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "--asyncio-mode=auto"])
