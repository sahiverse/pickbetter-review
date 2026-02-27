"""Product Contribution model for user-submitted product data."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, JSON, Text
from sqlmodel import SQLModel, Field, Relationship


class ProductContributionBase(SQLModel):
    """Base model for product contributions."""
    product_id: Optional[int] = Field(
        default=None,
        foreign_key="products.id",
        description="Linked product (NULL if new product)"
    )
    contributor_user_id: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column(String(100)),
        description="User who submitted the contribution"
    )
    contribution_type: str = Field(
        ...,
        max_length=50,
        sa_column=Column(String(50), nullable=False),
        description="Type: create, update, verify, report_error"
    )
    barcode: str = Field(
        ...,
        max_length=13,
        sa_column=Column(String(13), nullable=False),
        description="Product barcode"
    )
    nutrition_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        sa_column=Column(String(500)),
        description="URL to uploaded nutrition label image"
    )
    ingredients_image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        sa_column=Column(String(500)),
        description="URL to uploaded ingredients image"
    )
    ocr_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Extracted OCR data from images"
    )
    status: str = Field(
        default="pending",
        max_length=20,
        sa_column=Column(String(20), default="pending", nullable=False),
        description="Status: pending, approved, rejected"
    )
    reviewed_by: Optional[str] = Field(
        default=None,
        max_length=100,
        sa_column=Column(String(100)),
        description="Admin/moderator who reviewed"
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="When the review occurred"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        description="Contribution submission timestamp"
    )


class ProductContribution(ProductContributionBase, table=True):
    """Product contribution model with relationships."""
    __tablename__ = "product_contributions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship with Product
    product: Optional["Product"] = Relationship(back_populates="contributions")
    
    __table_args__ = (
        Index('idx_contributions_status', 'status'),
        Index('idx_contributions_barcode', 'barcode'),
        Index('idx_contributions_contributor', 'contributor_user_id'),
        Index('idx_contributions_created_at', 'created_at'),
    )


class ProductContributionCreate(ProductContributionBase):
    """Model for creating product contribution."""
    pass


class ProductContributionRead(ProductContributionBase):
    """Model for reading product contribution."""
    id: int


class ProductContributionUpdate(SQLModel):
    """Model for updating product contribution."""
    status: Optional[str] = Field(None, max_length=20)
    reviewed_by: Optional[str] = Field(None, max_length=100)
    reviewed_at: Optional[datetime] = None
    ocr_data: Optional[Dict[str, Any]] = None
