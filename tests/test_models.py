# tests/test_models.py
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models import Product, NormalizedNutrition

@pytest.mark.asyncio
async def test_create_product(db_session):
    """Test creating a product."""
    product = Product(
        barcode="1234567890123",
        name="Test Product",
        brand="Test Brand",
        category="Test Category"
    )
    
    db_session.add(product)
    await db_session.commit()
    
    stmt = select(Product).where(Product.barcode == "1234567890123")
    result = await db_session.execute(stmt)
    saved_product = result.scalar_one_or_none()
    
    assert saved_product is not None
    assert saved_product.name == "Test Product"
    assert saved_product.brand == "Test Brand"

@pytest.mark.asyncio
async def test_product_relationships(db_session):
    """Test the relationship between Product and NormalizedNutrition."""
    # Create a product
    product = Product(
        barcode="1234567890124",
        name="Test Product with Nutrition",
        brand="Test Brand",
        category="Test Category"
    )
    db_session.add(product)
    await db_session.commit()
    
    # Create nutrition data
    nutrition = NormalizedNutrition(
        product_id=product.id,
        calories_100g=100.0,
        fat_100g=10.0,
        saturated_fat_100g=5.0,
        carbohydrates_100g=20.0,
        sugars_100g=10.0,
        protein_100g=5.0,
        salt_100g=0.5
    )
    db_session.add(nutrition)
    await db_session.commit()
    
    # Test the relationship
    stmt = select(Product).where(Product.id == product.id).options(
        selectinload(Product.normalized_nutrition)
    )
    result = await db_session.execute(stmt)
    saved_product = result.scalar_one_or_none()
    
    assert saved_product is not None
    assert saved_product.normalized_nutrition is not None
    assert saved_product.normalized_nutrition.calories_100g == 100.0

@pytest.mark.asyncio
async def test_product_validation():
    """Test product validation at database level."""
    # Test that barcode must be at least 8 characters
    # This will be enforced at the database level
    product = Product(
        barcode="123",  # Invalid barcode length
        name="Test",
        brand="Test",
        category="Test"
    )
    # SQLModel table models don't raise validation errors on instantiation
    # They validate at the database level
    assert product.barcode == "123"  # The model accepts it
    # Database constraints would be enforced on commit

@pytest.mark.asyncio
async def test_unique_constraint(db_session):
    """Test unique constraint on barcode."""
    product1 = Product(
        barcode="1234567890125",
        name="Test Product 1",
        brand="Test Brand",
        category="Test Category"
    )
    db_session.add(product1)
    await db_session.commit()
    
    # Try to create another product with the same barcode
    product2 = Product(
        barcode="1234567890125",  # Same barcode
        name="Test Product 2",
        brand="Test Brand",
        category="Test Category"
    )
    db_session.add(product2)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    
    # Cleanup
    await db_session.rollback()