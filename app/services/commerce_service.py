"""
Commerce Link Service for PickBetter
Generates deep links for quick-commerce platforms without scraping
"""

import urllib.parse
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.product_service import ProductService


class CommerceLinkService:
    """Service for generating commerce platform deep links."""
    
    # Platform configurations
    PLATFORM_CONFIGS = {
        "blinkit": {
            "name": "Blinkit",
            "app_scheme": "blinkit://search",
            "web_url": "https://blinkit.com/s/",
            "query_param": "q"
        },
        "zepto": {
            "name": "Zepto",
            "app_scheme": "zepto://search",
            "web_url": "https://www.zeptonow.com/search",
            "query_param": "query"
        },
        "instamart": {
            "name": "Instamart",
            "app_scheme": "swiggy://instamart/search",
            "web_url": "https://www.swiggy.com/instamart/search",
            "query_param": "query"
        }
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize commerce link service."""
        self.db = db
        self.product_service = ProductService(db)
    
    async def generate_buy_links(self, barcode: str, platforms: Optional[List[str]] = None) -> Dict:
        """
        Generate buy links for a product across specified platforms.
        
        Args:
            barcode: Product barcode
            platforms: List of platforms (default: all platforms)
            
        Returns:
            Dictionary with product info and platform links
        """
        # Fetch product from database
        product = await self.product_service.get_by_barcode(barcode)
        if not product:
            raise ValueError(f"Product with barcode {barcode} not found")
        
        # Default to all platforms if none specified
        if platforms is None:
            platforms = list(self.PLATFORM_CONFIGS.keys())
        
        # Validate platforms
        valid_platforms = [p for p in platforms if p in self.PLATFORM_CONFIGS]
        if not valid_platforms:
            raise ValueError("No valid platforms specified")
        
        # Generate search query
        search_query = self._build_search_query(product)
        
        # Generate links for each platform
        links = []
        for platform in valid_platforms:
            config = self.PLATFORM_CONFIGS[platform]
            link_data = self._generate_platform_link(config, search_query)
            links.append(link_data)
        
        return {
            "product": {
                "barcode": product.barcode,
                "name": product.name,
                "brand": product.brand,
                "category": product.category
            },
            "links": links
        }
    
    def _build_search_query(self, product) -> str:
        """
        Build a clean search query from product information.
        
        Args:
            product: Product model instance
            
        Returns:
            URL-encoded search query string
        """
        # Start with brand and name
        query_parts = []
        
        if product.brand:
            # Clean brand name
            brand = self._clean_text(product.brand)
            if brand:
                query_parts.append(brand)
        
        if product.name:
            # Clean product name
            name = self._clean_text(product.name)
            if name:
                query_parts.append(name)
        
        # If no brand/name, use category as fallback
        if not query_parts and product.category:
            category = self._clean_text(product.category)
            if category:
                query_parts.append(category)
        
        # Join parts and encode
        search_query = " ".join(query_parts)
        return urllib.parse.quote_plus(search_query)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for search query.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove common unwanted characters and patterns
        import re
        
        # Remove special characters except spaces and hyphens
        text = re.sub(r'[^\w\s\-]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common marketing terms that don't help search
        marketing_terms = [
            'pack of', 'pack', 'pcs', 'pieces', 'grams', 'g', 'kg', 'ltr', 'l',
            'ml', 'premium', 'special', 'offer', 'deal',
            'of', 'x', 'size', 'unit', 'units', 'new'
        ]
        
        words = text.lower().split()
        filtered_words = [
            word for word in words 
            if (word not in marketing_terms and 
                len(word) > 1 and 
                not word.isdigit() and
                not word.replace('g', '').isdigit() and
                not word.replace('ml', '').isdigit() and
                not word.replace('l', '').isdigit() and
                not word.replace('kg', '').isdigit())
        ]
        
        # Return cleaned text (preserve original case for better search)
        return ' '.join(filtered_words).title()
    
    def _generate_platform_link(self, config: Dict, search_query: str) -> Dict:
        """
        Generate deep link and fallback URL for a platform.
        
        Args:
            config: Platform configuration
            search_query: URL-encoded search query
            
        Returns:
            Dictionary with platform link information
        """
        # Build deep link
        deep_link = f"{config['app_scheme']}?{config['query_param']}={search_query}"
        
        # Build fallback web URL
        fallback_url = f"{config['web_url']}?{config['query_param']}={search_query}"
        
        return {
            "platform": config["name"],
            "platform_key": config["name"].lower(),
            "deep_link": deep_link,
            "fallback_url": fallback_url
        }
    
    def get_supported_platforms(self) -> List[Dict]:
        """
        Get list of supported platforms.
        
        Returns:
            List of platform information
        """
        return [
            {
                "key": key,
                "name": config["name"],
                "app_scheme": config["app_scheme"],
                "web_url": config["web_url"]
            }
            for key, config in self.PLATFORM_CONFIGS.items()
        ]


# Convenience function for dependency injection
async def get_commerce_links(
    barcode: str,
    platforms: Optional[List[str]] = None,
    db: AsyncSession = None
) -> Dict:
    """
    Convenience function for getting commerce links.
    
    Args:
        barcode: Product barcode
        platforms: List of platforms (default: all platforms)
        db: Database session
        
    Returns:
        Dictionary with product info and platform links
    """
    if not db:
        raise ValueError("Database session is required")
    
    service = CommerceLinkService(db)
    return await service.generate_buy_links(barcode, platforms)
