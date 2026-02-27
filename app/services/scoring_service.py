"""
Indian Nutrition Rating (INR) / Health Star Rating (HSR) Scoring Engine for PickBetter

This service implements scientifically accurate nutrition scoring based on INR/HSR models,
with separate logic for solids and beverages.
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class NutritionScorer:
    """
    INR/HSR-based nutrition scoring engine for Indian dietary context.

    Implements data normalization, baseline points calculation, positive points calculation,
    and final grading with different scales for solids vs beverages.
    """

    # Grading scales for solids
    SOLID_GRADING_SCALE = {
        'A': (-float('inf'), -1),
        'B': (0, 10),
        'C': (11, 18),
        'D': (19, 26),
        'E': (27, float('inf'))
    }

    # Grading scales for beverages (stricter)
    BEVERAGE_GRADING_SCALE = {
        'A': (-float('inf'), 1),  # Water gets A always
        'B': (2, 5),
        'C': (6, 9),
        'D': (10, float('inf')),
        'E': (float('inf'), float('inf'))  # Beverages with score >= 10 get E
    }

    @staticmethod
    def normalize_to_100g(nutrition_data: Dict[str, Union[float, int, str]], serving_size: Optional[float] = None) -> Dict[str, float]:
        """
        Normalize nutrition data to per 100g/ml values.

        Args:
            nutrition_data: Raw nutrition data dict
            serving_size: Serving size in grams/ml (if data is per serving)

        Returns:
            Normalized nutrition data with all values per 100g/ml
        """
        if not nutrition_data:
            return {}

        normalized = {}

        # Common nutrient fields to normalize
        nutrient_fields = [
            'energy-kcal', 'proteins', 'carbohydrates', 'sugars', 'fat', 'saturated-fat',
            'trans-fat', 'fiber', 'sodium', 'calcium', 'iron', 'vitamin-c'
        ]

        for field in nutrient_fields:
            value = nutrition_data.get(field)
            if value is None or value == '':
                continue

            try:
                # Convert to float if it's a string
                if isinstance(value, str):
                    value = float(value.replace(',', '').strip())
                elif not isinstance(value, (int, float)):
                    continue

                # If serving_size is provided and data appears to be per serving, normalize
                if serving_size and serving_size > 0:
                    # Check if field name suggests per serving (this is heuristic)
                    if 'per_serving' in str(nutrition_data.get('serving_size_unit', '')).lower():
                        value = (value / serving_size) * 100
                    # For energy and nutrients, assume per serving if serving_size provided
                    elif field in ['energy-kcal', 'proteins', 'carbohydrates', 'sugars', 'fat', 'saturated-fat', 'fiber', 'sodium']:
                        # Only normalize if the value seems unreasonably high for 100g
                        if field == 'energy-kcal' and value > 900:  # kcal per serving > 900 suggests per serving
                            value = (value / serving_size) * 100
                        elif field in ['proteins', 'carbohydrates', 'sugars', 'fat', 'fiber'] and value > 100:  # grams per serving > 100g suggests per serving
                            value = (value / serving_size) * 100
                        elif field == 'sodium' and value > 2000:  # mg per serving > 2000mg suggests per serving
                            value = (value / serving_size) * 100

                normalized[field] = float(value)

            except (ValueError, TypeError):
                logger.warning(f"Could not normalize field {field} with value {value}")
                continue

        # Calculate FVNL% if we have the necessary data
        carbohydrates_100g = normalized.get('carbohydrates', 0)
        fiber_100g = normalized.get('fiber', 0)
        protein_100g = normalized.get('proteins', 0)

        if carbohydrates_100g > 0:
            fvnl_percent = ((fiber_100g + protein_100g) / carbohydrates_100g) * 100
            normalized['fvnl_percent'] = min(fvnl_percent, 100)  # Cap at 100%

        # Calculate added sugar percentage if available
        total_sugars = normalized.get('sugars', 0)
        if carbohydrates_100g > 0 and total_sugars > 0:
            added_sugar_percent = (total_sugars / carbohydrates_100g) * 100
            normalized['added_sugar_percent'] = min(added_sugar_percent, 100)

        logger.info(f"Normalized nutrition data: {normalized}")
        return normalized

    @staticmethod
    def _get_baseline_points(energy: float, sat_fat: float, sugar: float, sodium: float, is_beverage: bool) -> int:
        """
        Calculate baseline points (bad nutrients) based on INR/HSR model.

        Args:
            energy: Energy in kcal per 100g
            sat_fat: Saturated fat in g per 100g
            sugar: Total sugar in g per 100g
            sodium: Sodium in mg per 100g
            is_beverage: Whether the product is a beverage

        Returns:
            Total baseline points (0-40 max)
        """
        points = 0

        if is_beverage:
            # Stricter beverage logic
            # Energy: +1 point per 7 kcal (max 10)
            energy_points = min(math.floor(energy / 7), 10)
            points += energy_points

            # Sat Fat: +1 point per 1g (max 10) - same as solids
            sat_fat_points = min(math.floor(sat_fat / 1), 10)
            points += sat_fat_points

            # Total Sugar: +1 point per 1.5g (max 10) - stricter than solids
            sugar_points = min(math.floor(sugar / 1.5), 10)
            points += sugar_points

            # Sodium: +1 point per 90mg (max 10) - same as solids
            sodium_points = min(math.floor(sodium / 90), 10)
            points += sodium_points
        else:
            # Solids logic
            # Energy: +1 point per 80 kcal (max 10)
            energy_points = min(math.floor(energy / 80), 10)
            points += energy_points

            # Sat Fat: +1 point per 1g (max 10)
            sat_fat_points = min(math.floor(sat_fat / 1), 10)
            points += sat_fat_points

            # Total Sugar: +1 point per 4.5g (max 10)
            sugar_points = min(math.floor(sugar / 4.5), 10)
            points += sugar_points

            # Sodium: +1 point per 90mg (max 10)
            sodium_points = min(math.floor(sodium / 90), 10)
            points += sodium_points

        return points

    @staticmethod
    def _get_positive_points(fiber: float, protein: float, fvnl_percent: float, is_beverage: bool) -> int:
        """
        Calculate positive points (good nutrients) based on INR/HSR model.

        Args:
            fiber: Fiber in g per 100g
            protein: Protein in g per 100g
            fvnl_percent: Fruit/Veg/Nuts/Legumes percentage
            is_beverage: Whether the product is a beverage

        Returns:
            Total positive points
        """
        points = 0

        if is_beverage:
            # Beverages: stricter criteria
            # Fruit/Veg %: only counts if >40%
            if fvnl_percent > 40:
                # Fiber: +1 point per 0.9g
                fiber_points = math.floor(fiber / 0.9)
                points += fiber_points

                # Protein: +1 point per 1.6g
                protein_points = math.floor(protein / 1.6)
                points += protein_points

            # FVNL points: 0-5 based on percentage (>80% = 5 pts)
            if fvnl_percent > 80:
                points += 5
            elif fvnl_percent > 60:
                points += 4
            elif fvnl_percent > 40:
                points += 3
            elif fvnl_percent > 20:
                points += 2
            elif fvnl_percent > 0:
                points += 1
        else:
            # Solids logic
            # Fiber: +1 point per 0.9g
            fiber_points = math.floor(fiber / 0.9)
            points += fiber_points

            # Protein: +1 point per 1.6g
            protein_points = math.floor(protein / 1.6)
            points += protein_points

            # FVNL points: 0-5 based on percentage (>80% = 5 pts)
            if fvnl_percent > 80:
                points += 5
            elif fvnl_percent > 60:
                points += 4
            elif fvnl_percent > 40:
                points += 3
            elif fvnl_percent > 20:
                points += 2
            elif fvnl_percent > 0:
                points += 1

        return points

    @staticmethod
    def _calculate_final_score(baseline_points: int, positive_points: int) -> int:
        """
        Calculate final INR/HSR score.

        Args:
            baseline_points: Points from bad nutrients
            positive_points: Points from good nutrients

        Returns:
            Final score (baseline - positive)
        """
        return baseline_points - positive_points

    @staticmethod
    def _get_grade_from_score(score: int, is_beverage: bool, is_water: bool = False) -> str:
        """
        Get grade (A-E) based on final score and product type.

        Args:
            score: Final calculated score
            is_beverage: Whether the product is a beverage
            is_water: Special case for water (always gets A)

        Returns:
            Grade letter (A-E)
        """
        if is_water:
            return 'A'  # Water always gets A

        grading_scale = NutritionScorer.BEVERAGE_GRADING_SCALE if is_beverage else NutritionScorer.SOLID_GRADING_SCALE

        for grade, (min_score, max_score) in grading_scale.items():
            if min_score <= score <= max_score:
                return grade

        # Default fallback
        return 'E'

    @staticmethod
    def _apply_quality_penalties(grade: str, added_sugar_percent: float, trans_fat: float) -> str:
        """
        Apply quality caps/penalties to the grade.

        Args:
            grade: Current grade before penalties
            added_sugar_percent: Percentage of added sugar
            trans_fat: Trans fat content in g per 100g

        Returns:
            Adjusted grade after penalties
        """
        # Trans Fat Cap: If trans_fat > 0.2g, set grade to E
        if trans_fat > 0.2:
            return 'E'

        # Added Sugar Cap: If added_sugar > 10%, cap max grade at C
        if added_sugar_percent > 10:
            grade_hierarchy = ['A', 'B', 'C', 'D', 'E']
            current_index = grade_hierarchy.index(grade) if grade in grade_hierarchy else 4
            # Cap at C (index 2)
            capped_index = min(current_index, 2)
            return grade_hierarchy[capped_index]

        return grade

    @classmethod
    def calculate_inr_score(cls, nutrition_data: Dict[str, Union[float, int, str]],
                          serving_size: Optional[float] = None,
                          is_beverage: bool = False,
                          is_water: bool = False) -> Dict:
        """
        Calculate INR/HSR score for a product.

        Args:
            nutrition_data: Raw nutrition data dict
            serving_size: Serving size in grams/ml (if data is per serving)
            is_beverage: Whether the product is a beverage
            is_water: Special case for water

        Returns:
            Dictionary containing score, grade, breakdown, and factors
        """
        try:
            # Step 1: Normalize data to 100g
            normalized = cls.normalize_to_100g(nutrition_data, serving_size)

            if not normalized:
                return cls._create_error_response("No valid nutrition data provided")

            # Extract normalized values with defaults
            energy = normalized.get('energy-kcal', 0)
            sat_fat = normalized.get('saturated-fat', 0)
            sugar = normalized.get('sugars', 0)
            sodium = normalized.get('sodium', 0)
            fiber = normalized.get('fiber', 0)
            protein = normalized.get('proteins', 0)
            fvnl_percent = normalized.get('fvnl_percent', 0)
            added_sugar_percent = normalized.get('added_sugar_percent', 0)
            trans_fat = normalized.get('trans-fat', 0)

            # Step 2: Calculate baseline points (bad nutrients)
            baseline_points = cls._get_baseline_points(energy, sat_fat, sugar, sodium, is_beverage)

            # Step 3: Calculate positive points (good nutrients)
            positive_points = cls._get_positive_points(fiber, protein, fvnl_percent, is_beverage)

            # Step 4: Calculate final score
            final_score = cls._calculate_final_score(baseline_points, positive_points)

            # Step 5: Get initial grade
            initial_grade = cls._get_grade_from_score(final_score, is_beverage, is_water)

            # Step 6: Apply quality penalties
            final_grade = cls._apply_quality_penalties(initial_grade, added_sugar_percent, trans_fat)

            # Step 7: Create detailed breakdown
            breakdown = {
                "baseline_points": baseline_points,
                "positive_points": positive_points,
                "final_score": final_score,
                "energy_points": min(math.floor(energy / (7 if is_beverage else 80)), 10),
                "sat_fat_points": min(math.floor(sat_fat / 1), 10),
                "sugar_points": min(math.floor(sugar / (1.5 if is_beverage else 4.5)), 10),
                "sodium_points": min(math.floor(sodium / 90), 10),
                "fiber_points": math.floor(fiber / 0.9),
                "protein_points": math.floor(protein / 1.6),
                "fvnl_points": cls._calculate_fvnl_points(fvnl_percent, is_beverage)
            }

            # Step 8: Analyze factors
            factors = cls._analyze_factors(breakdown, is_beverage)

            result = {
                "score": final_score,
                "grade": final_grade,
                "initial_grade": initial_grade,
                "breakdown": breakdown,
                "factors": factors,
                "normalized_nutrition": normalized,
                "product_type": "beverage" if is_beverage else "solid",
                "is_water": is_water,
                "calculated_at": datetime.utcnow().isoformat(),
                "model": "INR_HSR_v1"
            }

            logger.info(f"Calculated INR/HSR score: {final_score} (Grade {final_grade}) for {'beverage' if is_beverage else 'solid'}")
            return result

        except Exception as e:
            logger.error(f"Error calculating INR/HSR score: {str(e)}")
            return cls._create_error_response(f"Calculation error: {str(e)}")

    @staticmethod
    def _calculate_fvnl_points(fvnl_percent: float, is_beverage: bool) -> int:
        """Calculate FVNL points based on percentage."""
        if is_beverage and fvnl_percent <= 40:
            return 0  # Beverages only get FVNL points if >40%

        if fvnl_percent > 80:
            return 5
        elif fvnl_percent > 60:
            return 4
        elif fvnl_percent > 40:
            return 3
        elif fvnl_percent > 20:
            return 2
        elif fvnl_percent > 0:
            return 1
        return 0

    @staticmethod
    def _analyze_factors(breakdown: Dict, is_beverage: bool) -> Dict[str, List[str]]:
        """Analyze strengths and concerns based on score breakdown."""
        strengths = []
        concerns = []

        # Check for positive factors
        if breakdown.get('fiber_points', 0) > 0:
            strengths.append("Good fiber content")
        if breakdown.get('protein_points', 0) > 0:
            strengths.append("Good protein content")
        if breakdown.get('fvnl_points', 0) >= 3:
            strengths.append("High FVNL content")
        if breakdown.get('energy_points', 0) == 0:
            strengths.append("Low energy density")
        if breakdown.get('sat_fat_points', 0) == 0:
            strengths.append("Low saturated fat")

        # Check for concerns
        if breakdown.get('sugar_points', 0) > 5:
            concerns.append("High sugar content")
        if breakdown.get('sodium_points', 0) > 5:
            concerns.append("High sodium content")
        if breakdown.get('energy_points', 0) > 5:
            concerns.append("High energy density")
        if breakdown.get('sat_fat_points', 0) > 5:
            concerns.append("High saturated fat")

        return {
            "strengths": strengths,
            "concerns": concerns
        }

    @staticmethod
    def _create_error_response(message: str) -> Dict:
        """Create standardized error response."""
        return {
            "score": 0,
            "grade": "E",
            "error": message,
            "breakdown": {},
            "factors": {"strengths": [], "concerns": [message]},
            "normalized_nutrition": {},
            "calculated_at": datetime.utcnow().isoformat(),
            "model": "INR_HSR_v1"
        }


# Convenience function
def calculate_inr_score(nutrition_data: Dict[str, Union[float, int, str]],
                       serving_size: Optional[float] = None,
                       is_beverage: bool = False,
                       is_water: bool = False) -> Dict:
    """
    Convenience function to calculate INR/HSR score.

    Args:
        nutrition_data: Raw nutrition data dict
        serving_size: Serving size in grams/ml (if data is per serving)
        is_beverage: Whether the product is a beverage
        is_water: Special case for water

    Returns:
        INR/HSR score calculation result
    """
    return NutritionScorer.calculate_inr_score(nutrition_data, serving_size, is_beverage, is_water)
