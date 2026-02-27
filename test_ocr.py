#!/usr/bin/env python3
"""Test script to verify OCR service functionality."""

import os
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.ocr_service import get_ocr_service


async def test_ocr_service():
    """Test the OCR service with a sample image."""
    print("🔍 Testing OCR Service...")
    
    # Set Google credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/sahithivarma/PickBetter/pickbetter-487718-992f747b66e2.json"
    
    # Get OCR service
    ocr_service = get_ocr_service()
    
    # Test with a simple text image (you can replace with actual nutrition label path)
    test_image_path = "/Users/sahithivarma/PickBetter/test_nutrition_label.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"⚠️  Test image not found at: {test_image_path}")
        print("Please provide a nutrition label image to test OCR functionality")
        return False
    
    try:
        print(f"📸 Processing image: {test_image_path}")
        
        # Extract text
        extracted_text = await ocr_service.extract_text(test_image_path)
        print(f"✅ Extracted text:\n{extracted_text}")
        
        # Parse nutrition data
        nutrition_data = ocr_service.parse_nutrition_data(extracted_text)
        print(f"✅ Parsed nutrition data:\n{nutrition_data}")
        
        # Check if we got mandatory fields
        mandatory_fields = ['energy', 'sugar', 'fat', 'protein']
        missing_fields = [field for field in mandatory_fields if not nutrition_data.get(field)]
        
        if missing_fields:
            print(f"⚠️  Missing mandatory fields: {missing_fields}")
        else:
            print("✅ All mandatory nutrition fields found!")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_google_vision_availability():
    """Test if Google Vision API is accessible."""
    print("\n🔍 Testing Google Vision API availability...")
    
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        
        # Test with a simple request
        response = client.annotate_image({
            'image': {'source': {'image_uri': 'https://picsum.photos/seed/test/100/100.jpg'}},
            'features': [{'type_': vision.Feature.Type.TEXT_DETECTION}]
        })
        
        print("✅ Google Vision API is accessible")
        return True
        
    except Exception as e:
        print(f"❌ Google Vision API test failed: {str(e)}")
        return False


async def main():
    """Run all OCR tests."""
    print("=" * 60)
    print("🧪 OCR Service Test Suite")
    print("=" * 60)
    
    # Test Google Vision availability
    vision_ok = await test_google_vision_availability()
    
    # Test OCR service
    ocr_ok = await test_ocr_service()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Google Vision API: {'✅ PASS' if vision_ok else '❌ FAIL'}")
    print(f"OCR Service: {'✅ PASS' if ocr_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if vision_ok and ocr_ok:
        print("🎉 All OCR tests passed! The module is working properly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
