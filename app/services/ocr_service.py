"""
OCR Service for extracting text from nutrition and ingredients images.
Uses OpenCV for preprocessing and Google Cloud Vision API for text extraction.
"""

import io
import re
# Try to import PIL, fallback if not available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: PIL not available - image handling disabled")
    # Create dummy Image class for compatibility
    class DummyImage:
        def __getattr__(self, name):
            def dummy_function(*args, **kwargs):
                return None
            return dummy_function
    Image = DummyImage()
from typing import Dict, Optional, List, Tuple
import logging

# Try to import OpenCV, fallback if not available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("WARNING: OpenCV not available - OCR preprocessing disabled")
    # Create dummy cv2 and np modules for compatibility
    class DummyCV2:
        def __getattr__(self, name):
            def dummy_function(*args, **kwargs):
                return None
            return dummy_function
    cv2 = DummyCV2()
    
    class DummyNP:
        def __getattr__(self, name):
            def dummy_function(*args, **kwargs):
                return None
            return dummy_function
    np = DummyNP()

logger = logging.getLogger(__name__)

# Try to import Google Cloud Vision, fallback to mock if not available
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    logger.warning("Google Cloud Vision not available, using fallback OCR")


class OCRService:
    """
    Service for OCR processing of nutrition and ingredients images.
    Preprocesses images with OpenCV and extracts text using Cloud Vision.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize OCR service.
        
        Args:
            credentials_path: Path to Google Cloud service account JSON (optional)
        """
        self.client = None
        if GOOGLE_VISION_AVAILABLE:
            try:
                if credentials_path:
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path
                    )
                    self.client = vision.ImageAnnotatorClient(credentials=credentials)
                else:
                    # Use default credentials
                    self.client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Cloud Vision: {e}")
                self.client = None
    
    def preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Preprocess image using OpenCV for better OCR accuracy.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed image bytes
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("Failed to decode image")
                return image_bytes
            
            # Resize if image is too large (max 2000px on longest side)
            max_size = 2000
            height, width = img.shape[:2]
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to RGB for Cloud Vision
            rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
            
            # Encode back to bytes
            _, buffer = cv2.imencode('.png', rgb)
            return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image_bytes
    
    def extract_text(self, image_bytes: bytes, preprocess: bool = True) -> str:
        """
        Extract text from image using Cloud Vision API.
        
        Args:
            image_bytes: Raw image bytes
            preprocess: Whether to preprocess image before OCR
            
        Returns:
            Extracted text
        """
        try:
            # Preprocess if enabled
            if preprocess:
                image_bytes = self.preprocess_image(image_bytes)
            
            # If Cloud Vision is available, use it
            if self.client:
                image = vision.Image(content=image_bytes)
                response = self.client.text_detection(image=image)
                
                if response.text_annotations:
                    # First annotation contains all text
                    full_text = response.text_annotations[0].description
                    return full_text
                else:
                    return ""
            else:
                # Fallback: return mock text for testing
                logger.warning("Using fallback OCR - returning empty text")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def process_nutrition_image(self, image_bytes: bytes) -> Dict[str, Optional[float]]:
        """
        Process nutrition label image and extract nutritional values.
        
        Args:
            image_bytes: Nutrition label image bytes
            
        Returns:
            Dictionary of nutritional values
        """
        # Extract text
        text = self.extract_text(image_bytes, preprocess=True)
        
        if not text:
            logger.warning("No text extracted from nutrition image")
            return {}
        
        # Parse nutritional values
        return self._parse_nutrition_text(text)
    
    def process_ingredients_image(self, image_bytes: bytes) -> str:
        """
        Process ingredients list image and extract ingredients text.
        
        Args:
            image_bytes: Ingredients image bytes
            
        Returns:
            Extracted ingredients text
        """
        text = self.extract_text(image_bytes, preprocess=True)
        return text.strip() if text else ""
    
    def _parse_nutrition_text(self, text: str) -> Dict[str, Optional[float]]:
        """
        Parse nutrition text using regex patterns to extract values.
        
        Args:
            text: Raw OCR text from nutrition label
            
        Returns:
            Dictionary of nutritional values per 100g
        """
        nutrition_data = {}
        
        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Energy patterns (kcal)
        energy_patterns = [
            r'[Ee]nergy[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:kcal|KCAL|kCal)',
            r'[Cc]alories?[\s:]*([0-9]+(?:\.[0-9]+)?)',
            r'([0-9]+(?:\.[0-9]+)?)[\s]*(?:kcal|KCAL|kCal)',
        ]
        for pattern in energy_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['energy-kcal_100g'] = float(match.group(1))
                break
        
        # Protein patterns
        protein_patterns = [
            r'[Pp]rotein[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Pp]roteins?[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in protein_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['proteins_100g'] = float(match.group(1))
                break
        
        # Carbohydrates patterns
        carb_patterns = [
            r'[Cc]arbohydrates?[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Cc]arbs?[\s:]*([0-9]+(?:\.[0-9]+)?)',
            r'[Tt]otal[\s]*[Cc]arbohydrates?[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in carb_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['carbohydrates_100g'] = float(match.group(1))
                break
        
        # Sugars patterns
        sugar_patterns = [
            r'[Ss]ugars?[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Oo]f[\s]*[Ww]hich[\s]*[Ss]ugars?[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in sugar_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['sugars_100g'] = float(match.group(1))
                break
        
        # Fat patterns
        fat_patterns = [
            r'[Ff]at[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Tt]otal[\s]*[Ff]at[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in fat_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['fat_100g'] = float(match.group(1))
                break
        
        # Saturated Fat patterns
        sat_fat_patterns = [
            r'[Ss]aturated[\s]*[Ff]at[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Ss]aturates?[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in sat_fat_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['saturated-fat_100g'] = float(match.group(1))
                break
        
        # Fiber patterns
        fiber_patterns = [
            r'[Ff]iber[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Ff]ibre[\s:]*([0-9]+(?:\.[0-9]+)?)',
            r'[Dd]ietary[\s]*[Ff]iber[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in fiber_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['fiber_100g'] = float(match.group(1))
                break
        
        # Sodium patterns (mg)
        sodium_patterns = [
            r'[Ss]odium[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:mg|MG)',
            r'[Ss]odium[\s:]*([0-9]+(?:\.[0-9]+)?)',
        ]
        for pattern in sodium_patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                # Convert mg to g if needed
                if val > 50:  # Assume >50 means it's in mg
                    val = val / 1000
                nutrition_data['sodium_100g'] = val
                break
        
        # Trans Fat patterns
        trans_fat_patterns = [
            r'[Tt]rans[\s]*[Ff]at[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Tt]rans[\s]*[Ff]atty[\s]*[Aa]cid[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Tt]rans[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
        ]
        for pattern in trans_fat_patterns:
            match = re.search(pattern, text)
            if match:
                nutrition_data['trans-fat_100g'] = float(match.group(1))
                break
        
        # Added Sugar patterns
        added_sugar_patterns = [
            r'[Aa]dded[\s]*[Ss]ugars?[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G)',
            r'[Aa]dded[\s]*[Ss]ugars?[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*%',
            r'[Ss]ugars?[\s]*[Aa]dded[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G|%)',
            r'[Ii]ncluding[\s]*[Aa]dded[\s]*[Ss]ugars?[\s:]*([0-9]+(?:\.[0-9]+)?)[\s]*(?:g|G|%)',
        ]
        for pattern in added_sugar_patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                if '%' in text[text.find(match.group(0)):text.find(match.group(0)) + 20]:  # Check if it's a percentage
                    nutrition_data['added_sugar_percent'] = val
                else:
                    nutrition_data['added_sugar_100g'] = val
                break
        
        # Calculate FVNL (Fruit, Vegetable, Nut, Legume) percentage if we have carbs and fiber
        if 'carbohydrates_100g' in nutrition_data and 'fiber_100g' in nutrition_data:
            carbs = nutrition_data['carbohydrates_100g']
            fiber = nutrition_data['fiber_100g']
            if carbs > 0:
                # FVNL% = ((carbs - fiber) / carbs) * 100
                # This estimates the percentage of carbs that are not from FVNL sources
                # Lower FVNL% means higher FVNL content (more fiber relative to carbs)
                fvnl_percent = ((carbs - fiber) / carbs) * 100
                nutrition_data['fvnl_percent'] = max(0, min(100, fvnl_percent))  # Clamp to 0-100
        
        logger.info(f"Parsed nutrition data: {nutrition_data}")
        return nutrition_data
    
    def get_data_completeness(self, nutrition_data: Dict[str, Optional[float]]) -> Tuple[float, List[str]]:
        mandatory_fields = [
            'energy-kcal_100g',
            'proteins_100g',
            'carbohydrates_100g',
            'fat_100g',
            'sugars_100g',
            'saturated-fat_100g',
            'sodium_100g'
        ]
        
        present = sum(1 for field in mandatory_fields if field in nutrition_data and nutrition_data[field] is not None)
        missing = [field for field in mandatory_fields if field not in nutrition_data or nutrition_data[field] is None]
        
        completeness = (present / len(mandatory_fields)) * 100
        
        return completeness, missing


# Global OCR service instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service(credentials_path: Optional[str] = None) -> OCRService:
    """
    Get or create global OCR service instance.
    
    Args:
        credentials_path: Path to Google Cloud credentials (optional)
        
    Returns:
        OCRService instance
    """
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(credentials_path)
    return _ocr_service
