import asyncio
from app.services.gemini_service import gemini_service
import json

try:
    res = gemini_service.synthesize_product_from_barcode("899999995555544444")
    print(json.dumps(res, indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
