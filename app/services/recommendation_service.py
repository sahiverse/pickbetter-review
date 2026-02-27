"""Recommendation Engine for PickBetter - Suggests healthier alternatives."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.product import Product
from app.services.product_service import ProductService
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for finding healthier product alternatives."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
    
    async def get_recommendations(
        self,
        product_barcode: str,
        limit: int = 5,
        user_preferences: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get healthier alternatives for a product using Gemini AI.
        
        Args:
            product_barcode: Barcode of scanned product
            limit: Maximum number of recommendations (default: 5)
            user_preferences: Optional dict with filters
            user_profile: User's health profile for personalized analysis
            
        Returns:
            Dictionary with recommendations and metadata
        """
        try:
            # Get the original product
            original_product = await self.product_service.get_by_barcode(product_barcode)
            if not original_product:
                return {
                    "error": f"Product with barcode {product_barcode} not found",
                    "recommendations": []
                }
            
            # Convert product to dict for Gemini analysis
            original_product_dict = self._product_to_dict(original_product)
            
            # Use Gemini to analyze the original product
            gemini_analysis = gemini_service.analyze_product_health_score(
                original_product_dict, 
                user_profile
            )
            
            # If grade is C or below, find alternatives
            recommendations = []
            if gemini_analysis['grade'] in ['C', 'D', 'F']:
                recommendations = await self._find_gemini_alternatives(
                    original_product_dict, 
                    original_product, 
                    limit, 
                    user_profile
                )
            
            return {
                "original_product": original_product.dict(),
                "gemini_analysis": gemini_analysis,
                "recommendations": recommendations,
                "total_found": len(recommendations),
                "message": self._generate_gemini_message(gemini_analysis['grade'], len(recommendations)),
                "user_context": self._generate_user_context(user_profile)
            }
            
        except Exception as e:
            logger.error(f"Error getting Gemini recommendations: {e}")
            return {
                "error": f"Failed to get recommendations: {str(e)}",
                "recommendations": []
            }
    
    async def _find_gemini_alternatives(
        self,
        original_product_dict: Dict[str, Any],
        original_product: Product,
        limit: int,
        user_profile: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find healthier alternatives using Gemini AI."""
        try:
            # Find similar products from database
            similar_products = await self._find_similar_products(original_product, limit=20)
            
            # Convert to dict format for Gemini
            similar_product_dicts = [
                self._product_to_dict(p) for p in similar_products
                if p.barcode != original_product.barcode
            ]
            
            # Use Gemini to find best alternatives
            gemini_alternatives = gemini_service.find_healthier_alternatives(
                original_product_dict,
                similar_product_dicts,
                user_profile
            )
            
            # Enhance with additional data and personalized recommendations
            enhanced_alternatives = []
            for alt in gemini_alternatives[:limit]:
                try:
                    # Find the original product data
                    original_alt_product = next(
                        (p for p in similar_products if p.barcode == alt['product'].get('code')),
                        None
                    )
                    
                    # Generate personalized recommendation
                    personalized_rec = gemini_service.generate_personalized_recommendation(
                        alt['analysis'],
                        user_profile or {}
                    )
                    
                    enhanced_alternatives.append({
                        'product': alt['product'],
                        'analysis': alt['analysis'],
                        'original_product_data': original_alt_product.dict() if original_alt_product else None,
                        'personalized_recommendation': personalized_rec,
                        'image_url': alt['product'].get('image_url'),
                        'reasoning': alt.get('reasoning', '')
                    })
                    
                except Exception as e:
                    logger.warning(f"Error enhancing alternative: {e}")
                    enhanced_alternatives.append(alt)
            
            return enhanced_alternatives
            
        except Exception as e:
            logger.error(f"Error finding Gemini alternatives: {e}")
            return []
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert Product object to dict for Gemini analysis."""
        return {
            'code': product.barcode,
            'product_name': product.name,
            'brands': product.brand,
            'categories': product.category,
            'ingredients_text': product.ingredients_text,
            'nutriments': product.nutriments,
            'nutrition_grades': product.nutrition_grades,
            'nova_group': product.nova_group,
            'allergens': product.allergens,
            'image_url': product.image_url,
            'health_score': product.health_score,
            'health_grade': product.health_grade
        }
    
    def _generate_gemini_message(self, grade: str, num_recommendations: int) -> str:
        """Generate appropriate message based on Gemini analysis."""
        if grade in ['A', 'B']:
            return "✅ Great choice! This is already a healthy option."
        elif grade == 'C':
            if num_recommendations > 0:
                return f"Found {num_recommendations} healthier alternative(s) with A/B grades."
            else:
                return "This is an average product. Consider healthier options when available."
        else:  # D, F
            if num_recommendations > 0:
                return f"⚠️ This product needs improvement. Found {num_recommendations} healthier A/B grade alternative(s)."
            else:
                return "⚠️ This product is not the healthiest choice. Look for A/B grade alternatives."
    
    def _generate_user_context(self, user_profile: Optional[Dict[str, Any]]) -> str:
        """Generate user context string for display."""
        if not user_profile:
            return "General user (no specific preferences set)"
        
        context_parts = []
        
        if user_profile.get('allergens'):
            context_parts.append(f"Allergens: {', '.join(user_profile['allergens'])}")
        
        if user_profile.get('health_conditions'):
            context_parts.append(f"Conditions: {', '.join(user_profile['health_conditions'])}")
        
        if user_profile.get('primary_goal'):
            context_parts.append(f"Goal: {user_profile['primary_goal']}")
        
        if user_profile.get('dietary_preference'):
            context_parts.append(f"Diet: {user_profile['dietary_preference']}")
        
        return " | ".join(context_parts) if context_parts else "General user"
    
    async def _find_similar_products(
        self, 
        product: Product, 
        limit: int = 20
    ) -> List[Product]:
        """Find products in same or similar category."""
        try:
            # Extract category information
            category = product.category or ""
            
            # Try to find products in exact category first
            stmt = select(Product).where(
                and_(
                    Product.barcode != product.barcode,  # Exclude the scanned product
                    or_(
                        Product.category.ilike(f"%{category}%"),
                        Product.category.ilike(f"%{category.split()[-1]}%")  # Last word fallback
                    )
                )
            ).order_by(desc(Product.health_score)).limit(limit)
            
            result = await self.db.execute(stmt)
            similar_products = list(result.scalars().all())
            
            # If we have very few products, try broader category
            if len(similar_products) < 3 and category:
                # Go up one level in category hierarchy
                broader_category = self._get_broader_category(category)
                if broader_category:
                    stmt = select(Product).where(
                        and_(
                            Product.barcode != product.barcode,
                            Product.category.ilike(f"%{broader_category}%")
                        )
                    ).order_by(desc(Product.health_score)).limit(limit)
                    
                    result = await self.db.execute(stmt)
                    similar_products = list(result.scalars().all())
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []
    
    def _get_broader_category(self, category: str) -> Optional[str]:
        """Get a broader category from the current category."""
        # Simple category hierarchy mapping
        category_hierarchy = {
            "biscuits": "snacks",
            "chips": "snacks", 
            "cookies": "snacks",
            "instant-noodles": "pasta",
            "breakfast-cereals": "cereals",
            "soft-drinks": "beverages",
            "energy-drinks": "beverages",
            "chocolate-bars": "confectionery",
            "candies": "confectionery",
            "ice-cream": "frozen-desserts",
            "yogurt": "dairy-products"
        }
        
        # Find the first matching broader category
        for specific, broader in category_hierarchy.items():
            if specific in category.lower():
                return broader
        
        return None
    
    def _filter_by_preferences(
        self, 
        products: List[Product], 
        preferences: Dict[str, Any]
    ) -> List[Product]:
        """Apply user dietary preferences and restrictions."""
        filtered_products = products.copy()
        
        # Dietary restrictions
        dietary = preferences.get('dietary', [])
        if dietary:
            for restriction in dietary:
                if restriction == 'vegan':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_vegan(p)
                    ]
                elif restriction == 'vegetarian':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_vegetarian(p)
                    ]
                elif restriction == 'gluten-free':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_gluten_free(p)
                    ]
        
        # Allergen exclusions
        avoid_allergens = preferences.get('avoid_allergens', [])
        if avoid_allergens:
            for allergen in avoid_allergens:
                filtered_products = [
                    p for p in filtered_products 
                    if not self._contains_allergen(p, allergen)
                ]
        
        # Nutrition goals
        nutrition_goals = preferences.get('nutrition_goals', [])
        if nutrition_goals:
            for goal in nutrition_goals:
                if goal == 'low-sugar':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_low_sugar(p)
                    ]
                elif goal == 'low-sodium':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_low_sodium(p)
                    ]
                elif goal == 'high-protein':
                    filtered_products = [
                        p for p in filtered_products 
                        if self._is_high_protein(p)
                    ]
        
        return filtered_products
    
    def _is_vegan(self, product: Product) -> bool:
        """Check if product appears to be vegan."""
        if not product.ingredients_text:
            return False
        
        vegan_keywords = ['plant-based', 'vegan', 'dairy-free', 'egg-free']
        ingredients_lower = product.ingredients_text.lower()
        
        # Look for non-vegan indicators
        non_vegan_keywords = ['milk', 'egg', 'honey', 'gelatin', 'cheese']
        
        has_vegan_keywords = any(keyword in ingredients_lower for keyword in vegan_keywords)
        has_non_vegan_keywords = any(keyword in ingredients_lower for keyword in non_vegan_keywords)
        
        return has_vegan_keywords and not has_non_vegan_keywords
    
    def _is_vegetarian(self, product: Product) -> bool:
        """Check if product appears to be vegetarian."""
        if not product.ingredients_text:
            return False
        
        # Look for non-vegetarian indicators
        non_veg_keywords = ['meat', 'poultry', 'fish', 'seafood', 'pork', 'beef', 'chicken']
        ingredients_lower = product.ingredients_text.lower()
        
        return not any(keyword in ingredients_lower for keyword in non_veg_keywords)
    
    def _is_gluten_free(self, product: Product) -> bool:
        """Check if product appears to be gluten-free."""
        if not product.ingredients_text:
            return False
        
        gluten_keywords = ['wheat', 'barley', 'rye', 'malt', 'bread', 'pasta']
        ingredients_lower = product.ingredients_text.lower()
        
        return not any(keyword in ingredients_lower for keyword in gluten_keywords)
    
    def _contains_allergen(self, product: Product, allergen: str) -> bool:
        """Check if product contains specific allergen."""
        if not product.ingredients_text:
            return False
        
        ingredients_lower = product.ingredients_text.lower()
        allergen_lower = allergen.lower()
        
        allergen_keywords = {
            'nuts': ['nuts', 'almonds', 'peanuts', 'cashews', 'walnuts'],
            'soy': ['soy', 'soya', 'tofu', 'soybean'],
            'eggs': ['egg', 'eggs', 'albumin']
        }
        
        if allergen_lower in allergen_keywords:
            return any(keyword in ingredients_lower for keyword in allergen_keywords[allergen_lower])
        
        return False
    
    def _is_low_sugar(self, product: Product) -> bool:
        """Check if product is low in sugar."""
        if not product.nutriments:
            return False
        
        sugars = product.nutriments.get('sugars_100g', 0)
        return sugars <= 5  # Low sugar threshold
    
    def _is_low_sodium(self, product: Product) -> bool:
        """Check if product is low in sodium."""
        if not product.nutriments:
            return False
        
        sodium = product.nutriments.get('sodium_100g', 0)
        return sodium <= 200  # Low sodium threshold
    
    def _is_high_protein(self, product: Product) -> bool:
        """Check if product is high in protein."""
        if not product.nutriments:
            return False
        
        protein = product.nutriments.get('proteins_100g', 0)
        return protein >= 10  # High protein threshold
    
    def _calculate_similarity_score(self, product_a: Product, product_b: Product) -> float:
        """Calculate how similar two products are (0.0 to 1.0)."""
        similarity_score = 0.0
        
        # Brand similarity (30% weight)
        if product_a.brand and product_b.brand:
            if product_a.brand.lower() == product_b.brand.lower():
                similarity_score += 10 * 0.3
            elif any(word in product_b.brand.lower() for word in product_a.brand.lower().split()):
                similarity_score += 5 * 0.3
        
        # Category similarity (20% weight)
        if product_a.category and product_b.category:
            if product_a.category.lower() == product_b.category.lower():
                similarity_score += 10 * 0.2
            elif product_a.category.split()[-1] == product_b.category.split()[-1]:
                similarity_score += 5 * 0.2
        
        # Base similarity for being in same broad category (10% weight)
        if product_a.category and product_b.category:
            if product_a.category.split()[-1] == product_b.category.split()[-1]:
                similarity_score += 10 * 0.1
        
        # Price range similarity (would need price data, using placeholder)
        # similarity_score += price_similarity * 0.2
        
        return min(similarity_score, 1.0)
    
    def _calculate_composite_score(
        self,
        original: Product,
        alternative: Product,
        similarity: float
    ) -> float:
        """Calculate final ranking score."""
        if not original.health_score or not alternative.health_score:
            return 0.0
        
        # Health score difference (50% weight)
        score_diff = alternative.health_score - original.health_score
        health_component = min(score_diff * 0.5, 25)  # Max 25 points
        
        # Similarity score (30% weight)
        similarity_component = similarity * 30  # Max 30 points
        
        # Popularity bonus (20% weight) - using health score as proxy
        popularity_component = min(alternative.health_score * 0.2, 20)  # Max 20 points
        
        return health_component + similarity_component + popularity_component
    
    def _generate_comparison_metrics(
        self, 
        original: Product, 
        alternative: Product
    ) -> Dict[str, str]:
        """Generate human-readable comparison metrics."""
        if not original.nutriments or not alternative.nutriments:
            return {}
        
        comparison = {}
        
        # Sugar comparison
        orig_sugar = original.nutriments.get('sugars_100g', 0)
        alt_sugar = alternative.nutriments.get('sugars_100g', 0)
        if alt_sugar < orig_sugar:
            reduction = ((orig_sugar - alt_sugar) / orig_sugar * 100) if orig_sugar > 0 else 0
            comparison['sugar_reduction'] = f"{reduction:.0f}% less sugar"
        
        # Sodium comparison
        orig_sodium = original.nutriments.get('sodium_100g', 0)
        alt_sodium = alternative.nutriments.get('sodium_100g', 0)
        if alt_sodium < orig_sodium:
            reduction = ((orig_sodium - alt_sodium) / orig_sodium * 100) if orig_sodium > 0 else 0
            comparison['sodium_reduction'] = f"{reduction:.0f}% less sodium"
        
        # Protein comparison
        orig_protein = original.nutriments.get('proteins_100g', 0)
        alt_protein = alternative.nutriments.get('proteins_100g', 0)
        if alt_protein > orig_protein:
            increase = (alt_protein / orig_protein) if orig_protein > 0 else 0
            comparison['protein_increase'] = f"{increase:.1f}x more protein"
        
        # Saturated fat comparison
        orig_sat_fat = original.nutriments.get('saturated-fat_100g', 0)
        alt_sat_fat = alternative.nutriments.get('saturated-fat_100g', 0)
        if alt_sat_fat < orig_sat_fat:
            reduction = ((orig_sat_fat - alt_sat_fat) / orig_sat_fat * 100) if orig_sat_fat > 0 else 0
            comparison['saturated_fat_reduction'] = f"{reduction:.0f}% less saturated fat"
        
        return comparison
    
    def _generate_recommendation_reasons(
        self,
        original: Product,
        alternative: Product,
        score_diff: int,
        similarity: float
    ) -> List[str]:
        """Generate bullet points explaining why this is recommended."""
        reasons = []
        
        # Health improvement reason
        if score_diff > 0:
            reasons.append(f"{score_diff} points healthier")
        
        # Brand similarity
        if original.brand and alternative.brand:
            if original.brand.lower() == alternative.brand.lower():
                reasons.append("Same brand you trust")
            elif any(word in alternative.brand.lower() for word in original.brand.lower().split()):
                reasons.append("Similar trusted brand")
        
        # Category similarity
        if similarity > 0.7:
            reasons.append("Very similar product type")
        elif similarity > 0.5:
            reasons.append("Similar product category")
        
        # Specific nutritional benefits
        comparison = self._generate_comparison_metrics(original, alternative)
        if 'sugar_reduction' in comparison:
            reasons.append("Lower sugar content")
        if 'protein_increase' in comparison:
            reasons.append("Higher protein content")
        if 'sodium_reduction' in comparison:
            reasons.append("Lower sodium content")
        
        return reasons
    
    def _generate_message(self, total_found: int, returned: int) -> str:
        """Generate appropriate message based on results."""
        if returned == 0:
            return "✅ Great choice! This is already one of the healthier options in this category."
        elif total_found < 3:
            return f"Found {returned} healthier alternative(s) - limited options available."
        else:
            return f"Found {returned} healthier alternatives out of {total_found} total."


async def get_recommendations(
    product_barcode: str,
    limit: int = 5,
    user_preferences: Optional[Dict[str, Any]] = None,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """
    Convenience function for getting recommendations.
    
    Args:
        product_barcode: Barcode of scanned product
        limit: Maximum number of recommendations
        user_preferences: Optional user preference filters
        db: Database session
        
    Returns:
        Dictionary with recommendations and metadata
    """
    if not db:
        raise ValueError("Database session is required")
    
    engine = RecommendationEngine(db)
    return await engine.get_recommendations(product_barcode, limit, user_preferences)