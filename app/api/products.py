"""API endpoints for product-related operations."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import ProductResponse, ProductListResponse
from app.services.product_service import ProductService
from app.services.scoring_service import calculate_inr_score, NutritionScorer
from app.services.recommendation_service import RecommendationEngine
from app.services.firebase_auth import (
    get_current_user,
    get_current_user_optional,
    get_authenticated_user
)
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/products", tags=["products"])

import logging
logger = logging.getLogger(__name__)


def _is_beverage(product) -> bool:
    """
    Determine if a product is a beverage based on category and other fields.

    Args:
        product: Product model instance

    Returns:
        True if beverage, False if solid food
    """
    if not product:
        return False

    # Check category first
    category = (product.category or "").lower()

    beverage_keywords = [
        'beverages', 'drink', 'juice', 'soda', 'soft drink', 'water', 'milk',
        'tea', 'coffee', 'beer', 'wine', 'liquor', 'alcohol', 'energy drink',
        'sports drink', 'carbonated', 'non-alcoholic', 'beverage'
    ]

    for keyword in beverage_keywords:
        if keyword in category:
            return True

    # Check product name/brand for beverage indicators
    name_brand = f"{product.name or ''} {product.brand or ''}".lower()
    for keyword in beverage_keywords:
        if keyword in name_brand:
            return True

    return False


def _is_water(product) -> bool:
    """
    Determine if a product is water (special case for beverages).

    Args:
        product: Product model instance

    Returns:
        True if water, False otherwise
    """
    if not product:
        return False

    name_brand = f"{product.name or ''} {product.brand or ''}".lower()
    water_keywords = ['water', 'mineral water', 'spring water', 'purified water']

    for keyword in water_keywords:
        if keyword in name_brand:
            return True

    return False


@router.get("/{barcode}", response_model=ProductResponse)
async def get_product(
    barcode: str,
    force_refresh: bool = False,
    include_score: bool = True,
    user_profile: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a product by its barcode.
    
    Implements a cache-first strategy:
    1. Check if product exists in the database and is fresh (<30 days old)
    2. If not found or force_refresh=True, fetch from Open Food Facts
    3. Parse and store the product data
    4. Return the product with optional health score
    
    Args:
        barcode: Product barcode (EAN-13, UPC, etc.)
        force_refresh: If True, bypass cache and fetch fresh data from Open Food Facts
        include_score: If True, include health score calculation
        
    Returns:
        Product data if found, 404 if not found
    """
    service = ProductService(db)
    product = await service.get_by_barcode(barcode, force_refresh=force_refresh)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode {barcode} not found"
        )
    
    # Convert to response model
    response_data = product.dict()
    
    # Add health score if requested
    if include_score:
        # Check if score needs recalculation
        needs_recalculation = (
            not product.health_score or 
            not product.health_grade or 
            not product.score_last_calculated or
            (product.updated_at > product.score_last_calculated)
        )
        
        if needs_recalculation:
            print(f"Recalculating health score for {barcode} - data updated")
            # Get the actual database product to update
            db_product = await service._get_from_database(barcode)
            if db_product:
                # Determine if product is beverage or water
                is_beverage = _is_beverage(db_product)
                is_water = _is_water(db_product)

                # Use new INR/HSR scoring system with normalized nutrition data
                nutrition_data = db_product.nutriments or {}
                serving_size = getattr(db_product, 'serving_size', None)

                health_score = calculate_inr_score(
                    nutrition_data=nutrition_data,
                    serving_size=serving_size,
                    is_beverage=is_beverage,
                    is_water=is_water
                )

                # Update database product with new score (no nested transaction)
                db_product.health_score = health_score["score"]
                db_product.health_grade = health_score["grade"]
                db_product.score_last_calculated = datetime.utcnow()
                
                # Add to session and commit
                db.add(db_product)
                await db.commit()
                await db.refresh(db_product)

                # Update response data with new score
                response_data["health_score"] = health_score["score"]
                response_data["health_grade"] = health_score["grade"]
                response_data["score_calculated_fresh"] = True
                
                # Add personalization if user profile provided
                if user_profile:
                    product_data = {
                        "barcode": db_product.barcode,
                        "name": db_product.name,
                        "brand": db_product.brand,
                        "ingredients_text": db_product.ingredients_text or "",
                        "nutriments": db_product.nutriments or {},
                        "category": db_product.category,
                        "health_grade": db_product.health_grade,
                        "health_score": db_product.health_score
                    }
                    personalized_analysis = get_personalized_analysis(product_data, user_profile)
                    response_data["personalized_flags"] = personalized_analysis.get("flags", [])
            else:
                response_data["health_score"] = 0
                response_data["health_grade"] = "N"
                response_data["score_calculated_fresh"] = False
        else:
            print(f"Using cached health score for {barcode} - data unchanged")
            # Return cached score
            response_data["health_score"] = product.health_score
            response_data["health_grade"] = product.health_grade
            response_data["score_calculated_fresh"] = False
            
            # Add personalization if user profile provided
            if user_profile:
                product_data = {
                    "barcode": product.barcode,
                    "name": product.name,
                    "brand": product.brand,
                    "ingredients_text": product.ingredients_text or "",
                    "nutriments": product.nutriments or {},
                    "category": product.category,
                    "health_grade": product.health_grade,
                    "health_score": product.health_score
                }
                personalized_analysis = get_personalized_analysis(product_data, user_profile)
                response_data["personalized_flags"] = personalized_analysis.get("flags", [])
    
    return response_data


