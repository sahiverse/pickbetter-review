"""Database models for PickBetter application."""
from app.models.base import Base
from app.models.product import (
    Product,
    ProductBase,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    NormalizedNutrition,
    NormalizedNutritionBase,
    NormalizedNutritionCreate,
    NormalizedNutritionRead,
)
from app.models.user import UserProfile
from app.models.scan_history import (
    ScanHistory,
    ScanHistoryBase,
    ScanHistoryCreate,
    ScanHistoryRead,
    ScanHistoryUpdate,
)
from app.models.product_contribution import (
    ProductContribution,
    ProductContributionBase,
    ProductContributionCreate,
    ProductContributionRead,
    ProductContributionUpdate,
)
from app.models.user_favorite import (
    UserFavorite,
    UserFavoriteBase,
    UserFavoriteCreate,
    UserFavoriteRead,
    UserFavoriteDelete,
)

__all__ = [
    # Base
    "Base",
    # Product models
    "Product",
    "ProductBase",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "NormalizedNutrition",
    "NormalizedNutritionBase",
    "NormalizedNutritionCreate",
    "NormalizedNutritionRead",
    # User models
    "UserProfile",
    # Scan history models
    "ScanHistory",
    "ScanHistoryBase",
    "ScanHistoryCreate",
    "ScanHistoryRead",
    "ScanHistoryUpdate",
    # Product contribution models
    "ProductContribution",
    "ProductContributionBase",
    "ProductContributionCreate",
    "ProductContributionRead",
    "ProductContributionUpdate",
    # User favorite models
    "UserFavorite",
    "UserFavoriteBase",
    "UserFavoriteCreate",
    "UserFavoriteRead",
    "UserFavoriteDelete",
]
