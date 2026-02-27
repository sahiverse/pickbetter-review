"""Chat API for Vitalis AI interactions."""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.gemini_service import gemini_service
from app.services.firebase_auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_profile: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

@router.post("/")
async def chat_with_vitalis(
    request: ChatRequest,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> ChatResponse:
    """
    Chat with Vitalis AI assistant.

    Args:
        request: Chat messages and user profile
        user: Authenticated user info (optional)

    Returns:
        AI response
    """
    try:
        logger.info(f"Chat request from user: {user.get('user_id') if user else 'anonymous'}")

        # Convert Pydantic models to dicts for the service
        messages = [msg.dict() for msg in request.messages]

        # Use user profile from request or authenticated user
        user_profile = request.user_profile
        if not user_profile and user:
            # Extract relevant user info for the AI
            user_profile = {
                "user_id": user.get("user_id"),
                "conditions": user.get("conditions", []),
                "allergens": user.get("allergens", []),
                "dietary_preference": user.get("dietary_preference"),
                "primary_goal": user.get("primary_goal"),
                "age": user.get("age"),
                "sex": user.get("sex")
            }

        # Get AI response
        response = await gemini_service.chat_completion(messages, user_profile)

        return ChatResponse(response=response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Unable to process chat request. Please try again."
        )
