"""
API endpoints for user data contribution.
Handles product contributions when barcode is not found in database.
"""

import base64
import json
from datetime import datetime
from typing import Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product, ProductResponse, NormalizedNutrition
from app.config import get_settings

router = APIRouter(prefix="/contribute", tags=["contribution"])


@router.post("/", response_model=dict)
async def contribute_product(
    barcode: str = Form(...),
    nutrition_image: UploadFile = File(...),
    ingredients_image: Optional[UploadFile] = File(None),
    product_name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Contribute a new product by uploading nutrition and ingredients images.
    Gemini Vision analyzes the images and returns a full product health profile.
    """
    settings = get_settings()
    try:
        # Read image bytes
        nutrition_bytes = await nutrition_image.read()
        nutrition_b64 = base64.b64encode(nutrition_bytes).decode('utf-8')

        ingredients_b64 = None
        if ingredients_image:
            ingredients_bytes = await ingredients_image.read()
            ingredients_b64 = base64.b64encode(ingredients_bytes).decode('utf-8')

        # Build Gemini Vision prompt parts
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')

        parts = []

        prompt_text = f"""You are a professional nutritionist AI. A user has submitted photos of a food product that is NOT in any database.

Product barcode: {barcode}
{f'Product name hint: {product_name}' if product_name else ''}
{f'Brand hint: {brand}' if brand else ''}

The attached image(s) show the nutrition label{' and ingredients list' if ingredients_b64 else ''} of this product.

Please:
1. Read ALL nutrition values from the nutrition label image carefully.
2. Read the ingredients list if provided.
3. Assign a health grade (A/B/C/D/F) and score (0-100) based on the nutritional profile.

Return ONLY a valid JSON object in this exact format:
{{
  "original_product": {{
    "product_name": "extracted or guessed product name",
    "brands": "brand name if visible or provided",
    "ingredients_text": "full ingredients text extracted from image, or empty string",
    "nutriments": {{
      "energy-kcal_100g": number or null,
      "proteins_100g": number or null,
      "carbohydrates_100g": number or null,
      "fat_100g": number or null,
      "sugars_100g": number or null,
      "fiber_100g": number or null,
      "sodium_100g": number or null
    }},
    "image_url": null,
    "code": "{barcode}"
  }},
  "gemini_analysis": {{
    "grade": "A/B/C/D/F",
    "score": 0-100,
    "reasoning": "detailed explanation of the health grade",
    "health_concerns": ["list", "of", "concerns"],
    "positive_aspects": ["list", "of", "positives"]
  }},
  "recommendations": [],
  "message": "AI Analyzed from User Contribution"
}}

Be accurate when reading the nutrition label. If a value is not visible, use null."""

        parts.append(prompt_text)
        parts.append({
            "mime_type": nutrition_image.content_type or "image/jpeg",
            "data": nutrition_b64
        })

        if ingredients_b64:
            parts.append({
                "mime_type": ingredients_image.content_type or "image/jpeg",
                "data": ingredients_b64
            })

        response = model.generate_content(parts)
        result_text = response.text.strip()

        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()

        gemini_result = json.loads(result_text)

        return {
            "status": "success",
            "data": gemini_result,
            "contribution": {
                "grade": gemini_result.get("gemini_analysis", {}).get("grade", "C"),
                "score": gemini_result.get("gemini_analysis", {}).get("score", 50),
            },
            "message": "Thank you for your contribution! 🎉",
            "friendly_message": f"Great job! 🌟 We've analyzed your product photos and assigned a health grade of {gemini_result.get('gemini_analysis', {}).get('grade', 'C')} ({gemini_result.get('gemini_analysis', {}).get('score', 50)}/100)."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process contribution: {str(e)}"
        )



@router.get("/pending", response_model=dict)
async def get_pending_contributions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending contributions (for admin use).
    
    Args:
        limit: Maximum number of pending contributions to return
        db: Database session
        
    Returns:
        List of pending contributions
    """
    try:
        result = await db.execute(
            select(Product)
            .where(Product.pending_verification == True)
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        pending = result.scalars().all()
        
        return {
            "count": len(pending),
            "pending_contributions": [
                {
                    "id": p.id,
                    "barcode": p.barcode,
                    "name": p.name,
                    "brand": p.brand,
                    "grade": p.health_grade,
                    "score": p.health_score,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "data_completeness": _calculate_data_completeness(p.nutriments)
                }
                for p in pending
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending contributions: {str(e)}"
        )


@router.post("/verify/{product_id}", response_model=dict)
async def verify_contribution(
    product_id: int,
    approved: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify (approve/reject) a pending contribution (admin only).
    
    Args:
        product_id: Product ID to verify
        approved: True to approve, False to reject
        db: Database session
        
    Returns:
        Verification result
    """
    try:
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if not product.pending_verification:
            return {
                "status": "already_verified",
                "message": "This contribution has already been verified.",
                "product": {
                    "id": product.id,
                    "barcode": product.barcode,
                    "verified": product.verified,
                    "pending_verification": product.pending_verification
                }
            }
        
        if approved:
            product.verified = True
            product.pending_verification = False
            await db.commit()
            
            return {
                "status": "approved",
                "message": f"Contribution for {product.name} has been approved! 🎉",
                "product": {
                    "id": product.id,
                    "barcode": product.barcode,
                    "name": product.name,
                    "grade": product.health_grade,
                    "score": product.health_score,
                    "verified": True
                }
            }
        else:
            # Reject - delete the product
            await db.delete(product)
            await db.commit()
            
            return {
                "status": "rejected",
                "message": "Contribution has been rejected and removed."
            }
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify contribution: {str(e)}"
        )


def _calculate_data_completeness(nutriments: Optional[dict]) -> float:
    """Calculate data completeness percentage."""
    if not nutriments:
        return 0.0
    
    mandatory_fields = [
        "energy-kcal_100g",
        "proteins_100g",
        "carbohydrates_100g",
        "fat_100g",
        "sugars_100g",
        "saturated-fat_100g",
        "sodium_100g"
    ]
    
    present = sum(1 for field in mandatory_fields if field in nutriments and nutriments[field] is not None)
    return (present / len(mandatory_fields)) * 100
