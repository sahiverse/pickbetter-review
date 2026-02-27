from app.config import get_settings
from dotenv import load_dotenv

load_dotenv()
settings = get_settings()
print(f"Key loaded from config: '{settings.GEMINI_API_KEY}'")
print(f"Length: {len(settings.GEMINI_API_KEY)}")
