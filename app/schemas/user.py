"""
Pydantic schemas for user profile validation and serialization.
"""

from datetime import datetime
from typing import List, Optional
import json
from pydantic import BaseModel, Field, validator


class UserProfileBase(BaseModel):
    """Base schema for UserProfile."""
    user_id: str = Field(..., description="Unique user identifier")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    age: Optional[int] = Field(None, ge=1, le=150, description="User's age")
    sex: Optional[str] = Field(None, description="User's sex (Male/Female/Other)")
    height: Optional[int] = Field(None, ge=50, le=300, description="Height in cm")
    weight: Optional[int] = Field(None, ge=10, le=500, description="Weight in kg")

    # Safety & Health Parameters
    allergens: List[str] = Field(default_factory=list, description="List of allergens the user has")
    health_conditions: List[str] = Field(default_factory=list, description="List of health conditions the user has")

    # Custom Needs (for 'Others' input)
    custom_needs: List[str] = Field(default_factory=list, description="List of custom health/safety requirements")
    custom_needs_status: str = Field(default="pending", description="Status of custom needs processing")

    # Lifestyle
    dietary_preference: Optional[str] = Field("General", description="User's dietary preference")
    primary_goal: Optional[str] = Field("General Wellness", description="User's primary health goal")

    @validator('sex')
    def validate_sex(cls, v):
        if v is not None and v not in ['Male', 'Female', 'Other']:
            raise ValueError('sex must be Male, Female, or Other')
        return v

    @validator('custom_needs_status')
    def validate_custom_needs_status(cls, v):
        if v not in ['pending', 'reviewed', 'implemented']:
            raise ValueError('custom_needs_status must be pending, reviewed, or implemented')
        return v

    class Config:
        json_encoders = {
            List[str]: lambda v: json.dumps(v) if v else None
        }
        from_attributes = True


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile."""
    pass


class UserProfileUpdate(BaseModel):
    """Schema for updating an existing user profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=150)
    sex: Optional[str] = Field(None)
    height: Optional[int] = Field(None, ge=50, le=300)
    weight: Optional[int] = Field(None, ge=10, le=500)
    allergens: Optional[List[str]] = Field(None)
    health_conditions: Optional[List[str]] = Field(None)
    custom_needs: Optional[List[str]] = Field(None)
    custom_needs_status: Optional[str] = Field(None)
    dietary_preference: Optional[str] = Field(None)
    primary_goal: Optional[str] = Field(None)

    @validator('sex')
    def validate_sex(cls, v):
        if v is not None and v not in ['Male', 'Female', 'Other']:
            raise ValueError('sex must be Male, Female, or Other')
        return v

    @validator('custom_needs_status')
    def validate_custom_needs_status(cls, v):
        if v not in ['pending', 'reviewed', 'implemented']:
            raise ValueError('custom_needs_status must be pending, reviewed, or implemented')
        return v


class UserProfileResponse(UserProfileBase):
    """Schema for user profile API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
