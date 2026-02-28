from functools import lru_cache
from typing import Optional
import os

from pydantic import validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api/v1"
    
    # Supabase (Optional if DATABASE_URL is provided)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Open Food Facts
    OPENFOODFACTS_API_URL: str = "https://world.openfoodfacts.org/api/v2"
    
    # DeepSeek AI
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    # Gemini AI
    GEMINI_API_KEY: str
    
    # Caching
    PRODUCT_CACHE_DAYS: int = 30
    
    # Database - PostgreSQL only
    DATABASE_URL: str
    
    # Firebase Authentication
    FIREBASE_CREDENTIALS_PATH: str = "credentials/firebase-credentials.json"
    GUEST_TOKEN_SECRET: str = "change-this-secret-key-in-production"
    
    @validator("DATABASE_URL", pre=True)
    def validate_postgresql_url(cls, v: str, values: dict) -> str:
        """Validate that DATABASE_URL is PostgreSQL."""
        if not v:
            # Default to Supabase PostgreSQL
            supabase_url = values.get('SUPABASE_URL', '').replace('https://', '')
            service_key = values.get('SUPABASE_SERVICE_KEY', '')
            return f"postgresql://postgres:{service_key}@{supabase_url}/postgres"
        
        # Ensure it's PostgreSQL
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string (postgresql://...)")
        
        return v
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return Settings()