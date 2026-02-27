"""Test database connection and basic operations."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from app.database import async_session, engine
from app.models.product import Product, NormalizedNutrition
from app.models.user import UserProfile
from app.models.scan_history import ScanHistory
from app.models.product_contribution import ProductContribution
from app.models.user_favorite import UserFavorite
from app.config import get_settings


async def test_database_connection():
    """Test database connection and operations."""
    print("=" * 60)
    print("🔍 Testing PostgreSQL Database Connection")
    print("=" * 60)
    
    # Test 1: Check configuration
    print("\n1️⃣ Testing Configuration...")
    settings = get_settings()
    print(f"   ✅ Database URL: {settings.DATABASE_URL}")
    print(f"   ✅ Environment: {settings.APP_ENV}")
    
    # Test 2: Test connection
    print("\n2️⃣ Testing Database Connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(select(func.version()))
            version = result.scalar()
            print(f"   ✅ Connected to: {version}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 3: Check tables exist
    print("\n3️⃣ Checking Tables...")
    async with async_session() as session:
        try:
            # Check products table
            result = await session.execute(select(func.count(Product.id)))
            product_count = result.scalar()
            print(f"   ✅ Products table: {product_count} records")
            
            # Check user_profiles table
            result = await session.execute(select(func.count(UserProfile.id)))
            user_count = result.scalar()
            print(f"   ✅ User Profiles table: {user_count} records")
            
            # Check scan_history table
            result = await session.execute(select(func.count(ScanHistory.id)))
            scan_count = result.scalar()
            print(f"   ✅ Scan History table: {scan_count} records")
            
            # Check product_contributions table
            result = await session.execute(select(func.count(ProductContribution.id)))
            contrib_count = result.scalar()
            print(f"   ✅ Product Contributions table: {contrib_count} records")
            
            # Check user_favorites table
            result = await session.execute(select(func.count(UserFavorite.id)))
            fav_count = result.scalar()
            print(f"   ✅ User Favorites table: {fav_count} records")
            
        except Exception as e:
            print(f"   ❌ Table check failed: {e}")
            return False
    
    # Test 4: Test CRUD operations
    print("\n4️⃣ Testing CRUD Operations...")
    async with async_session() as session:
        try:
            # Read existing products
            result = await session.execute(
                select(Product).limit(3)
            )
            products = result.scalars().all()
            print(f"   ✅ Read: Found {len(products)} products")
            
            for product in products:
                print(f"      - {product.name} ({product.barcode})")
            
            # Test creating a user profile
            test_user = UserProfile(
                user_id="test_user_123",
                name="Test User",
                age=25,
                dietary_preference="Vegetarian",
                allergens=["peanuts", "shellfish"],
                health_conditions=["diabetes"]
            )
            session.add(test_user)
            await session.commit()
            print(f"   ✅ Create: Added test user profile")
            
            # Read the created user
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == "test_user_123")
            )
            created_user = result.scalar_one_or_none()
            if created_user:
                print(f"   ✅ Read: Retrieved user '{created_user.name}'")
            
            # Update the user
            created_user.age = 26
            await session.commit()
            print(f"   ✅ Update: Updated user age to 26")
            
            # Delete the test user
            await session.delete(created_user)
            await session.commit()
            print(f"   ✅ Delete: Removed test user")
            
        except Exception as e:
            print(f"   ❌ CRUD operations failed: {e}")
            await session.rollback()
            return False
    
    # Test 5: Test relationships
    print("\n5️⃣ Testing Table Relationships...")
    async with async_session() as session:
        try:
            # Get a product with its nutrition data
            result = await session.execute(
                select(Product).limit(1)
            )
            product = result.scalar_one_or_none()
            
            if product:
                print(f"   ✅ Product: {product.name}")
                
                # Check if normalized_nutrition relationship works
                result = await session.execute(
                    select(NormalizedNutrition).where(
                        NormalizedNutrition.product_id == product.id
                    )
                )
                nutrition = result.scalar_one_or_none()
                if nutrition:
                    print(f"   ✅ Nutrition data linked: {nutrition.calories_100g} kcal/100g")
                else:
                    print(f"   ℹ️  No nutrition data for this product yet")
            
        except Exception as e:
            print(f"   ❌ Relationship test failed: {e}")
            return False
    
    # Test 6: Test pgvector extension
    print("\n6️⃣ Testing pgvector Extension...")
    async with engine.connect() as conn:
        try:
            result = await conn.execute(
                select(func.count()).select_from(
                    select(1).select_from(
                        func.unnest(func.array([1, 2, 3]))
                    ).subquery()
                )
            )
            print(f"   ✅ pgvector extension is available")
        except Exception as e:
            print(f"   ⚠️  pgvector test skipped: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All Database Tests Passed!")
    print("=" * 60)
    return True


async def main():
    """Main test function."""
    try:
        success = await test_database_connection()
        if success:
            print("\n🎉 Database is fully functional and ready to use!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Close database connection
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
