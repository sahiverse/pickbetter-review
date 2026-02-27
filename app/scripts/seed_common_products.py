"""Seed database with common Indian products with real barcodes and data."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.product import Product
from app.models.base import Base
from datetime import datetime

# Common Indian products with real barcodes and nutrition data
COMMON_PRODUCTS = [
    # Lays Chips
    {
        "barcode": "8901262000017",
        "name": "Lays Classic Salted",
        "brand": "Lays",
        "category": "Snacks",
        "image_url": "https://m.media-amazon.com/images/I/81EWRIkN7LL.jpg",
        "ingredients_text": "Potatoes, Edible Vegetable Oil, Salt, Iodized Salt",
        "nutriments": {
            "energy-kcal_100g": 536,
            "proteins_100g": 6.7,
            "carbohydrates_100g": 50.0,
            "sugars_100g": 0.5,
            "fat_100g": 35.0,
            "saturated-fat_100g": 15.0,
            "sodium_100g": 0.8,
            "fiber_100g": 3.3
        },
        "health_grade": "D",
        "health_score": 35
    },
    {
        "barcode": "8901262000024",
        "name": "Lays American Style Cream & Onion",
        "brand": "Lays",
        "category": "Snacks",
        "image_url": "https://m.media-amazon.com/images/I/81k+VYvN7LL.jpg",
        "ingredients_text": "Potatoes, Edible Vegetable Oil, Seasoning (Onion Powder, Milk Solids, Sugar, Salt, Cream Powder)",
        "nutriments": {
            "energy-kcal_100g": 528,
            "proteins_100g": 6.5,
            "carbohydrates_100g": 52.0,
            "sugars_100g": 2.5,
            "fat_100g": 33.0,
            "saturated-fat_100g": 14.0,
            "sodium_100g": 0.9,
            "fiber_100g": 3.0
        },
        "health_grade": "D",
        "health_score": 32
    },
]


async def seed_products():
    """Seed the database with common products."""
    # Get database URL from config
    from app.config import get_settings
    settings = get_settings()
    database_url = str(settings.DATABASE_URL).replace('postgresql://', 'postgresql+asyncpg://')
    
    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check existing products
        from sqlalchemy import select
        result = await session.execute(select(Product))
        existing_products = {p.barcode for p in result.scalars().all()}
        
        # Add new products
        added_count = 0
        for product_data in COMMON_PRODUCTS:
            if product_data["barcode"] not in existing_products:
                product = Product(
                    barcode=product_data["barcode"],
                    name=product_data["name"],
                    brand=product_data["brand"],
                    category=product_data["category"],
                    image_url=product_data["image_url"],
                    ingredients_text=product_data["ingredients_text"],
                    nutriments=product_data["nutriments"],
                    health_grade=product_data["health_grade"],
                    health_score=product_data["health_score"],
                    verification_status="verified",
                    source="seed_data",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(product)
                added_count += 1
                print(f"✅ Added: {product_data['name']} ({product_data['barcode']})")
            else:
                print(f"⏭️  Skipped: {product_data['name']} (already exists)")
        
        await session.commit()
        print(f"\n🎉 Seeding complete! Added {added_count} new products.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_products())
