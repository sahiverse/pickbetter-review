"""
Personalization Engine for PickBetter
Provides personalized product analysis based on user health profiles, allergens, and preferences.
"""

from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Engine for generating personalized product flags based on user profiles.
    Analyzes products against user allergens, health conditions, dietary preferences, and goals.
    """

    # Strict allergen lists with keywords for detection
    ALLERGEN_KEYWORDS = {
        "Peanuts": ["peanut", "groundnut", "arachis"],
        "Tree Nuts (Cashews, Almonds, Walnuts)": ["cashew", "almond", "walnut", "pistachio", "pecan", "hazelnut", "brazil nut", "macadamia"],
        "Milk/Dairy": ["milk", "curd", "paneer", "whey", "casein", "lactose", "cream", "ghee", "butter", "cheese", "yogurt", "dahi"],
        "Wheat/Gluten": ["wheat", "gluten", "maida", "atta", "flour", "bread", "pasta", "noodle"],
        "Mustard": ["mustard", "sarson", "rai"],
        "Soy": ["soy", "soya", "soybean", "tofu", "tempeh", "edamame"],
        "Egg": ["egg", "albumin", "lecithin"],
        "Sesame": ["sesame", "til", "tahini"],
        "Shellfish/Fish": ["fish", "shellfish", "prawn", "shrimp", "crab", "lobster", "mussel", "clam", "oyster", "sardine", "salmon", "tuna", "cod"]
    }

    # Dietary preference keywords for detection
    DIETARY_KEYWORDS = {
        "Vegan": ["meat", "chicken", "fish", "egg", "milk", "dairy", "honey", "gelatin", "animal"],
        "Vegetarian": ["meat", "chicken", "fish", "prawn", "shrimp"],
        "Keto": [],  # Handled by carb calculation
        "Paleo": ["wheat", "grain", "rice", "corn", "legume", "bean", "lentil", "dairy", "milk", "cheese"],
        "Mediterranean": [],  # Handled by positive flags
        "Low Carb": [],  # Handled by carb calculation
        "General": []  # No restrictions
    }

    @staticmethod
    def get_personalized_analysis(product_data: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized analysis for a product based on user profile.

        Args:
            product_data: Product information including nutrition, ingredients, etc.
            user_profile: User profile with allergens, conditions, preferences, etc.

        Returns:
            Dict containing base_grade, personalized_score, and flags list
        """
        try:
            flags = []

            # Extract user preferences
            user_allergens = user_profile.get('allergens', [])
            user_conditions = user_profile.get('conditions', [])
            user_diet = user_profile.get('dietType', None)
            user_goal = user_profile.get('primaryGoal', None)
            user_custom_needs = user_profile.get('custom_needs', [])

            # Extract product data
            ingredients_text = product_data.get('ingredients_text', '').lower()
            nutrition = product_data.get('nutriments', {})

            # Category 1: Safety (Allergens) - DANGER flags
            flags.extend(PersonalizationEngine._check_allergens(user_allergens, ingredients_text))

            # Category 2: Health Conditions - WARNING flags
            flags.extend(PersonalizationEngine._check_health_conditions(user_conditions, nutrition, user_goal))

            # Category 3: Lifestyle (Dietary Preference) - INFO flags
            flags.extend(PersonalizationEngine._check_dietary_preferences(user_diet, ingredients_text, nutrition))

            # Category 4: Primary Health Goal - SUCCESS flags
            flags.extend(PersonalizationEngine._check_health_goals(user_goal, nutrition))

            # Category 5: Custom Others - INFO flags
            flags.extend(PersonalizationEngine._check_custom_needs(user_custom_needs))

            # Calculate personalized score (optional enhancement)
            personalized_score = PersonalizationEngine._calculate_personalized_score(flags)

            # Get base grade from product data
            base_grade = product_data.get('health_grade', 'C')

            return {
                "base_grade": base_grade,
                "personalized_score": personalized_score,
                "flags": flags
            }

        except Exception as e:
            logger.error(f"Error in personalized analysis: {str(e)}")
            return {
                "base_grade": product_data.get('health_grade', 'C'),
                "personalized_score": 50,
                "flags": [{
                    "type": "warning",
                    "reason": "Analysis Error",
                    "impact": "Unable to perform personalized analysis",
                    "details": "An error occurred while analyzing this product for your profile."
                }]
            }

    @staticmethod
    def _check_allergens(user_allergens: List[str], ingredients_text: str) -> List[Dict[str, str]]:
        """Check for allergen matches in ingredients - DANGER level."""
        flags = []

        for allergen in user_allergens:
            if allergen in PersonalizationEngine.ALLERGEN_KEYWORDS:
                keywords = PersonalizationEngine.ALLERGEN_KEYWORDS[allergen]
                for keyword in keywords:
                    if keyword in ingredients_text:
                        # Find the matched ingredient for detailed info
                        matched_ingredient = PersonalizationEngine._find_matched_ingredient(keyword, ingredients_text)
                        flags.append({
                            "type": "danger",
                            "reason": f"Contains {allergen}",
                            "impact": "Allergen detected - click for details",
                            "details": f"UNSAFE: Contains '{matched_ingredient}' which matches your {allergen} allergy. This ingredient was found in the product ingredients list."
                        })
                        break  # Only flag once per allergen

        return flags

    @staticmethod
    def _check_health_conditions(user_conditions: List[str], nutrition: Dict[str, Any], user_goal: Optional[str]) -> List[Dict[str, str]]:
        """Check health condition warnings."""
        flags = []

        sugar_100g = nutrition.get('sugars_100g', 0) or 0
        added_sugar_100g = nutrition.get('added_sugar_percent', 0) or 0
        sodium_100g = nutrition.get('sodium_100g', 0) or 0
        carbs_100g = nutrition.get('carbohydrates_100g', 0) or 0
        fiber_100g = nutrition.get('fiber_100g', 0) or 0
        sat_fat_100g = nutrition.get('saturated-fat_100g', 0) or 0
        trans_fat = nutrition.get('trans-fat_100g', 0) or 0

        for condition in user_conditions:
            if condition == "Diabetes / Prediabetes" or (user_goal and user_goal == "Sugar Control"):
                if sugar_100g > 10 or added_sugar_100g > 5:
                    flags.append({
                        "type": "warning",
                        "reason": "Sugar Concern",
                        "impact": "May affect glucose levels - click for details",
                        "details": f"High sugar content detected: {sugar_100g:.1f}g sugar per 100g. This may affect glucose levels for individuals with {condition}."
                    })

            elif condition == "Hypertension (High BP)" or (user_goal and user_goal == "Heart Health"):
                if sodium_100g > 400:
                    flags.append({
                        "type": "warning",
                        "reason": "Sodium Concern",
                        "impact": "May affect blood pressure - click for details",
                        "details": f"High sodium content: {sodium_100g:.1f}mg per 100g. This may affect blood pressure for individuals with {condition}."
                    })

            elif condition == "PCOS / PCOD":
                if carbs_100g > 40 and fiber_100g < 3:
                    flags.append({
                        "type": "warning",
                        "reason": "Carb/Fiber Imbalance",
                        "impact": "May affect hormonal balance - click for details",
                        "details": f"High glycemic load detected: {carbs_100g:.1f}g carbs with only {fiber_100g:.1f}g fiber per 100g. This carb/fiber ratio may affect hormonal balance for individuals with {condition}."
                    })

            elif condition == "High Cholesterol":
                if sat_fat_100g > 4 or trans_fat > 0.1:
                    fat_details = []
                    if sat_fat_100g > 4:
                        fat_details.append(f"{sat_fat_100g:.1f}g saturated fat")
                    if trans_fat > 0.1:
                        fat_details.append(f"{trans_fat:.1f}g trans fat")
                    fat_info = " and ".join(fat_details)
                    flags.append({
                        "type": "warning",
                        "reason": "Fat Content Concern",
                        "impact": "May affect cholesterol levels - click for details",
                        "details": f"Contains {fat_info} per 100g. This may affect cholesterol levels for individuals with {condition}."
                    })

        return flags

    @staticmethod
    def _check_dietary_preferences(user_diet: Optional[str], ingredients_text: str, nutrition: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check dietary preference compatibility - INFO level."""
        flags = []

        if not user_diet or user_diet == "General":
            return flags

        if user_diet in ["Vegan", "Vegetarian"]:
            restricted_items = PersonalizationEngine.DIETARY_KEYWORDS[user_diet]
            found_items = []
            for item in restricted_items:
                if item in ingredients_text:
                    found_items.append(item)

            if found_items:
                flags.append({
                    "type": "info",
                    "reason": f"Not suitable for {user_diet}",
                    "impact": "Contains restricted ingredients - click for details",
                    "details": f"This product contains {', '.join(found_items)} which are not suitable for a {user_diet.lower()} diet."
                })

        elif user_diet == "Keto":
            # Calculate net carbs (carbs - fiber)
            carbs_100g = nutrition.get('carbohydrates_100g', 0) or 0
            fiber_100g = nutrition.get('fiber_100g', 0) or 0
            net_carbs = carbs_100g - fiber_100g

            if net_carbs > 7:
                flags.append({
                    "type": "info",
                    "reason": "High Net Carbs",
                    "impact": "May not suit Keto diet - click for details",
                    "details": f"This product contains {net_carbs:.1f}g net carbs per 100g (total carbs: {carbs_100g:.1f}g minus fiber: {fiber_100g:.1f}g). For Keto diets, aim for less than 20-50g net carbs per day."
                })

        elif user_diet == "Paleo":
            restricted_items = PersonalizationEngine.DIETARY_KEYWORDS[user_diet]
            found_items = []
            for item in restricted_items:
                if item in ingredients_text:
                    found_items.append(item)

            if found_items:
                flags.append({
                    "type": "info",
                    "reason": f"Not suitable for {user_diet}",
                    "impact": "Contains modern foods - click for details",
                    "details": f"This product contains {', '.join(found_items)} which are not part of the Paleo diet (focuses on foods available to Paleolithic humans)."
                })

        elif user_diet == "Low Carb":
            carbs_100g = nutrition.get('carbohydrates_100g', 0) or 0
            if carbs_100g > 20:
                flags.append({
                    "type": "info",
                    "reason": "High Carbohydrate Content",
                    "impact": "May not suit Low Carb diet - click for details",
                    "details": f"This product contains {carbs_100g:.1f}g carbohydrates per 100g. For Low Carb diets, aim for less than 50-100g carbs per day."
                })

        return flags

    @staticmethod
    def _check_health_goals(user_goal: Optional[str], nutrition: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check primary health goal alignment - SUCCESS level."""
        flags = []

        if not user_goal:
            return flags

        energy_kcal = nutrition.get('energy-kcal_100g', 0) or 0
        protein_100g = nutrition.get('proteins_100g', 0) or 0
        fiber_100g = nutrition.get('fiber_100g', 0) or 0
        sugar_100g = nutrition.get('sugars_100g', 0) or 0
        sat_fat_100g = nutrition.get('saturated-fat_100g', 0) or 0
        sodium_100g = nutrition.get('sodium_100g', 0) or 0

        if user_goal == "Muscle Gain":
            if protein_100g > 15:
                flags.append({
                    "type": "success",
                    "reason": "High Protein Content",
                    "impact": "Excellent for muscle gain - click for details",
                    "details": f"This product contains {protein_100g:.1f}g protein per 100g, which is excellent for supporting muscle growth and repair. Aim for 1.6-2.2g of protein per kg of body weight daily."
                })

        elif user_goal == "Weight Loss":
            if energy_kcal < 150 and fiber_100g > 4:
                flags.append({
                    "type": "success",
                    "reason": "Low Calorie & High Fiber",
                    "impact": "Supports weight loss goals - click for details",
                    "details": f"This product has only {energy_kcal:.0f} calories and {fiber_100g:.1f}g fiber per 100g. High-fiber, low-calorie foods help with satiety and weight management."
                })

        elif user_goal == "Heart Health":
            if sat_fat_100g < 2 and sodium_100g < 200:
                flags.append({
                    "type": "success",
                    "reason": "Heart Healthy Profile",
                    "impact": "Supports cardiovascular health - click for details",
                    "details": f"This product contains only {sat_fat_100g:.1f}g saturated fat and {sodium_100g:.0f}mg sodium per 100g, making it suitable for heart health goals."
                })

        elif user_goal == "Sugar Control":
            if sugar_100g < 5:
                flags.append({
                    "type": "success",
                    "reason": "Low Sugar Content",
                    "impact": "Supports blood sugar management - click for details",
                    "details": f"This product contains only {sugar_100g:.1f}g sugar per 100g, which is beneficial for maintaining stable blood sugar levels."
                })

        return flags

    @staticmethod
    def _check_custom_needs(user_custom_needs: List[str]) -> List[Dict[str, str]]:
        """Check custom user needs - INFO level."""
        flags = []

        for custom_need in user_custom_needs:
            flags.append({
                "type": "info",
                "reason": "Custom Analysis Pending",
                "impact": "Expert review in progress - click for details",
                "details": f"Our nutrition experts are currently reviewing '{custom_need}' for personalized analysis. We'll provide specific recommendations once the review is complete."
            })

        return flags

    @staticmethod
    def _find_matched_ingredient(keyword: str, ingredients_text: str) -> str:
        """Find the actual matched ingredient name for better messaging."""
        # Simple regex to find word boundaries around the keyword
        pattern = r'\b\w*' + re.escape(keyword) + r'\w*\b'
        matches = re.findall(pattern, ingredients_text, re.IGNORECASE)

        if matches:
            return matches[0].strip()

        return keyword  # Fallback to the keyword itself

    @staticmethod
    def _calculate_personalized_score(flags: List[Dict[str, str]]) -> int:
        """Calculate a personalized fit score based on flags (0-100)."""
        if not flags:
            return 75  # Neutral score if no flags

        # Scoring weights
        weights = {
            "danger": -30,
            "warning": -15,
            "info": -5,
            "success": 20
        }

        base_score = 75  # Start neutral
        total_adjustment = 0

        for flag in flags:
            flag_type = flag.get("type", "info")
            adjustment = weights.get(flag_type, 0)
            total_adjustment += adjustment

        final_score = max(0, min(100, base_score + total_adjustment))
        return int(final_score)


# Convenience function
def get_personalized_analysis(product_data: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to get personalized analysis.

    Args:
        product_data: Product information
        user_profile: User profile data

    Returns:
        Personalized analysis with flags
    """
    return PersonalizationEngine.get_personalized_analysis(product_data, user_profile)
