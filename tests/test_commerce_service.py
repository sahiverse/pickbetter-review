#!/usr/bin/env python3
"""
Unit Tests for Commerce Link Service
Tests deep link generation for quick-commerce platforms
"""

import pytest
import urllib.parse
from unittest.mock import Mock, AsyncMock
from app.services.commerce_service import CommerceLinkService


class TestCommerceLinkService:
    """Test cases for CommerceLinkService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_product(self):
        """Mock product object."""
        product = Mock()
        product.barcode = "8901234567890"
        product.name = "Britannia Good Day Oats Biscuits"
        product.brand = "Britannia"
        product.category = "biscuits"
        return product
    
    @pytest.fixture
    def commerce_service(self, mock_db):
        """Commerce service instance."""
        return CommerceLinkService(mock_db)
    
    def test_platform_configs(self):
        """Test platform configurations are properly defined."""
        expected_platforms = ["blinkit", "zepto", "instamart"]
        assert list(CommerceLinkService.PLATFORM_CONFIGS.keys()) == expected_platforms
        
        # Test Blinkit config
        blinkit_config = CommerceLinkService.PLATFORM_CONFIGS["blinkit"]
        assert blinkit_config["name"] == "Blinkit"
        assert blinkit_config["app_scheme"] == "blinkit://search"
        assert blinkit_config["web_url"] == "https://blinkit.com/s/"
        assert blinkit_config["query_param"] == "q"
    
    def test_clean_text(self, commerce_service):
        """Test text cleaning for search queries."""
        # Basic cleaning
        assert commerce_service._clean_text("Britannia Good Day") == "Britannia Good Day"
        assert commerce_service._clean_text("Good Day! Biscuits?") == "Good Day Biscuits"
        
        # Remove marketing terms
        assert commerce_service._clean_text("Pack of 200g") == ""
        assert commerce_service._clean_text("New Fresh Best Premium") == "Fresh Best"
        
        # Handle edge cases
        assert commerce_service._clean_text("") == ""
        assert commerce_service._clean_text(None) == ""
        assert commerce_service._clean_text("A") == ""
        assert commerce_service._clean_text("AB") == "Ab"
    
    def test_build_search_query(self, commerce_service, mock_product):
        """Test search query building."""
        query = commerce_service._build_search_query(mock_product)
        expected = "Britannia+Britannia+Good+Day+Oats+Biscuits"
        assert query == expected
    
    def test_build_search_query_brand_only(self, commerce_service):
        """Test search query with brand only."""
        product = Mock()
        product.brand = "Amul"
        product.name = None
        product.category = "dairy"
        
        query = commerce_service._build_search_query(product)
        expected = "Amul"
        assert query == expected
    
    def test_build_search_query_name_only(self, commerce_service):
        """Test search query with name only."""
        product = Mock()
        product.brand = None
        product.name = "Milk Chocolate"
        product.category = "confectionery"
        
        query = commerce_service._build_search_query(product)
        expected = "Milk+Chocolate"
        assert query == expected
    
    def test_build_search_query_category_fallback(self, commerce_service):
        """Test search query fallback to category."""
        product = Mock()
        product.brand = None
        product.name = None
        product.category = "beverages"
        
        query = commerce_service._build_search_query(product)
        expected = "Beverages"
        assert query == expected
    
    def test_generate_platform_link(self, commerce_service):
        """Test platform link generation."""
        config = CommerceLinkService.PLATFORM_CONFIGS["blinkit"]
        search_query = "britannia+good+day"
        
        link_data = commerce_service._generate_platform_link(config, search_query)
        
        assert link_data["platform"] == "Blinkit"
        assert link_data["platform_key"] == "blinkit"
        assert link_data["deep_link"] == "blinkit://search?q=britannia+good+day"
        assert link_data["fallback_url"] == "https://blinkit.com/s/?q=britannia+good+day"
    
    def test_get_supported_platforms(self, commerce_service):
        """Test getting supported platforms."""
        platforms = commerce_service.get_supported_platforms()
        
        assert len(platforms) == 3
        assert platforms[0]["key"] == "blinkit"
        assert platforms[0]["name"] == "Blinkit"
        assert "app_scheme" in platforms[0]
        assert "web_url" in platforms[0]
    
    @pytest.mark.asyncio
    async def test_generate_buy_links_success(self, commerce_service, mock_product, mock_db):
        """Test successful buy links generation."""
        # Mock product service
        commerce_service.product_service = AsyncMock()
        commerce_service.product_service.get_by_barcode.return_value = mock_product
        
        # Test with all platforms
        result = await commerce_service.generate_buy_links("8901234567890")
        
        assert result["product"]["barcode"] == "8901234567890"
        assert result["product"]["name"] == "Britannia Good Day Oats Biscuits"
        assert len(result["links"]) == 3
        
        # Check Blinkit link
        blinkit_link = next(link for link in result["links"] if link["platform"] == "Blinkit")
        assert "blinkit://search" in blinkit_link["deep_link"]
        assert "https://blinkit.com/s/" in blinkit_link["fallback_url"]
        
        # Check Zepto link
        zepto_link = next(link for link in result["links"] if link["platform"] == "Zepto")
        assert "zepto://search" in zepto_link["deep_link"]
        assert "https://www.zeptonow.com/search" in zepto_link["fallback_url"]
        
        # Check Instamart link
        instamart_link = next(link for link in result["links"] if link["platform"] == "Instamart")
        assert "swiggy://instamart/search" in instamart_link["deep_link"]
        assert "https://www.swiggy.com/instamart/search" in instamart_link["fallback_url"]
    
    @pytest.mark.asyncio
    async def test_generate_buy_links_specific_platforms(self, commerce_service, mock_product, mock_db):
        """Test buy links generation for specific platforms."""
        # Mock product service
        commerce_service.product_service = AsyncMock()
        commerce_service.product_service.get_by_barcode.return_value = mock_product
        
        # Test with specific platforms
        result = await commerce_service.generate_buy_links(
            "8901234567890", 
            platforms=["blinkit", "zepto"]
        )
        
        assert len(result["links"]) == 2
        platforms = [link["platform"] for link in result["links"]]
        assert "Blinkit" in platforms
        assert "Zepto" in platforms
        assert "Instamart" not in platforms
    
    @pytest.mark.asyncio
    async def test_generate_buy_links_product_not_found(self, commerce_service, mock_db):
        """Test buy links generation when product not found."""
        # Mock product service to return None
        commerce_service.product_service = AsyncMock()
        commerce_service.product_service.get_by_barcode.return_value = None
        
        with pytest.raises(ValueError, match="Product with barcode 9999999999999 not found"):
            await commerce_service.generate_buy_links("9999999999999")
    
    @pytest.mark.asyncio
    async def test_generate_buy_links_invalid_platforms(self, commerce_service, mock_product, mock_db):
        """Test buy links generation with invalid platforms."""
        # Mock product service
        commerce_service.product_service = AsyncMock()
        commerce_service.product_service.get_by_barcode.return_value = mock_product
        
        with pytest.raises(ValueError, match="No valid platforms specified"):
            await commerce_service.generate_buy_links(
                "8901234567890", 
                platforms=["invalid_platform"]
            )
    
    @pytest.mark.asyncio
    async def test_generate_buy_links_empty_platforms(self, commerce_service, mock_product, mock_db):
        """Test buy links generation with empty platforms list."""
        # Mock product service
        commerce_service.product_service = AsyncMock()
        commerce_service.product_service.get_by_barcode.return_value = mock_product
        
        with pytest.raises(ValueError, match="No valid platforms specified"):
            await commerce_service.generate_buy_links(
                "8901234567890", 
                platforms=[]
            )
    
    def test_url_encoding_edge_cases(self, commerce_service):
        """Test URL encoding for edge cases."""
        config = CommerceLinkService.PLATFORM_CONFIGS["blinkit"]
        
        # Test special characters
        search_query = "cadbury+5+star+chocolate"
        link_data = commerce_service._generate_platform_link(config, search_query)
        
        assert "cadbury+5+star+chocolate" in link_data["deep_link"]
        assert "cadbury+5+star+chocolate" in link_data["fallback_url"]
        
        # Test spaces are properly encoded
        search_query = "parle+g+biscuits"
        link_data = commerce_service._generate_platform_link(config, search_query)
        
        assert "parle+g+biscuits" in link_data["deep_link"]
        assert "parle+g+biscuits" in link_data["fallback_url"]
    
    def test_text_cleaning_edge_cases(self, commerce_service):
        """Test text cleaning edge cases."""
        # Test with numbers and units
        assert commerce_service._clean_text("Pack of 6 x 25g") == ""
        assert commerce_service._clean_text("1kg Pack") == ""
        
        # Test with mixed case and special chars
        assert commerce_service._clean_text("FRESH & BEST! (New)") == "Fresh Best"
        
        # Test with very short words
        assert commerce_service._clean_text("A B C D") == ""
        assert commerce_service._clean_text("AB CD EF") == "Ab Cd Ef"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
