"""Database seeding script for Populating Products."""
import asyncio
import argparse
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from tqdm import tqdm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.database import get_db, DATABASE_URL
from app.services.product_service import ProductService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSeeder:
    """Handles database seeding operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the seeder with a database session."""
        self.db = db
        self.service = ProductService(db)
    
    async def seed_products(self, category: str, limit: int = 100) -> Dict[str, Any]:
        """
        Seed the database with products from Open Food Facts.
        
        Args:
            category: Product category to seed (e.g., 'beverages', 'snacks')
            limit: Maximum number of products to fetch
            
        Returns:
            Dictionary with seeding results
        """
        logger.info(f"Starting to seed up to {limit} products from category: {category}")
        
        try:
            # Initialize progress bar
            with tqdm(total=limit, desc=f"Seeding {category}", unit="product") as pbar:
                # Use the ProductService to fetch and save products
                result = await self.service.seed_from_openfoodfacts(
                    category=category,
                    limit=limit
                )
                
                # Update progress bar
                pbar.update(limit)
                
                return {
                    "status": "success",
                    "category": category,
                    "total_processed": result["total_processed"],
                    "added": result["added"],
                    "updated": result["updated"],
                    "skipped": result["skipped"],
                    "errors": result["errors"],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error during seeding: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "category": category,
                "timestamp": datetime.utcnow().isoformat()
            }


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Seed the database with products from Open Food Facts.')
    parser.add_argument(
        '--category', 
        type=str, 
        help='Product category to seed (e.g., beverages, snacks)'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=100,
        help='Maximum number of products to fetch (default: 100)'
    )
    return parser.parse_args()


async def interactive_mode() -> tuple[str, int]:
    """Run the seeder in interactive mode."""
    print("\n🚀 Database Seeder - Interactive Mode")
    print("=" * 40)
    
    # Get category
    while True:
        category = input("\n📋 Enter product category (e.g., beverages, snacks): ").strip()
        if category:
            break
        print("❌ Category cannot be empty. Please try again.")
    
    # Get limit with validation
    while True:
        limit_input = input(f"\n🔢 Enter number of products to fetch (default: 100, max: 1000): ").strip()
        if not limit_input:
            limit = 100
            break
        try:
            limit = int(limit_input)
            if 1 <= limit <= 1000:
                break
            print("❌ Please enter a number between 1 and 1000.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    return category, limit


async def main():
    """Main entry point for the seeder."""
    args = parse_arguments()
    
    # If no category provided, run in interactive mode
    if not args.category:
        try:
            category, limit = await interactive_mode()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Operation cancelled by user.")
            return
    else:
        category = args.category
        limit = args.limit
    
    # Initialize database connection
    db = AsyncSession(bind=create_async_engine(DATABASE_URL))
    seeder = DatabaseSeeder(db)
    
    try:
        print(f"\n🌱 Seeding up to {limit} products from category: {category}")
        print("⏳ This may take a few minutes...")
        
        # Run the seeder
        start_time = datetime.now()
        result = await seeder.seed_products(category, limit)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Print results
        print("\n" + "=" * 50)
        if result["status"] == "success":
            print("✅ Seeding completed successfully!")
            print(f"📊 Results for category: {category}")
            print(f"   - Total processed: {result['total_processed']}")
            print(f"   - Added: {result['added']}")
            print(f"   - Updated: {result['updated']}")
            print(f"   - Skipped: {result['skipped']}")
            print(f"   - Errors: {result['errors']}")
            print(f"⏱️  Completed in {duration:.2f} seconds")
        else:
            print("❌ Seeding failed!")
            print(f"Error: {result.get('message', 'Unknown error')}")
        
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ An error occurred: {e}")
    
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())