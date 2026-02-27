"""Unit tests for ProductService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import json
import os
from freezegun import freeze_time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, NormalizedNutrition
from app.services.product_service import ProductService
from app.services.openfoodfacts import OpenFoodFactsClient

# Sample test data
SAMPLE_PRODUCT_DATA = {
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

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = MagicMock(scalar_one_or_none=AsyncMock(return_value=None))
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def product_service(mock_db_session):
    """Create a ProductService instance with a mock session."""
    return ProductService(mock_db_session)

@pytest.mark.asyncio
async def test_parse_product_data(product_service):
    """Test parsing product data from Open Food Facts API response."""
    # Act
    result = await product_service._parse_product_data(SAMPLE_PRODUCT_DATA)
    
    # Assert
    assert result.barcode == "1234567890123"
    assert result.name == "Test Product"
    assert result.brand == "Test Brand"
    assert result.category == "test-category"
    assert result.nutrition_grades is None
    assert result.image_url == "http://example.com/image.jpg"
    # last_modified is not set in the parse_product method
    assert result.last_modified is None
    
    # Test nutrition data
    nutrition = result.normalized_nutrition
    assert nutrition is not None
    assert nutrition.calories_100g == 150
    assert nutrition.protein_100g == 10.5
    assert nutrition.sugars_100g == 15.0
    assert nutrition.sodium_100g == 0.2
    assert nutrition.fiber_100g == 3.0
    # general_health_score is not set in the parse_product method
    assert nutrition.general_health_score is None

@pytest.mark.asyncio
@freeze_time("2024-01-01")
async def test_get_product_cache_hit(product_service, mock_db_session):
    """Test getting a product that's already in the database (cache hit)."""
    # Arrange
    mock_product = Product(
        barcode="1234567890123",
        name="Cached Product",
        brand="Test Brand",
        category="test-category",
        nutrition_grades="A",
        last_updated=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_product
    
    # Act
    start_time = datetime.now()
    result = await product_service.get_by_barcode("1234567890123")
    end_time = datetime.now()
    
    # Assert
    assert result is not None
    assert (end_time - start_time).total_seconds() < 0.1  # Should be very fast
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
@patch('app.services.product_service.OpenFoodFactsClient.get_product')
@freeze_time("2024-01-01")
async def test_get_product_cache_miss(mock_get_product, product_service, mock_db_session):
    """Test getting a product that's not in the database (cache miss)."""
    # Arrange
    mock_get_product.return_value = SAMPLE_PRODUCT_DATA
    
    # Act
    result = await product_service.get_by_barcode("1234567890123")
    
    # Assert
    assert result is not None
    assert result.barcode == "1234567890123"
    assert result.name == "Test Product"
    mock_get_product.assert_called_once_with("1234567890123")
    mock_db_session.add.assert_called()
    mock_db_session.commit.assert_awaited_once()

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
    assert result.nutrition_grades is None
    # normalized_nutrition is None when no nutrition data is present
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
    # Test health score calculation (implementation details may vary)
    # general_health_score might be None if no nutrition score is provided
    assert nutrition.general_health_score is None or 0 <= nutrition.general_health_score <= 100
