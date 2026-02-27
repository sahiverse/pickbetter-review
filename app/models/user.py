from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import SQLModel, Field

Base = declarative_base()


class UserProfile(SQLModel, table=True):
    """
    User profile model for storing user health and safety preferences.
    """
    __tablename__ = "user_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(
        ...,
        max_length=100,
        sa_column=Column(String(100), unique=True, nullable=False),
        description="Unique user identifier"
    )

    # Basic Information
    name: str = Field(..., max_length=200, sa_column=Column(String(200), nullable=False), description="User's full name")
    age: Optional[int] = Field(default=None, description="User's age")
    sex: Optional[str] = Field(default=None, max_length=20, sa_column=Column(String(20)), description="User's sex (Male/Female/Other)")
    height: Optional[int] = Field(default=None, description="Height in cm")
    weight: Optional[int] = Field(default=None, description="Weight in kg")

    # Safety & Health Parameters - Use JSONB for PostgreSQL, JSON for SQLite
    allergens: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Array of allergens"
    )
    health_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Array of health conditions"
    )

    # Custom Needs (for 'Others' input)
    custom_needs: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Custom requirements"
    )
    custom_needs_status: str = Field(
        default="pending",
        max_length=20,
        sa_column=Column(String(20), default="pending", nullable=False),
        description="Status of custom needs processing (pending/reviewed/implemented)"
    )

    # Lifestyle
    dietary_preference: Optional[str] = Field(
        default="General",
        max_length=50,
        sa_column=Column(String(50), default="General"),
        description="User's dietary preference"
    )
    primary_goal: Optional[str] = Field(
        default="General Wellness",
        max_length=100,
        sa_column=Column(String(100), default="General Wellness"),
        description="User's primary health goal"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    
    # Soft delete support
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    
    __table_args__ = (
        Index('idx_user_profiles_user_id', 'user_id'),
    )
