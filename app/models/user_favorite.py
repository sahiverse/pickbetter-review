"""User Favorites model for bookmarked products."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class UserFavoriteBase(SQLModel):
    """Base model for user favorites."""
    user_id: str = Field(
        ...,
        max_length=100,
        sa_column=Column(String(100), nullable=False),
        description="User who favorited the product"
    )
    product_id: int = Field(
        ...,
        foreign_key="products.id",
        description="Favorited product"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        description="When product was favorited"
    )


class UserFavorite(UserFavoriteBase, table=True):
    """User favorite model with relationships."""
    __tablename__ = "user_favorites"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship with Product
    product: Optional["Product"] = Relationship(back_populates="favorites")
    
    __table_args__ = (
        Index('idx_favorites_user_id', 'user_id'),
        Index('idx_favorites_product_id', 'product_id'),
        UniqueConstraint('user_id', 'product_id', name='uq_user_product_favorite'),
    )


class UserFavoriteCreate(UserFavoriteBase):
    """Model for creating user favorite."""
    pass


class UserFavoriteRead(UserFavoriteBase):
    """Model for reading user favorite."""
    id: int


class UserFavoriteDelete(SQLModel):
    """Model for deleting user favorite."""
    user_id: str
    product_id: int
