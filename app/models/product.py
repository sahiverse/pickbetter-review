from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, JSON, Text, String, Integer, Float, DateTime, ForeignKey, Index, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field as SQLField, Relationship

if TYPE_CHECKING:
    from app.models.scan_history import ScanHistory
    from app.models.product_contribution import ProductContribution
    from app.models.user_favorite import UserFavorite

class TimestampModel(SQLModel):
    """Base model with timestamp fields."""
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=datetime.utcnow, nullable=False)
    )

class ProductBase(SQLModel):
    barcode: str = SQLField(
        ...,
        max_length=13,
        min_length=8,
        regex=r"^\d{8,13}$",
        sa_column=Column(String(13), unique=True, index=True, nullable=False)
    )
    name: str = SQLField(..., max_length=200, sa_column=Column(String(200), nullable=False))
    brand: Optional[str] = SQLField(default=None, max_length=100, sa_column=Column(String(100)))
    category: Optional[str] = SQLField(default=None, max_length=100, sa_column=Column(String(100)))
    image_url: Optional[str] = SQLField(default=None, max_length=500, sa_column=Column(String(500)))
    ingredients_text: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    ingredients_list: Optional[List[Dict[str, Any]]] = SQLField(
        default=None,
        sa_column=Column(JSON)
    )
    nutriments: Optional[Dict[str, Any]] = SQLField(
        default=None,
        sa_column=Column(JSON)
    )
    nutrition_grades: Optional[str] = SQLField(default=None, max_length=1, sa_column=Column(String(1)))
    nova_group: Optional[int] = SQLField(default=None, ge=1, le=4, sa_column=Column(Integer))
    ecoscore_grade: Optional[str] = SQLField(default=None, max_length=1, sa_column=Column(String(1)))
    last_modified: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Indian Health Score fields
    health_score: Optional[int] = SQLField(default=None, ge=0, le=100, sa_column=Column(Integer))
    health_grade: Optional[str] = SQLField(default=None, max_length=1, sa_column=Column(String(1)))
    score_last_calculated: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Data Contribution fields
    verification_status: str = SQLField(default="verified", max_length=20, sa_column=Column(String(20), default="verified", nullable=False))
    source: Optional[str] = SQLField(default="openfoodfacts", max_length=50, sa_column=Column(String(50)))

class Product(ProductBase, TimestampModel, table=True):
    """Product model with all fields including health scores."""
    
    __tablename__ = "products"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    
    # Soft delete support
    deleted_at: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    
    # Relationships
    normalized_nutrition: Optional["NormalizedNutrition"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"uselist": False}  # One-to-one relationship
    )
    scan_history: List["ScanHistory"] = Relationship(back_populates="product")
    contributions: List["ProductContribution"] = Relationship(back_populates="product")
    favorites: List["UserFavorite"] = Relationship(back_populates="product")

class NormalizedNutritionBase(SQLModel):
    product_id: Optional[int] = SQLField(
        default=None,
        foreign_key="products.id"
    )
    calories_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    protein_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    carbohydrates_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    sugars_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    fat_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    saturated_fat_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    trans_fat_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    fiber_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    added_sugar_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    sodium_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    salt_100g: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    fvnl_percent: Optional[float] = SQLField(default=0.0, ge=0, le=100, sa_column=Column(Float, default=0.0))
    serving_size: Optional[str] = SQLField(default=None, max_length=50, sa_column=Column(String(50)))
    serving_quantity: Optional[float] = SQLField(default=None, ge=0, sa_column=Column(Float))
    nutrition_score_fr_100g: Optional[int] = SQLField(default=None, sa_column=Column(Integer))
    nutrition_score_fr: Optional[int] = SQLField(default=None, sa_column=Column(Integer))
    general_health_score: Optional[int] = SQLField(default=None, sa_column=Column(Integer))
    nutri_grade: Optional[str] = SQLField(default=None, max_length=1, sa_column=Column(String(1)))

class NormalizedNutrition(NormalizedNutritionBase, table=True):
    __tablename__ = "normalized_nutrition"
    
    # Override the product_id to make it required and set as primary key
    product_id: int = SQLField(
        default=None,
        foreign_key="products.id",
        primary_key=True
    )
    
    # Relationship with Product
    product: "Product" = Relationship(back_populates="normalized_nutrition")

# Pydantic models for request/response
class ProductCreate(ProductBase):
    normalized_nutrition: Optional[NormalizedNutritionBase] = None

class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ProductUpdate(SQLModel):
    """Model for updating product information."""
    name: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    ingredients_text: Optional[str] = None
    ingredients_list: Optional[List[Dict[str, Any]]] = None
    nutriments: Optional[Dict[str, Any]] = None
    nutrition_grades: Optional[str] = Field(None, max_length=1)
    nova_group: Optional[int] = Field(None, ge=1, le=4)
    ecoscore_grade: Optional[str] = Field(None, max_length=1)
    last_modified: Optional[datetime] = None

class NormalizedNutritionCreate(NormalizedNutritionBase):
    pass

class NormalizedNutritionRead(NormalizedNutritionBase):
    product_id: int
    created_at: datetime
    updated_at: datetime

class ProductResponse(ProductRead):
    """Response model for product with normalized nutrition data."""
    normalized_nutrition: Optional[NormalizedNutritionRead] = None

class ProductListResponse(SQLModel):
    """Response model for product list with pagination."""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
