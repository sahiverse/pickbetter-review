from .database import Base
from .models import Product, NormalizedNutrition  # Add all your models here

# This ensures SQLAlchemy can discover all models
__all__ = ['Base', 'Product', 'NormalizedNutrition']