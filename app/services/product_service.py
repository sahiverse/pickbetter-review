"""Product service for handling product-related operations."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.product import (
    Product, 
    NormalizedNutrition, 
    ProductCreate, 
    ProductUpdate, 
    ProductResponse,
    NormalizedNutritionBase
)
from app.services.openfoodfacts import OpenFoodFactsClient
from app.services.scoring_service import calculate_inr_score
from app.services.personalization_engine import get_personalized_analysis

logger = logging.getLogger(__name__)
settings = get_settings()

class ProductService:
    """Service for product-related operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the product service."""
        self.db = db
    
    async def get_by_barcode(
        self, 
        barcode: str, 
        force_refresh: bool = False
    ) -> Optional[ProductResponse]:
        """
        Get a product by its barcode, with cache-first strategy.
        
        Args:
            barcode: Product barcode
            force_refresh: If True, force refresh from Open Food Facts
            
        Returns:
            ProductResponse if found, None otherwise
        """
        # Check cache first if not forcing refresh
        if not force_refresh:
            product = await self._get_from_database(barcode)
            if product and self._is_fresh(product.updated_at):
                logger.debug(f"Returning cached product with barcode {barcode}")
                return await self._to_response(product)
        
        # If not in cache or force_refresh, fetch from Open Food Facts
        logger.debug(f"Fetching product {barcode} from Open Food Facts")
        async with OpenFoodFactsClient() as client:
            product_data = await client.get_product(barcode)
            
            if not product_data:
                logger.info(f"Product with barcode {barcode} not found in Open Food Facts")
                # Check if we have it in database anyway (might be user-contributed)
                product = await self._get_from_database(barcode)
                if product:
                    return await self._to_response(product)
                return None
            
            try:
                # Parse and save the product
                product = await self._create_or_update_product(product_data)
                return await self._to_response(product)
            except (ValueError, AttributeError) as e:
                logger.error(f"Failed to parse product {barcode}: {e}")
                # Check if we have it in database anyway
                product = await self._get_from_database(barcode)
                if product:
                    return await self._to_response(product)
                return None
    
    async def search_products(
        self,
        query: str = None,
        category: str = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for products with optional filtering.
        
        Args:
            query: Search query string
            category: Filter by category
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dictionary with products and pagination info
        """
        # Build the base query
        stmt = select(Product).options(
            selectinload(Product.normalized_nutrition)
        )
        
        # Apply filters
        conditions = []
        if query:
            conditions.append(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.brand.ilike(f"%{query}%"),
                    Product.category.ilike(f"%{query}%")
                )
            )
        if category:
            conditions.append(Product.category.ilike(f"%{category}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(stmt)
        products = result.scalars().all()
        
        # Get total count for pagination
        count_stmt = select(func.count()).select_from(Product)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar()
        
        return {
            "products": [await self._to_response(p) for p in products],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def seed_from_openfoodfacts(
        self, 
        category: str, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Seed the database with products from Open Food Facts.
        
        Args:
            category: Category to seed products from
            limit: Maximum number of products to fetch
            
        Returns:
            Dictionary with seeding results
        """
        logger.info(f"Seeding up to {limit} products from category: {category}")
        
        # Initialize counters
        added = 0
        updated = 0
        skipped = 0
        errors = 0
        
        # First, fetch all products from Open Food Facts
        async with OpenFoodFactsClient() as client:
            # Try with different search terms if the first attempt fails
            search_terms = [category, f"{category} drinks", f"{category} beverages"]
            products = []
            
            for search_term in search_terms:
                logger.info(f"Searching for products with term: {search_term}")
                products, total = await client.search_products(search_term, page_size=min(limit, 1000))
                if products:
                    logger.info(f"Found {len(products)} products with search term: {search_term}")
                    break
            
            if not products:
                logger.warning(f"No products found for category: {category} with any search terms")
                return {
                    "total_processed": 0,
                    "added": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": 0
                }
        
        # Process each product in its own transaction
        for product_data in products:
            try:
                # Start a new transaction for each product
                async with self.db.begin():
                    # Log the product being processed
                    logger.debug(f"Processing product: {product_data.get('product_name')} ({product_data.get('code')})")
                    
                    # Skip if missing required fields
                    if not product_data.get("code") or not product_data.get("product_name"):
                        logger.warning(f"Skipping product due to missing required fields: {product_data}")
                        skipped += 1
                        # Rollback and continue
                        await self.db.rollback()
                        continue
                    
                    # Check if product already exists
                    existing = await self._get_from_database(product_data["code"])
                    
                    # Parse the product data
                    product = await self._parse_product_data(product_data)
                    
                    if not product:
                        logger.warning(f"Failed to parse product data: {product_data.get('code')}")
                        skipped += 1
                        # Rollback and continue
                        await self.db.rollback()
                        continue
                    
                    if existing:
                        # Update existing product
                        await self._update_product(existing, product)
                        updated += 1
                        logger.info(f"Updated existing product: {product.name} ({product.barcode})")
                    else:
                        # Add new product
                        await self._add_product(product)
                        added += 1
                        logger.info(f"Added new product: {product.name} ({product.barcode})")
                    
                    # Commit this product's transaction
                    await self.db.commit()
                    
            except Exception as e:
                # Rollback on error
                await self.db.rollback()
                logger.error(f"Error processing product {product_data.get('code')}: {e}", exc_info=True)
                errors += 1
                # Continue with the next product
                continue
        
        result = {
            "total_processed": added + updated + skipped + errors,
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }
        
        logger.info(f"Seeding completed. Results: {result}")
        return result
    
    async def _get_from_database(self, barcode: str) -> Optional[Product]:
        """Get a product from the database by barcode."""
        stmt = select(Product).where(Product.barcode == barcode).options(
            selectinload(Product.normalized_nutrition)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def _create_or_update_product(
        self, 
        product_data: Dict[str, Any]
    ) -> Product:
        """
        Create or update a product from Open Food Facts data.
        
        Args:
            product_data: Raw product data from Open Food Facts
            
        Returns:
            The created or updated Product instance
        """
        # Parse the product data
        product = await self._parse_product_data(product_data)
        
        # Check if product parsing failed
        if not product:
            raise ValueError("Failed to parse product data")
        
        # Check if product exists
        existing = await self._get_from_database(product.barcode)
        
        if existing:
            return await self._update_product(existing, product)
        else:
            return await self._add_product(product)
    
    async def _parse_product_data(self, product_data: Dict[str, Any]) -> ProductCreate:
        """Parse raw product data into a ProductCreate instance."""
        async with OpenFoodFactsClient() as client:
            return client.parse_product(product_data)
    
    async def _add_product(self, product: ProductCreate) -> Product:
        """Add a new product to the database."""
        # Create the product without normalized_nutrition first
        product_data = product.dict(exclude={"normalized_nutrition"})
        db_product = Product(**product_data)
        
        # Add the product to the session first to generate an ID
        self.db.add(db_product)
        await self.db.flush()  # This will generate an ID for the product
        
        # Now add normalized nutrition if available
        if product.normalized_nutrition:
            # Create the nutrition object with the product_id
            nutrition_data = product.normalized_nutrition.dict(exclude_unset=True)
            nutrition_data["product_id"] = db_product.id
            
            db_nutrition = NormalizedNutrition(**nutrition_data)
            db_product.normalized_nutrition = db_nutrition
            self.db.add(db_nutrition)
        
        # Commit the transaction
        await self.db.commit()
        await self.db.refresh(db_product)
        
        logger.info(f"Added new product: {db_product.name} ({db_product.barcode})")
        return db_product
    
    async def _update_product(
        self, 
        existing: Product, 
        new_data: ProductCreate
    ) -> Product:
        """Update an existing product with new data."""
        # Update product fields
        update_data = new_data.dict(exclude={"normalized_nutrition"}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing, field, value)
        
        # Update or create normalized nutrition
        if new_data.normalized_nutrition:
            if existing.normalized_nutrition:
                # Update existing nutrition
                nutrition_data = new_data.normalized_nutrition.dict(exclude_unset=True)
                for field, value in nutrition_data.items():
                    setattr(existing.normalized_nutrition, field, value)
            else:
                # Create new nutrition with the product_id
                nutrition_data = new_data.normalized_nutrition.dict(exclude_unset=True)
                nutrition_data["product_id"] = existing.id
                existing.normalized_nutrition = NormalizedNutrition(**nutrition_data)
                self.db.add(existing.normalized_nutrition)
        
        # Commit the transaction
        await self.db.commit()
        await self.db.refresh(existing)
        
        logger.debug(f"Updated product: {existing.name} ({existing.barcode})")
        return existing
    
    async def _to_response(self, product: Product) -> ProductResponse:
        """Convert a Product to a ProductResponse."""
        if not product:
            return None
            
        # Convert SQLModel to dict manually
        data = {
            "id": product.id,
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "ingredients_text": product.ingredients_text,
            "ingredients_list": product.ingredients_list,
            "nutriments": product.nutriments,
            "nutrition_grades": product.nutrition_grades,
            "nova_group": product.nova_group,
            "ecoscore_grade": product.ecoscore_grade,
            "last_modified": product.last_modified,
            "health_score": product.health_score,
            "health_grade": product.health_grade,
            "score_last_calculated": product.score_last_calculated,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }
        
        # Skip normalized nutrition for mock data (not needed for recommendations)
        data['normalized_nutrition'] = None
        
        return ProductResponse(**data)
    
    def _is_fresh(self, updated_at: datetime) -> bool:
        """Check if a product's data is fresh (less than 30 days old)."""
        if not updated_at:
            return False
            
        cache_days = settings.PRODUCT_CACHE_DAYS
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Make updated_at timezone-aware if it isn't already
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return (now - updated_at) < timedelta(days=cache_days)