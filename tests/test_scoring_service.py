"""
Unit tests for the Indian Health Score Engine.

Tests cover:
- Edge cases for scoring calculations
- Products with missing data
- Very healthy and very unhealthy products
- Grade boundary conditions
- Data completeness calculations
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from app.services.scoring_service import IndianHealthScorer, calculate_indian_health_score
from app.models.product import Product


class TestIndianHealthScorer:
    """Test cases for IndianHealthScorer class."""
    
    def create_test_product(self, **kwargs):
        """Create a test product with custom nutrition data."""
        defaults = {
            'barcode': '1234567890123',
            'name': 'Test Product',
            'brand': 'Test Brand',
            'category': 'Test Category',
            'nutriments': {
                'sugars_100g': 10.0,
                'sodium_100g': 300.0,
                'trans-fat_100g': 0.1,
                'saturated-fat_100g': 5.0,
                'proteins_100g': 8.0,
                'fiber_100g': 4.0,
            },
            'ingredients_text': 'water, sugar, salt, natural flavors'
        }
        defaults.update(kwargs)
        
        product = Mock(spec=Product)
        product.barcode = defaults['barcode']
        product.name = defaults['name']
        product.brand = defaults['brand']
        product.category = defaults['category']
        product.nutriments = defaults['nutriments']
        product.ingredients_text = defaults['ingredients_text']
        product.normalized_nutrition = None
        
        return product
    
    def test_perfectly_healthy_product(self):
        """Test a perfectly healthy product should score high (80-100)."""
        product = self.create_test_product(
            nutriments={
                'sugars_100g': 2.0,  # Low sugar
                'sodium_100g': 100.0,  # Low sodium
                'trans-fat_100g': 0.0,  # No trans fats
                'saturated-fat_100g': 2.0,  # Low saturated fat
                'proteins_100g': 15.0,  # High protein
                'fiber_100g': 8.0,  # High fiber
            },
            ingredients_text='whole grains, nuts, seeds, dried fruit'
        )
        
        result = calculate_indian_health_score(product)
        
        assert result['score'] >= 80, f"Expected score >= 80, got {result['score']}"
        assert result['grade'] in ['A'], f"Expected grade A, got {result['grade']}"
        assert 'Good protein content' in result['factors']['strengths']
        assert 'High fiber content' in result['factors']['strengths']
        assert len(result['factors']['concerns']) == 0
    
    def test_very_unhealthy_product(self):
        """Test a very unhealthy product should score low (0-30)."""
        product = self.create_test_product(
            nutriments={
                'sugars_100g': 20.0,  # Very high sugar
                'sodium_100g': 800.0,  # Very high sodium
                'trans-fat_100g': 0.5,  # High trans fats
                'saturated-fat_100g': 15.0,  # High saturated fat
                'proteins_100g': 2.0,  # Low protein
                'fiber_100g': 1.0,  # Low fiber
            },
            ingredients_text='sugar, corn syrup, hydrogenated oil, artificial flavors, preservatives, color additives, emulsifiers, stabilizers'
        )
        
        result = calculate_indian_health_score(product)
        
        assert result['score'] <= 30, f"Expected score <= 30, got {result['score']}"
        assert result['grade'] in ['D', 'E'], f"Expected grade D or E, got {result['grade']}"
        assert 'High sugar content' in result['factors']['concerns']
        assert 'High sodium content' in result['factors']['concerns']
        assert 'Contains trans fats' in result['factors']['concerns']
    
    def test_moderate_product(self):
        """Test a moderate product should score in the middle range (40-79)."""
        product = self.create_test_product(
            nutriments={
                'sugars_100g': 8.0,  # Moderate sugar
                'sodium_100g': 400.0,  # Moderate sodium
                'trans-fat_100g': 0.1,  # Low trans fats
                'saturated-fat_100g': 6.0,  # Moderate saturated fat
                'proteins_100g': 6.0,  # Moderate protein
                'fiber_100g': 3.0,  # Moderate fiber
            },
            ingredients_text='wheat flour, sugar, vegetable oil, salt'
        )
        
        result = calculate_indian_health_score(product)
        
        assert 40 <= result['score'] <= 79, f"Expected score 40-79, got {result['score']}"
        assert result['grade'] in ['B', 'C'], f"Expected grade B or C, got {result['grade']}"
    
    def test_missing_nutrition_data(self):
        """Test product with missing nutrition data."""
        product = self.create_test_product(
            nutriments={},
            ingredients_text=None
        )
        
        result = calculate_indian_health_score(product)
        
        # Should handle missing data gracefully
        assert result['score'] == 100, f"Expected score 100 for missing data, got {result['score']}"
        assert result['grade'] == 'A', f"Expected grade A for missing data, got {result['grade']}"
        assert result['data_completeness'] == 0.0, f"Expected 0% completeness, got {result['data_completeness']}"
    
    def test_partial_nutrition_data(self):
        """Test product with partial nutrition data."""
        product = self.create_test_product(
            nutriments={
                'sugars_100g': 5.0,
                'proteins_100g': 10.0,
                # Missing other fields
            }
        )
        
        result = calculate_indian_health_score(product)
        
        # Should calculate completeness correctly
        assert result['data_completeness'] > 0, f"Expected some completeness, got {result['data_completeness']}"
        assert result['data_completeness'] < 100, f"Expected partial completeness, got {result['data_completeness']}"
    
    def test_grade_boundaries(self):
        """Test grade boundary conditions."""
        # Test Grade A boundary (80)
        product_a = self.create_test_product(
            nutriments={
                'sugars_100g': 3.0,
                'sodium_100g': 150.0,
                'trans-fat_100g': 0.0,
                'saturated-fat_100g': 3.0,
                'proteins_100g': 12.0,
                'fiber_100g': 7.0,
            }
        )
        result_a = calculate_indian_health_score(product_a)
        assert result_a['grade'] == 'A', f"Expected grade A at score {result_a['score']}"
        
        # Test Grade B boundary (60-79)
        product_b = self.create_test_product(
            nutriments={
                'sugars_100g': 8.0,
                'sodium_100g': 350.0,
                'trans-fat_100g': 0.1,
                'saturated-fat_100g': 6.0,
                'proteins_100g': 8.0,
                'fiber_100g': 4.0,
            }
        )
        result_b = calculate_indian_health_score(product_b)
        assert result_b['grade'] in ['A', 'B'], f"Expected grade A or B at score {result_b['score']}"
        
        # Test Grade E boundary (0-19)
        product_e = self.create_test_product(
            nutriments={
                'sugars_100g': 25.0,
                'sodium_100g': 1000.0,
                'trans-fat_100g': 1.0,
                'saturated-fat_100g': 20.0,
                'proteins_100g': 1.0,
                'fiber_100g': 0.5,
            }
        )
        result_e = calculate_indian_health_score(product_e)
        assert result_e['grade'] in ['D', 'E'], f"Expected grade D or E at score {result_e['score']}"
    
    def test_sugar_thresholds(self):
        """Test sugar content thresholds."""
        # Test >15g (should get -20 penalty)
        product_high = self.create_test_product(nutriments={'sugars_100g': 20.0})
        result_high = calculate_indian_health_score(product_high)
        assert result_high['breakdown']['sugar_penalty'] == -20
        
        # Test 10-15g (should get -10 penalty)
        product_medium = self.create_test_product(nutriments={'sugars_100g': 12.0})
        result_medium = calculate_indian_health_score(product_medium)
        assert result_medium['breakdown']['sugar_penalty'] == -10
        
        # Test 5-10g (should get -5 penalty)
        product_low = self.create_test_product(nutriments={'sugars_100g': 7.0})
        result_low = calculate_indian_health_score(product_low)
        assert result_low['breakdown']['sugar_penalty'] == -5
        
        # Test <5g (should get 0 penalty)
        product_very_low = self.create_test_product(nutriments={'sugars_100g': 3.0})
        result_very_low = calculate_indian_health_score(product_very_low)
        assert result_very_low['breakdown']['sugar_penalty'] == 0
    
    def test_sodium_thresholds(self):
        """Test sodium content thresholds."""
        # Test >600mg (should get -20 penalty)
        product_high = self.create_test_product(nutriments={'sodium_100g': 800.0})
        result_high = calculate_indian_health_score(product_high)
        assert result_high['breakdown']['sodium_penalty'] == -20
        
        # Test 400-600mg (should get -10 penalty)
        product_medium = self.create_test_product(nutriments={'sodium_100g': 500.0})
        result_medium = calculate_indian_health_score(product_medium)
        assert result_medium['breakdown']['sodium_penalty'] == -10
        
        # Test 200-400mg (should get -5 penalty)
        product_low = self.create_test_product(nutriments={'sodium_100g': 300.0})
        result_low = calculate_indian_health_score(product_low)
        assert result_low['breakdown']['sodium_penalty'] == -5
        
        # Test <200mg (should get 0 penalty)
        product_very_low = self.create_test_product(nutriments={'sodium_100g': 100.0})
        result_very_low = calculate_indian_health_score(product_very_low)
        assert result_very_low['breakdown']['sodium_penalty'] == 0
    
    def test_trans_fat_thresholds(self):
        """Test trans fat thresholds."""
        # Test >0.2g (should get -25 penalty)
        product_high = self.create_test_product(nutriments={'trans-fat_100g': 0.5})
        result_high = calculate_indian_health_score(product_high)
        assert result_high['breakdown']['trans_fat_penalty'] == -25
        
        # Test 0.1-0.2g (should get -10 penalty)
        product_medium = self.create_test_product(nutriments={'trans-fat_100g': 0.15})
        result_medium = calculate_indian_health_score(product_medium)
        assert result_medium['breakdown']['trans_fat_penalty'] == -10
        
        # Test <0.1g (should get 0 penalty)
        product_low = self.create_test_product(nutriments={'trans-fat_100g': 0.05})
        result_low = calculate_indian_health_score(product_low)
        assert result_low['breakdown']['trans_fat_penalty'] == 0
    
    def test_protein_bonuses(self):
        """Test protein content bonuses."""
        # Test >10g (should get +10 bonus)
        product_high = self.create_test_product(nutriments={'proteins_100g': 15.0})
        result_high = calculate_indian_health_score(product_high)
        assert result_high['breakdown']['protein_bonus'] == 10
        
        # Test 5-10g (should get +5 bonus)
        product_medium = self.create_test_product(nutriments={'proteins_100g': 7.0})
        result_medium = calculate_indian_health_score(product_medium)
        assert result_medium['breakdown']['protein_bonus'] == 5
        
        # Test <5g (should get 0 bonus)
        product_low = self.create_test_product(nutriments={'proteins_100g': 3.0})
        result_low = calculate_indian_health_score(product_low)
        assert result_low['breakdown']['protein_bonus'] == 0
    
    def test_fiber_bonuses(self):
        """Test fiber content bonuses."""
        # Test >6g (should get +10 bonus)
        product_high = self.create_test_product(nutriments={'fiber_100g': 8.0})
        result_high = calculate_indian_health_score(product_high)
        assert result_high['breakdown']['fiber_bonus'] == 10
        
        # Test 3-6g (should get +5 bonus)
        product_medium = self.create_test_product(nutriments={'fiber_100g': 4.0})
        result_medium = calculate_indian_health_score(product_medium)
        assert result_medium['breakdown']['fiber_bonus'] == 5
        
        # Test <3g (should get 0 bonus)
        product_low = self.create_test_product(nutriments={'fiber_100g': 2.0})
        result_low = calculate_indian_health_score(product_low)
        assert result_low['breakdown']['fiber_bonus'] == 0
    
    def test_additives_penalty(self):
        """Test additives penalty calculation."""
        # Test with many additives
        product_many = self.create_test_product(
            ingredients_text='sugar, water, artificial flavors, preservatives, color additives, emulsifiers, stabilizers, antioxidants, sodium benzoate, potassium sorbate'
        )
        result_many = calculate_indian_health_score(product_many)
        assert result_many['breakdown']['additives_penalty'] <= -15, "Should max out at -15 penalty"
        
        # Test with few additives
        product_few = self.create_test_product(
            ingredients_text='whole wheat, water, sea salt'
        )
        result_few = calculate_indian_health_score(product_few)
        assert result_few['breakdown']['additives_penalty'] >= -6, "Should have minimal penalty"
        
        # Test with no additives
        product_none = self.create_test_product(
            ingredients_text='organic whole grains, nuts, seeds'
        )
        result_none = calculate_indian_health_score(product_none)
        assert result_none['breakdown']['additives_penalty'] == 0, "Should have no penalty"
    
    def test_score_clamping(self):
        """Test that scores are properly clamped between 0-100."""
        # Test very high penalties (should clamp to 0)
        product_very_bad = self.create_test_product(
            nutriments={
                'sugars_100g': 50.0,
                'sodium_100g': 2000.0,
                'trans-fat_100g': 5.0,
                'saturated-fat_100g': 50.0,
            },
            ingredients_text='sugar, artificial flavors, preservatives, color additives, emulsifiers, stabilizers, antioxidants, acid, sodium, potassium, calcium, magnesium, phosphate, nitrate, sulfite'
        )
        result_very_bad = calculate_indian_health_score(product_very_bad)
        assert result_very_bad['score'] == 0, f"Score should be clamped to 0, got {result_very_bad['score']}"
        
        # Test perfect product (should be 100)
        product_perfect = self.create_test_product(
            nutriments={
                'sugars_100g': 0.0,
                'sodium_100g': 0.0,
                'trans-fat_100g': 0.0,
                'saturated-fat_100g': 0.0,
                'proteins_100g': 20.0,
                'fiber_100g': 15.0,
            },
            ingredients_text='organic whole grains, nuts, seeds, dried fruit'
        )
        result_perfect = calculate_indian_health_score(product_perfect)
        assert result_perfect['score'] == 100, f"Perfect product should score 100, got {result_perfect['score']}"
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test with None product
        with pytest.raises(Exception):
            calculate_indian_health_score(None)
        
        # Test with product that raises exception during calculation
        product_error = Mock(spec=Product)
        product_error.barcode = '123'
        product_error.nutriments = Mock(side_effect=Exception("Test error"))
        
        result = calculate_indian_health_score(product_error)
        assert result['score'] == 50, f"Error should return default score 50, got {result['score']}"
        assert result['grade'] == 'C', f"Error should return default grade C, got {result['grade']}"
        assert 'Error calculating score' in result['factors']['concerns']


if __name__ == '__main__':
    pytest.main([__file__])
