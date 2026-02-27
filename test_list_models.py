from app.config import get_settings
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"ERROR: {e}")
