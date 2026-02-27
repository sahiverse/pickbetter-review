"""Open Food Facts API client."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.models.product import ProductCreate, NormalizedNutritionBase

logger = logging.getLogger(__name__)
settings = get_settings()

# In app/services/openfoodfacts.py
class OpenFoodFactsClient:
    def __init__(self, base_url: str = None):
        """Initialize the Open Food Facts client.
        
        Args:
            base_url: Base URL for the Open Food Facts API (defaults to world.openfoodfacts.org)
        """
        self.base_url = base_url or "https://world.openfoodfacts.org"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "PickBetter/1.0 (PickBetter - Food Product Scanner; +https://pickbetter.app/)"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_product(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Get product data by barcode from Open Food Facts.
        
        Args:
            barcode: Product barcode
            
        Returns:
            Dict containing product data or None if not found
        """
        try:
            response = await self.client.get(f"/api/v2/product/{barcode}.json")
            response.raise_for_status()
            
            # Check if response is empty or invalid
            if not response.content or response.content.strip() == b'':
                logger.error(f"Empty response for barcode {barcode}")
                return None
                
            data = response.json()
            
            if data.get("status") == 0:  # Product not found
                logger.info(f"Product with barcode {barcode} not found in Open Food Facts")
                return None
                
            return data.get("product")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"Product with barcode {barcode} not found in Open Food Facts")
                return None
            logger.error(f"Error fetching product {barcode} from Open Food Facts: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching product {barcode}: {e}")
            raise
    
    async def search_products(
        self, 
        category: str, 
        page: int = 1, 
        page_size: int = 24
    ) -> Tuple[list[Dict[str, Any]], int]:
        """
        Search for products by category.
        
        Args:
            category: Product category to search for
            page: Page number (1-based)
            page_size: Number of items per page (max 1000 for Open Food Facts)
            
        Returns:
            Tuple of (products, total_count)
        """
        try:
            # Ensure page_size is within allowed limits
            page_size = min(max(1, page_size), 1000)
            
            # Simplified search parameters that work based on our test
            search_params = {
                "search_terms": category,
                "json": 1,
                "page": page,
                "page_size": page_size,
                "fields": "code,product_name,brands,categories,image_url,quantity,serving_size,nutriments,ingredients_text,ingredients_analysis_tags,allergens,labels_tags,ecoscore_grade,nova_group,nutriscore_grade,nutriscore_score,nutrient_levels"
            }
            
            logger.info(f"Searching with params: {search_params}")
            response = await self.client.get(
                "/cgi/search.pl",
                params=search_params
            )
            response.raise_for_status()
            
            data = response.json()
            products = data.get("products", [])
            count = data.get("count", len(products))
            
            logger.info(f"Found {len(products)} products (total: {count})")
            return products, count
            
        except Exception as e:
            logger.error(f"Error searching products in category {category}: {e}", exc_info=True)
            return [], 0
    
    def parse_product(self, product_data: Dict[str, Any]) -> Optional[ProductCreate]:
        """
        Parse Open Food Facts product data into our internal format.
        
        Args:
            product_data: Raw product data from Open Food Facts
            
        Returns:
            ProductCreate instance or None if data is invalid
        """
        try:
            # Extract basic product information
            barcode = product_data.get("code") or product_data.get("id")
            if not barcode:
                logger.error("Product data missing barcode")
                return None
            
            # Extract nutrition data
            nutriments = product_data.get("nutriments", {})
            
            # Create normalized nutrition data - don't include product_id here
            # It will be set when the product is created
            normalized_nutrition = None
            if any(key in nutriments for key in ["energy-kcal_100g", "energy_100g", "carbohydrates_100g", "sugars_100g"]):
                normalized_nutrition = NormalizedNutritionBase(
                    calories_100g=nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g"),
                    carbohydrates_100g=nutriments.get("carbohydrates_100g"),
                    sugars_100g=nutriments.get("sugars_100g"),
                    fiber_100g=nutriments.get("fiber_100g"),
                    protein_100g=nutriments.get("proteins_100g"),
                    fat_100g=nutriments.get("fat_100g"),
                    saturated_fat_100g=nutriments.get("saturated-fat_100g"),
                    trans_fat_100g=nutriments.get("trans-fat_100g"),
                    sodium_100g=nutriments.get("sodium_100g"),
                    salt_100g=nutriments.get("salt_100g"),
                    serving_size=product_data.get("serving_size"),
                    serving_quantity=nutriments.get("serving_quantity"),
                    nutrition_score_fr_100g=nutriments.get("nutrition-score-fr_100g"),
                    nutrition_score_fr=product_data.get("nutriscore_score"),
                    general_health_score=product_data.get("nutriscore_score"),
                    nutri_grade=product_data.get("nutriscore_grade", "").upper()
                )
            
            # Extract ingredients and allergens
            ingredients_text = product_data.get("ingredients_text", "")
            
            # Process ingredients list if available
            ingredients_list = []
            if "ingredients" in product_data:
                for ing in product_data["ingredients"]:
                    ingredients_list.append({
                        "id": ing.get("id"),
                        "text": ing.get("text", ""),
                        "vegan": ing.get("vegan"),
                        "vegetarian": ing.get("vegetarian"),
                        "from_palm_oil": ing.get("from_palm_oil"),
                        "percent_estimate": ing.get("percent_estimate"),
                        "rank": ing.get("rank"),
                    })
            
            # Process allergens
            allergens = []
            if "allergens" in product_data and product_data["allergens"]:
                allergens = [{"tag": a.strip()} for a in product_data["allergens"].split(",") if a.strip()]
            
            # Determine dietary flags
            is_vegan = "en:vegan" in product_data.get("labels_tags", [])
            is_vegetarian = is_vegan or "en:vegetarian" in product_data.get("labels_tags", [])
            is_gluten_free = "en:gluten-free" in product_data.get("labels_tags", [])
            
            # Calculate data quality score (simple heuristic)
            data_quality_score = 0
            if product_data.get("product_name"): data_quality_score += 20
            if product_data.get("brands"): data_quality_score += 10
            if product_data.get("categories"): data_quality_score += 10
            if ingredients_text: data_quality_score += 20
            if nutriments: data_quality_score += 20
            if product_data.get("image_url"): data_quality_score += 10
            if product_data.get("nutriscore_grade"): data_quality_score += 10
            
            # Create and return the product
            return ProductCreate(
                barcode=barcode,
                name=product_data.get("product_name", ""),
                brand=product_data.get("brands"),
                category=product_data.get("categories"),
                package_size=product_data.get("product_quantity"),
                serving_size=product_data.get("serving_size"),
                image_url=product_data.get("image_url"),
                ingredients_text=ingredients_text,
                ingredients_list=ingredients_list or None,
                allergens=allergens or None,
                is_vegan=is_vegan,
                is_vegetarian=is_vegetarian,
                is_gluten_free=is_gluten_free,
                data_quality_score=min(100, data_quality_score),  # Cap at 100
                raw_nutrition_data=product_data,
                normalized_nutrition=normalized_nutrition
            )
            
        except Exception as e:
            logger.error(f"Error parsing product data: {e}", exc_info=True)
            return None


# Global client instance
client = OpenFoodFactsClient()

# Helper functions for easier imports
async def get_product(barcode: str) -> Optional[Dict[str, Any]]:
    """Get product by barcode."""
    async with OpenFoodFactsClient() as client:
        return await client.get_product(barcode)

async def search_products(category: str, page: int = 1, page_size: int = 24) -> Tuple[list[Dict[str, Any]], int]:
    """Search for products by category."""
    async with OpenFoodFactsClient() as client:
        return await client.search_products(category, page, page_size)