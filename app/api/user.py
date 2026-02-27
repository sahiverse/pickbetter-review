"""
API endpoints for user profile management.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileUpdate, UserProfileResponse

router = APIRouter(prefix="/user", tags=["user"])


def _convert_lists_to_json(profile_data):
    """Convert list fields to JSON strings for database storage."""
    data = profile_data.dict(exclude_unset=True)
    for field in ['allergens', 'health_conditions', 'custom_needs']:
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])
    return data


def _convert_json_to_lists(profile):
    """Convert JSON string fields back to lists for API response."""
    if hasattr(profile, 'allergens') and profile.allergens:
        profile.allergens = json.loads(profile.allergens)
    else:
        profile.allergens = []
        
    if hasattr(profile, 'health_conditions') and profile.health_conditions:
        profile.health_conditions = json.loads(profile.health_conditions)
    else:
        profile.health_conditions = []
        
    if hasattr(profile, 'custom_needs') and profile.custom_needs:
        profile.custom_needs = json.loads(profile.custom_needs)
    else:
        profile.custom_needs = []
    
    return profile


@router.post("/profile", response_model=UserProfileResponse)
async def create_or_update_profile(
    profile_data: UserProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update a user profile.

    If a profile exists for the user_id, it will be updated.
    If not, a new profile will be created.

    Args:
        profile_data: User profile data
        db: Database session

    Returns:
        Created or updated user profile
    """
    try:
        # Check if profile exists
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == profile_data.user_id)
        )
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            # Update existing profile with JSON conversion
            update_data = _convert_lists_to_json(profile_data)
            for field, value in update_data.items():
                if field != 'user_id':  # Don't update user_id
                    setattr(existing_profile, field, value)

            # Handle custom_needs logic
            if profile_data.custom_needs:
                # If custom_needs is provided, set status to pending for review
                existing_profile.custom_needs_status = 'pending'
                print(f"📝 Custom needs noted for user {profile_data.user_id}: {profile_data.custom_needs}")

            await db.commit()
            await db.refresh(existing_profile)
            return UserProfileResponse.from_orm(_convert_json_to_lists(existing_profile))
        else:
            # Create new profile with JSON conversion
            profile_dict = _convert_lists_to_json(profile_data)
            new_profile = UserProfile(**profile_dict)

            # Handle custom_needs logic for new profiles
            if profile_data.custom_needs:
                new_profile.custom_needs_status = 'pending'
                print(f"📝 Custom needs noted for new user {profile_data.user_id}: {profile_data.custom_needs}")

            db.add(new_profile)
            await db.commit()
            await db.refresh(new_profile)
            return UserProfileResponse.from_orm(_convert_json_to_lists(new_profile))

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a user profile by user_id.

    Args:
        user_id: Unique user identifier
        db: Database session

    Returns:
        User profile data
    """
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        return UserProfileResponse.from_orm(_convert_json_to_lists(profile))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.patch("/profile/{user_id}", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user profile.

    Args:
        user_id: Unique user identifier
        profile_update: Updated profile data
        db: Database session

    Returns:
        Updated user profile
    """
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        # Update fields with JSON conversion
        update_data = _convert_lists_to_json(profile_update)
        for field, value in update_data.items():
            if value is not None:
                setattr(profile, field, value)

        # Handle custom_needs logic
        if profile_update.custom_needs is not None:
            profile.custom_needs_status = 'pending'
            print(f"📝 Custom needs updated for user {user_id}: {profile_update.custom_needs}")

        profile.updated_at = profile.updated_at  # Will be updated by SQLAlchemy

        await db.commit()
        await db.refresh(profile)
        return UserProfileResponse.from_orm(_convert_json_to_lists(profile))

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/profile/{user_id}")
async def delete_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user profile.

    Args:
        user_id: Unique user identifier
        db: Database session

    Returns:
        Success message
    """
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        await db.delete(profile)
        await db.commit()

        return {"message": f"Profile for user {user_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )
