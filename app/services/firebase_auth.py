"""Firebase authentication service for PickBetter."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

# Guest user configuration
GUEST_USER_ID = "guest_user"
GUEST_USER_EMAIL = "guest@pickbetter.app"
GUEST_TOKEN_SECRET = "your-secret-key-for-guest-tokens"  # Should be in .env
GUEST_TOKEN_EXPIRY_HOURS = 24


class FirebaseAuthService:
    """Service for Firebase authentication."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return
        
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Initialize Firebase with credentials
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully")
            except Exception as e:
                logger.warning(f"Firebase initialization failed: {e}. Guest mode will still work.")
        
        cls._initialized = True
    
    @staticmethod
    def verify_firebase_token(token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token.
        
        Args:
            token: Firebase ID token
            
        Returns:
            Decoded token with user information
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            decoded_token = auth.verify_id_token(token)
            return {
                "user_id": decoded_token['uid'],
                "email": decoded_token.get('email'),
                "email_verified": decoded_token.get('email_verified', False),
                "name": decoded_token.get('name'),
                "picture": decoded_token.get('picture'),
                "is_guest": False
            }
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    @staticmethod
    def create_guest_token() -> str:
        """
        Create a JWT token for guest users.
        
        Returns:
            JWT token string
        """
        expiry = datetime.utcnow() + timedelta(hours=GUEST_TOKEN_EXPIRY_HOURS)
        payload = {
            "user_id": GUEST_USER_ID,
            "email": GUEST_USER_EMAIL,
            "is_guest": True,
            "exp": expiry,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, GUEST_TOKEN_SECRET, algorithm="HS256")
        return token
    
    @staticmethod
    def verify_guest_token(token: str) -> Dict[str, Any]:
        """
        Verify guest JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token with user information
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, GUEST_TOKEN_SECRET, algorithms=["HS256"])
            return {
                "user_id": payload["user_id"],
                "email": payload.get("email"),
                "is_guest": payload.get("is_guest", True),
                "email_verified": False,
                "name": "Guest User",
                "picture": None
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Guest session expired. Please start a new guest session."
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Guest token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid guest token"
            )


# Dependency for optional authentication (allows guest users)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from token (optional - returns None if no token).
    
    This allows endpoints to work for both authenticated and unauthenticated users.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dict or None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Try Firebase token first
    try:
        FirebaseAuthService.initialize()
        return FirebaseAuthService.verify_firebase_token(token)
    except HTTPException:
        # If Firebase fails, try guest token
        try:
            return FirebaseAuthService.verify_guest_token(token)
        except HTTPException:
            return None


# Dependency for required authentication (rejects unauthenticated requests)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from token (required).
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If no valid token provided
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    
    # Try Firebase token first
    try:
        FirebaseAuthService.initialize()
        return FirebaseAuthService.verify_firebase_token(token)
    except HTTPException:
        # If Firebase fails, try guest token
        return FirebaseAuthService.verify_guest_token(token)


# Dependency that requires authenticated user (no guests)
async def get_authenticated_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get authenticated user (no guest users allowed).
    
    Args:
        user: User information from token
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If user is a guest
    """
    if user.get("is_guest", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a registered account. Please sign up or log in."
        )
    
    return user
