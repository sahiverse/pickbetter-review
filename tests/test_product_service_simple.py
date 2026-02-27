"""Simplified unit tests for ProductService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, NormalizedNutrition
from app.services.product_service import ProductService

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def product_service(mock_db_session):
    """Create a ProductService instance with a mock session."""
    return ProductService(mock_db_session)

@pytest.mark.asyncio
async def test_parse_product_data(product_service):
    """Test parsing product data from Open Food Facts API response."""
    # Sample test data
    sample_data = {
        "code": "1234567890123",
        "product_name": "Test Product",
        "brands": "Test Brand",
        "categories": "test-category",
        "nutriments": {
            "energy-kcal_100g": 150,
            "proteins_100g": 10.5,
            "carbohydrates_100g": 20.0,
            "sugars_100g": 15.0,
            "fat_100g": 5.0,
            "saturated-fat_100g": 2.0,
            "fiber_100g": 3.0,
            "salt_100g": 0.5,
            "sodium_100g": 0.2,
        },
        "nutriscore_grade": "b",
        "image_url": "http://example.com/image.jpg",
        "last_modified_t": int(datetime.now(timezone.utc).timestamp())
    }
    
    # Act
    result = await product_service._parse_product_data(sample_data)
    
    # Assert
    assert result.barcode == "1234567890123"
    assert result.name == "Test Product"
    assert result.brand == "Test Brand"
    assert result.category == "test-category"
    assert result.image_url == "http://example.com/image.jpg"
    
    # Test nutrition data
    nutrition = result.normalized_nutrition
    assert nutrition is not None
    assert nutrition.calories_100g == 150
    assert nutrition.protein_100g == 10.5
    assert nutrition.sugars_100g == 15.0
    assert nutrition.sodium_100g == 0.2
    assert nutrition.fiber_100g == 3.0

@pytest.mark.asyncio
async def test_handle_missing_nutrition(product_service):
    """Test handling of missing nutrition data."""
    # Arrange
    incomplete_data = {
        "code": "1234567890123",
        "product_name": "Incomplete Product",
        "brands": "Test Brand",
        "categories": "test-category",
        "nutriments": {},
        "nutriscore_grade": "e"
    }
    
    # Act
    result = await product_service._parse_product_data(incomplete_data)
    
    # Assert
    assert result.name == "Incomplete Product"
    assert result.normalized_nutrition is None

@pytest.mark.asyncio
async def test_per_100g_conversion(product_service):
    """Test conversion of nutrition values to per 100g."""
    # Arrange
    product_data = {
        "code": "1234567890123",
        "product_name": "Test Conversion",
        "brands": "Test Brand",
        "categories": "test-category",
        "nutriments": {
            "energy-kcal_100g": 100,
            "proteins_100g": 10,
            "sugars_100g": 5,
            "sodium_100g": 0.1,
            "fiber_100g": 2.5,
        },
        "nutriscore_grade": "b"
    }
    
    # Act
    result = await product_service._parse_product_data(product_data)
    nutrition = result.normalized_nutrition
    
    # Assert
    assert nutrition.calories_100g == 100
    assert nutrition.protein_100g == 10
    assert nutrition.sugars_100g == 5
    assert nutrition.sodium_100g == 0.1
    assert nutrition.fiber_100g == 2.5

@pytest.mark.asyncio
async def test_is_fresh(product_service):
    """Test the _is_fresh method."""
    # Test with fresh data (less than 30 days old)
    fresh_date = datetime.utcnow() - timedelta(days=15)
    assert product_service._is_fresh(fresh_date) == True
    
    # Test with stale data (more than 30 days old)
    stale_date = datetime.utcnow() - timedelta(days=35)
    assert product_service._is_fresh(stale_date) == False
    
    # Test with None date
    assert product_service._is_fresh(None) == False