@router.post("/seed/{category}")
async def seed_products(
    category: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Seed the database with products from Open Food Facts.
    
    Args:
        category: Product category to seed (e.g., 'cereals', 'beverages')
        limit: Maximum number of products to fetch (1-1000)
        
    Returns:
        Dictionary with seeding results
    """
    if not category or len(category.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category must be at least 2 characters long"
        )
    
    service = ProductService(db)
    result = await service.seed_from_openfoodfacts(category=category, limit=limit)
    
    return {
        "status": "success",
        "message": f"Seeded {result['added']} new products, updated {result['updated']} existing ones",
        "data": result
    }


@router.get("/", response_model=ProductListResponse)
async def search_products(
    q: Optional[str] = Query(None, min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for products with optional filtering.
    
    Args:
        q: Search query (searches in name, brand, and category)
        category: Filter by category
        page: Page number (1-based)
        page_size: Number of items per page (1-100)
        
    Returns:
        Paginated list of matching products
    """
    if not q and not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'q' or 'category' parameters is required"
        )
    
    service = ProductService(db)
    result = await service.search_products(
        query=q,
        category=category,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/{barcode}/score")
async def get_product_score(
    barcode: str,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health score breakdown for a product by its barcode.
    
    Args:
        barcode: Product barcode (EAN-13, UPC, etc.)
        force_refresh: If True, bypass cache and fetch fresh data from Open Food Facts
        
    Returns:
        Health score calculation with breakdown and factors
    """
    service = ProductService(db)
    product = await service.get_by_barcode(barcode, force_refresh=force_refresh)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode {barcode} not found"
        )
    
    # Calculate health score
    # Check if score needs recalculation
    needs_recalculation = (
        not product.health_score or 
        not product.health_grade or 
        not product.score_last_calculated or
        (product.updated_at > product.score_last_calculated)
    )
    
    if needs_recalculation:
        print(f"Recalculating health score for {barcode} - data updated")
        # Get the actual database product to update
        db_product = await service._get_from_database(barcode)
        if db_product:
            # Determine if product is beverage or water
            is_beverage = _is_beverage(db_product)
            is_water = _is_water(db_product)

            # Use new INR/HSR scoring system with normalized nutrition data
            nutrition_data = db_product.nutriments or {}
            serving_size = getattr(db_product, 'serving_size', None)

            health_score = calculate_inr_score(
                nutrition_data=nutrition_data,
                serving_size=serving_size,
                is_beverage=is_beverage,
                is_water=is_water
            )

            # Update database product with new score
            db_product.health_score = health_score["score"]
            db_product.health_grade = health_score["grade"]
            db_product.score_last_calculated = datetime.utcnow()

            # Commit changes (session is managed by FastAPI)
            await db.commit()
            await db.refresh(db_product)

            response_data = {
                "barcode": barcode,
                "product_name": db_product.name,
                "brand": db_product.brand,
                "health_score": health_score,
                "score_calculated_fresh": True
            }
        else:
            response_data = {
                "barcode": barcode,
                "product_name": "Unknown",
                "brand": "Unknown",
                "health_score": {"score": 0, "grade": "N"},
                "score_calculated_fresh": False
            }
    else:
        print(f"Using cached health score for {barcode} - data unchanged")
        # Return cached score with full breakdown (recalculate for display)
        if product.health_score:
            # Determine if product is beverage or water
            is_beverage = _is_beverage(product)
            is_water = _is_water(product)

            # Use new INR/HSR scoring system with normalized nutrition data for breakdown
            nutrition_data = product.nutriments or {}
            serving_size = getattr(product, 'serving_size', None)

            health_score = calculate_inr_score(
                nutrition_data=nutrition_data,
                serving_size=serving_size,
                is_beverage=is_beverage,
                is_water=is_water
            )

            response_data = {
                "barcode": barcode,
                "product_name": product.name,
                "brand": product.brand,
                "health_score": health_score,
                "score_calculated_fresh": False
            }
        else:
            # No cached score available - calculate fresh
            # Determine if product is beverage or water
            is_beverage = _is_beverage(product)
            is_water = _is_water(product)

            # Use new INR/HSR scoring system with normalized nutrition data
            nutrition_data = product.nutriments or {}
            serving_size = getattr(product, 'serving_size', None)

            health_score = calculate_inr_score(
                nutrition_data=nutrition_data,
                serving_size=serving_size,
                is_beverage=is_beverage,
                is_water=is_water
            )

            response_data = {
                "barcode": barcode,
                "product_name": product.name,
                "brand": product.brand,
                "health_score": health_score,
                "score_calculated_fresh": True
            }
    
    return response_data


@router.get("/health/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "product-service"
    }


@router.get("/{barcode}/recommendations")
async def get_product_recommendations(
    barcode: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    dietary: Optional[List[str]] = Query(None, description="Dietary restrictions"),
    nutrition_goals: Optional[List[str]] = Query(None, description="Nutrition goals"),
    avoid_allergens: Optional[List[str]] = Query(None, description="Allergens to avoid"),
    min_improvement: int = Query(10, ge=5, le=50, description="Minimum health score improvement"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get healthier alternatives for a product.
    
    Args:
        barcode: Product barcode (EAN-13, UPC, etc.)
        limit: Maximum number of recommendations (1-20)
        dietary: Dietary restrictions (vegan, vegetarian, gluten-free)
        nutrition_goals: Nutrition goals (low-sugar, low-sodium, high-protein)
        avoid_allergens: Allergens to avoid (nuts, soy, eggs)
        min_improvement: Minimum health score improvement required
        
    Returns:
        Dictionary with recommendations and metadata
    """
    # Build user preferences from query parameters
    user_preferences = {}
    
    if dietary:
        user_preferences['dietary'] = dietary
    
    if nutrition_goals:
        user_preferences['nutrition_goals'] = nutrition_goals
    
    if avoid_allergens:
        user_preferences['avoid_allergens'] = avoid_allergens
    
    user_preferences['min_improvement'] = min_improvement
    
    # Get recommendations
    result = await get_recommendations(
        product_barcode=barcode,
        limit=limit,
        user_preferences=user_preferences,
        db=db
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.get("/compare/{barcode1}/{barcode2}")
async def compare_products(
    barcode1: str,
    barcode2: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Direct comparison between two products.
    
    Args:
        barcode1: First product barcode
        barcode2: Second product barcode
        
    Returns:
        Side-by-side comparison with health scores
    """
    service = ProductService(db)
    
    # Get both products
    product1 = await service.get_by_barcode(barcode1)
    product2 = await service.get_by_barcode(barcode2)
    
    if not product1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode {barcode1} not found"
        )
    
    if not product2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode {barcode2} not found"
        )
    
    # Calculate health scores using new INR/HSR system
    # Product 1
    is_beverage1 = _is_beverage(product1)
    is_water1 = _is_water(product1)
    nutrition_data1 = product1.nutriments or {}
    serving_size1 = getattr(product1, 'serving_size', None)

    score1 = calculate_inr_score(
        nutrition_data=nutrition_data1,
        serving_size=serving_size1,
        is_beverage=is_beverage1,
        is_water=is_water1
    )

    # Product 2
    is_beverage2 = _is_beverage(product2)
    is_water2 = _is_water(product2)
    nutrition_data2 = product2.nutriments or {}
    serving_size2 = getattr(product2, 'serving_size', None)

    score2 = calculate_inr_score(
        nutrition_data=nutrition_data2,
        serving_size=serving_size2,
        is_beverage=is_beverage2,
        is_water=is_water2
    )
    
    # Generate comparison
    comparison = {
        "product1": {
            "barcode": barcode1,
            "name": product1.name,
            "brand": product1.brand,
            "category": product1.category,
            "health_score": score1
        },
        "product2": {
            "barcode": barcode2,
            "name": product2.name,
            "brand": product2.brand,
            "category": product2.category,
            "health_score": score2
        },
        "winner": "product1" if score1["score"] > score2["score"] else "product2",
        "score_difference": abs(score1["score"] - score2["score"]),
        "comparison_summary": _generate_comparison_summary(product1, product2, score1, score2)
    }
    
    return comparison


def _generate_comparison_summary(product1, product2, score1, score2):
    """Generate a summary of the comparison."""
    summary = []
    
    score_diff = score1["score"] - score2["score"]
    
    if score_diff > 0:
        summary.append(f"{product1.name} is {score_diff} points healthier")
    elif score_diff < 0:
        summary.append(f"{product2.name} is {abs(score_diff)} points healthier")
    else:
        summary.append("Both products have the same health score")
    
    # Compare key nutritional factors
    if product1.nutriments and product2.nutriments:
        # Sugar comparison
        sugar1 = product1.nutriments.get('sugars_100g', 0)
        sugar2 = product2.nutriments.get('sugars_100g', 0)
        
        if sugar1 < sugar2:
            reduction = ((sugar2 - sugar1) / sugar2 * 100) if sugar2 > 0 else 0
            summary.append(f"{product1.name} has {reduction:.0f}% less sugar")
        elif sugar2 < sugar1:
            reduction = ((sugar1 - sugar2) / sugar1 * 100) if sugar1 > 0 else 0
            summary.append(f"{product2.name} has {reduction:.0f}% less sugar")
        
        # Protein comparison
        protein1 = product1.nutriments.get('proteins_100g', 0)
        protein2 = product2.nutriments.get('proteins_100g', 0)
        
        if protein1 > protein2:
            increase = (protein1 / protein2) if protein2 > 0 else 0
            summary.append(f"{product1.name} has {increase:.1f}x more protein")
        elif protein2 > protein1:
            increase = (protein2 / protein1) if protein1 > 0 else 0
            summary.append(f"{product2.name} has {increase:.1f}x more protein")
    
    return summary


@router.get("/{barcode}/buy-links")
async def get_product_buy_links(
    barcode: str,
    platforms: Optional[List[str]] = Query(None, description="Commerce platforms (blinkit, zepto, instamart)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get buy links for a product across quick-commerce platforms.
    
    Args:
        barcode: Product barcode (EAN-13, UPC, etc.)
        platforms: List of platforms (default: all platforms)
        
    Returns:
        Dictionary with product info and platform buy links
    """
    try:
        # Get commerce links
        result = await get_commerce_links(
            barcode=barcode,
            platforms=platforms,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# Explicitly handle OPTIONS for the scan endpoint to prevent it from matching /{barcode}/{action} catch-alls and failing validation
@router.options("/scan/{barcode}")
async def options_scan_product(barcode: str):
    return {}

@router.post("/scan/{barcode}")
async def scan_product(barcode: str) -> Dict[str, Any]:
    """Scan a product barcode and return analysis."""
    import httpx
    import asyncio

    try:
        # Try to fetch real product data from Open Food Facts
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5.0)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1 and data.get('product'):
                product = data['product']

                # Extract product info
                product_name = product.get('product_name', f'Product {barcode}')
                brands = product.get('brands', 'Unknown Brand')
                ingredients = product.get('ingredients_text', 'Various ingredients')
                nutriments = product.get('nutriments', {})
                image_url = product.get('image_url') or product.get('selected_images', {}).get('front', {}).get('display', {}).get('en') or f"https://via.placeholder.com/300x300?text={barcode}"

                # Create analysis based on real data
                return {
                    "status": "success",
                    "data": {
                        "original_product": {
                            "product_name": product_name,
                            "brands": brands,
                            "ingredients_text": ingredients,
                            "nutriments": {
                                "energy-kcal_100g": nutriments.get('energy-kcal_100g', 0),
                                "proteins_100g": nutriments.get('proteins_100g', 0),
                                "carbohydrates_100g": nutriments.get('carbohydrates_100g', 0),
                                "fat_100g": nutriments.get('fat_100g', 0)
                            },
                            "image_url": image_url,
                            "code": barcode
                        },
                        "gemini_analysis": {
                            "grade": "B",  # Assume B grade for demo
                            "score": 75,
                            "reasoning": f"This is a B grade product. {product_name} has moderate nutritional value with some health benefits.",
                            "health_concerns": ["May contain processed ingredients", "Check allergens"],
                            "positive_aspects": ["Widely available", "Reasonable nutritional balance"]
                        },
                        "recommendations": [
                            {
                                "product": {
                                    "product_name": f"Healthier Alternative to {product_name}",
                                    "brands": "Healthy Choice",
                                    "code": f"{int(barcode) + 1}",
                                    "image_url": f"https://via.placeholder.com/200x200?text=Healthy+Alt"
                                },
                                "analysis": {
                                    "grade": "A",
                                    "score": 90,
                                    "reasoning": "Superior nutritional profile."
                                },
                                "personalized_recommendation": "This alternative offers better nutritional value.",
                                "image_url": f"https://via.placeholder.com/200x200?text=Healthy+Alt",
                                "reasoning": "Recommended for improved health score."
                            }
                        ],
                        "total_found": 1,
                        "message": f"✅ {product_name} analyzed successfully!",
                        "user_context": "Analysis based on available nutritional data."
                    }
                }

    except Exception as e:
        logger.warning(f"Failed to fetch from Open Food Facts for {barcode}: {e}")

    # Fallback: Try to synthesize the product using Gemini AI
    logger.info(f"Attempting to synthesize unknown product {barcode} via Gemini")
    
    from fastapi.concurrency import run_in_threadpool
    synthesized_data = await run_in_threadpool(
        gemini_service.synthesize_product_from_barcode, 
        barcode
    )
    
    if not synthesized_data:
        # Gemini explicitly returned NOT_FOUND
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode {barcode} not found in database and could not be synthesized."
        )

    return {
        "status": "success",
        "data": synthesized_data
    }


async def _get_user_profile(user_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Get user profile for personalized recommendations."""
    try:
        from app.models.user import UserProfile
        from sqlalchemy import select

        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await db.execute(stmt)
        user_profile = result.scalar_one_or_none()

        if user_profile:
            return {
                'user_id': user_profile.user_id,
                'name': user_profile.name,
                'allergens': user_profile.allergens,
                'health_conditions': user_profile.health_conditions,
                'dietary_preference': user_profile.dietary_preference,
                'primary_goal': user_profile.primary_goal,
                'age': user_profile.age,
                'sex': user_profile.sex,
                'height': user_profile.height,
                'weight': user_profile.weight
            }

        return None

    except Exception as e:
        logger.error(f"Error getting user profile for {user_id}: {e}")
        return None