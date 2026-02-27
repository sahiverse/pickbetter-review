"""Authentication API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import UserProfile
from app.services.firebase_auth import (
    FirebaseAuthService,
    get_current_user,
    get_current_user_optional
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class GuestSessionResponse(BaseModel):
    """Response model for guest session creation."""
    token: str
    user_id: str
    is_guest: bool
    expires_in_hours: int
    message: str


class TokenVerifyRequest(BaseModel):
    """Request model for token verification."""
    token: str


class UserInfoResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    email: Optional[str]
    name: Optional[str]
    picture: Optional[str]
    is_guest: bool
    email_verified: bool


@router.post("/guest", response_model=GuestSessionResponse)
async def create_guest_session():
    """
    Create a guest session for users who want to try the app without signing up.
    
    Guest users have limited features:
    - Can scan products and view nutrition information
    - Can search and browse products
    - Cannot save favorites
    - Cannot save scan history
    - Cannot create custom user profiles
    
    Returns:
        Guest session token and information
    """
    token = FirebaseAuthService.create_guest_token()
    
    return GuestSessionResponse(
        token=token,
        user_id="guest_user",
        is_guest=True,
        expires_in_hours=24,
        message="Guest session created. Sign up to save your data and access all features!"
    )


@router.post("/verify", response_model=UserInfoResponse)
async def verify_token(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify authentication token and return user information.
    
    Automatically creates user record in PostgreSQL if it doesn't exist.
    Works for both Firebase tokens and guest tokens.
    
    Args:
        user: User information from token (injected by dependency)
        db: Database session
        
    Returns:
        User information
    """
    # Skip database operations for guest users
    if user.get("is_guest", False):
        return UserInfoResponse(
            user_id=user["user_id"],
            email=user.get("email"),
            name=user.get("name"),
            picture=user.get("picture"),
            is_guest=True,
            email_verified=user.get("email_verified", False)
        )
    
    # Check if user exists in PostgreSQL
    stmt = select(UserProfile).where(UserProfile.user_id == user["user_id"])
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    # Create user record if it doesn't exist
    if not existing_user:
        print(f"📝 Creating new user record for Firebase user: {user['user_id']}")
        new_user = UserProfile(
            user_id=user["user_id"],
            name=user.get("name", ""),
            # Note: We don't store email in user_profiles table as it's handled by Firebase
            # Email is available in the response but not stored in PostgreSQL
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(f"✅ User record created in PostgreSQL: {new_user.user_id}")
    
    return UserInfoResponse(
        user_id=user["user_id"],
        email=user.get("email"),
        name=user.get("name"),
        picture=user.get("picture"),
        is_guest=False,
        email_verified=user.get("email_verified", False)
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        user: User information from token (injected by dependency)
        
    Returns:
        User information
    """
    return UserInfoResponse(
        user_id=user["user_id"],
        email=user.get("email"),
        name=user.get("name"),
        picture=user.get("picture"),
        is_guest=user.get("is_guest", False),
        email_verified=user.get("email_verified", False)
    )


@router.post("/logout")
async def logout(
    user: dict = Depends(get_current_user_optional)
):
    """
    Logout endpoint (client should delete the token).
    
    For Firebase users, the client should call Firebase signOut().
    For guest users, the client should delete the guest token.
    
    Returns:
        Success message
    """
    if user:
        user_type = "guest" if user.get("is_guest") else "authenticated"
        return {
            "message": f"Logged out successfully",
            "user_type": user_type
        }
    
    return {"message": "No active session"}


@router.get("/status")
async def auth_status(
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Check authentication status.
    
    Returns authentication status without requiring a token.
    Useful for checking if a user is logged in.
    
    Returns:
        Authentication status
    """
    if not user:
        return {
            "authenticated": False,
            "is_guest": False,
            "message": "Not authenticated"
        }
    
    return {
        "authenticated": True,
        "is_guest": user.get("is_guest", False),
        "user_id": user["user_id"],
        "email": user.get("email"),
        "message": "Authenticated" if not user.get("is_guest") else "Guest session active"
    }
