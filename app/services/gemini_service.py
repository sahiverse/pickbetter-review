"""Gemini AI service for product analysis and health recommendations."""
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiService:
    """Service for Gemini AI product analysis and recommendations."""

    def __init__(self):
        """Initialize Gemini AI service."""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            raise

    def analyze_product_health_score(self, product_data: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze product and assign health score (A/B/C/D/F).

        Args:
            product_data: Product information from barcode scan
            user_profile: User's health profile and preferences

        Returns:
            Dict with score, grade, reasoning, and health concerns
        """
        try:
            # Extract product info
            product_name = product_data.get('product_name', 'Unknown Product')
            ingredients = product_data.get('ingredients_text', '')
            nutrients = product_data.get('nutriments', {})
            categories = product_data.get('categories', '')
            allergens = product_data.get('allergens', '')

            # Build user context
            user_context = ""
            if user_profile:
                user_context = f"""
                User Profile:
                - Allergens to avoid: {', '.join(user_profile.get('allergens', []))}
                - Health conditions: {', '.join(user_profile.get('health_conditions', []))}
                - Dietary preference: {user_profile.get('dietary_preference', 'General')}
                - Primary goal: {user_profile.get('primary_goal', 'General Wellness')}
                """

            # Create analysis prompt
            prompt = f"""
            Analyze this food product's health score on a scale of A to F (A being excellent, F being very poor).

            Product Information:
            - Name: {product_name}
            - Ingredients: {ingredients}
            - Categories: {categories}
            - Allergens: {allergens}
            - Nutrition per 100g:
              * Energy: {nutrients.get('energy-kcal_100g', 'N/A')} kcal
              * Fat: {nutrients.get('fat_100g', 'N/A')}g
              * Saturated Fat: {nutrients.get('saturated-fat_100g', 'N/A')}g
              * Sugar: {nutrients.get('sugars_100g', 'N/A')}g
              * Salt: {nutrients.get('salt_100g', 'N/A')}g
              * Fiber: {nutrients.get('fiber_100g', 'N/A')}g
              * Protein: {nutrients.get('proteins_100g', 'N/A')}g

            {user_context}

            Provide analysis in this exact JSON format:
            {{
                "grade": "A/B/C/D/F",
                "score": 85,
                "reasoning": "Brief explanation of the score",
                "health_concerns": ["list", "of", "specific", "concerns"],
                "positive_aspects": ["list", "of", "good", "qualities"],
                "recommendations": ["specific", "suggestions", "for", "improvement"]
            }}

            Scoring Criteria:
            - A (90-100): Excellent nutritional profile, minimal processing, whole foods
            - B (80-89): Good nutritional value, some processing but healthy ingredients
            - C (70-79): Average, acceptable but could be healthier
            - D (60-69): Poor nutritional value, high in unhealthy ingredients
            - F (0-59): Very poor, avoid if possible

            Consider allergens, health conditions, and user's dietary goals in your analysis.
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response (remove markdown code blocks if present)
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            # Parse JSON response
            import json
            analysis = json.loads(result_text)

            return {
                'grade': analysis.get('grade', 'C'),
                'score': analysis.get('score', 70),
                'reasoning': analysis.get('reasoning', 'Analysis completed'),
                'health_concerns': analysis.get('health_concerns', []),
                'positive_aspects': analysis.get('positive_aspects', []),
                'recommendations': analysis.get('recommendations', [])
            }

        except Exception as e:
            logger.error(f"Error analyzing product health score: {e}")
            return {
                'grade': 'C',
                'score': 70,
                'reasoning': 'Analysis failed, assigned average score',
                'health_concerns': ['Unable to analyze'],
                'positive_aspects': [],
                'recommendations': ['Try another product for detailed analysis']
            }

    def find_healthier_alternatives(self, original_product: Dict[str, Any], category_products: List[Dict[str, Any]], user_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find healthier alternatives in the same category.

        Args:
            original_product: The scanned product
            category_products: Other products in same category
            user_profile: User's health profile

        Returns:
            List of recommended healthier alternatives
        """
        try:
            if not category_products:
                return []

            # Analyze all products in category
            analyzed_products = []
            for product in category_products[:10]:  # Limit to top 10 for performance
                analysis = self.analyze_product_health_score(product, user_profile)
                analyzed_products.append({
                    'product': product,
                    'analysis': analysis,
                    'score': analysis['score']
                })

            # Sort by score (highest first)
            analyzed_products.sort(key=lambda x: x['score'], reverse=True)

            # Return top 3 A/B grade alternatives (excluding original if it's in the list)
            recommendations = []
            original_name = original_product.get('product_name', '').lower()

            for item in analyzed_products:
                product_name = item['product'].get('product_name', '').lower()
                grade = item['analysis']['grade']

                # Skip if it's the same product or not A/B grade
                if product_name == original_name or grade not in ['A', 'B']:
                    continue

                recommendations.append({
                    'product': item['product'],
                    'analysis': item['analysis'],
                    'reasoning': f"Better alternative with grade {grade} (score: {item['score']})"
                })

                if len(recommendations) >= 3:
                    break

            return recommendations

        except Exception as e:
            logger.error(f"Error finding healthier alternatives: {e}")
            return []

    def generate_personalized_recommendation(self, product_analysis: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """
        Generate personalized recommendation based on user profile.

        Args:
            product_analysis: Product health analysis
            user_profile: User's health profile

        Returns:
            Personalized recommendation text
        """
        try:
            grade = product_analysis.get('grade', 'C')
            concerns = product_analysis.get('health_concerns', [])
            user_allergens = user_profile.get('allergens', [])
            user_conditions = user_profile.get('health_conditions', [])

            prompt = f"""
            Generate a personalized recommendation for this product based on the user's profile.

            Product Grade: {grade}
            Health Concerns: {', '.join(concerns)}
            User Allergens: {', '.join(user_allergens)}
            User Health Conditions: {', '.join(user_conditions)}
            User Goal: {user_profile.get('primary_goal', 'General Wellness')}

            Write a brief, helpful recommendation (2-3 sentences) that considers the user's specific health needs and goals.
            """

            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating personalized recommendation: {e}")
            return f"This product received a grade {grade}. Consider your health goals when making food choices."


    async def chat_completion(self, messages: list, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Get chat completion from Gemini AI for Vitalis AI conversations.

        Args:
            messages: List of chat messages
            user_profile: User profile information

        Returns:
            AI response string
        """
        try:
            # Prepare system prompt with business context
            system_prompt = self._get_vitalis_system_prompt(user_profile)

            # Prepare messages for Gemini API
            gemini_messages = []

            # Add system message
            gemini_messages.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })

            # Add assistant acknowledgment
            gemini_messages.append({
                "role": "model",
                "parts": [{"text": "I understand my role as Vitalis AI. I'm ready to help with nutrition and health questions based on PickBetter's system and the user's profile."}]
            })

            # Add conversation history (limit to last 10 messages for context)
            for msg in messages[-10:]:
                role = "model" if msg["role"] == "assistant" else "user"
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            # Generate response
            response = await self.model.generate_content_async(gemini_messages)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error calling Gemini AI for chat: {e}")
            return "I'm sorry, I'm having trouble connecting right now. Please try again later."


    def _get_vitalis_system_prompt(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Get the system prompt with business context for Vitalis AI."""

        base_context = """You are Vitalis AI, an expert nutrition and health assistant for PickBetter, a revolutionary AI-powered food scanning app.

## About PickBetter
PickBetter is a mobile/web application that helps users make healthier food choices through:
- Real-time barcode scanning of food products
- AI-powered nutritional analysis using Google Gemini
- Personalized health recommendations based on user profiles
- Allergen detection and dietary compatibility checking
- Health score grading (A-F) for products
- Alternative product suggestions

## Your Role as Vitalis AI
You are the intelligent chat assistant that provides:
- Expert nutrition advice and guidance
- Answers to questions about scanned products
- Health and wellness recommendations
- Dietary advice based on user conditions
- Analysis of nutritional data and trends
- Educational content about healthy eating

## Business Logic & AI System

### Product Analysis Engine
- Uses Google Gemini AI for comprehensive product analysis
- Evaluates ingredients, nutritional content, and health impact
- Assigns health grades: A (Excellent) to F (Poor)
- Considers processing methods, additives, and nutritional density

### Personalization System
- Analyzes user profiles including:
  - Allergens (peanuts, dairy, gluten, etc.)
  - Health conditions (diabetes, PCOS, hypertension, etc.)
  - Dietary preferences (vegan, keto, paleo, etc.)
  - Fitness goals (weight loss, muscle gain, maintenance)
  - Age, gender, height, weight for caloric needs

### Recommendation Algorithm
- Suggests healthier alternatives when products score C or below
- Matches alternatives based on similar nutritional profiles
- Considers allergen compatibility and dietary restrictions
- Provides personalized reasoning for each recommendation

### Health Scoring Methodology
Based on Indian dietary guidelines and international nutritional standards:
- **Grade A (90-100)**: Whole foods, minimal processing, nutrient-dense
- **Grade B (80-89)**: Good nutritional value, some processing but healthy ingredients
- **Grade C (70-79)**: Average, acceptable but could be healthier
- **Grade D (60-69)**: Poor nutritional value, high in unhealthy ingredients
- **Grade F (0-59)**: Very poor, avoid if possible

### Key Features
- **Allergen Detection**: Real-time scanning of ingredients against user allergies
- **Nutrient Analysis**: Detailed breakdown of calories, macros, vitamins, minerals
- **Health Impact Assessment**: How products affect specific health conditions
- **Meal Planning**: Integration with daily nutritional goals
- **Progress Tracking**: Long-term health trend analysis

## Response Guidelines

### Communication Style
- EXTREMELY CONCISE: Limit responses to 1-2 short sentences unless the user explicitly requests more detail.
- PLAIN TEXT ONLY: Do NOT use any Markdown formatting whatsoever (no asterisks, no bolding, no lists, no italics).
- Friendly, knowledgeable, and encouraging
- Use "we" when referring to PickBetter features

### Answer Structure
- Get straight to the point without filler words.
- Give one actionable, practical recommendation or piece of information.

### Important Notes
- Always consider the user's health conditions and allergies
- Base recommendations on scientific evidence
- Respect cultural and personal dietary preferences
- Promote balanced, sustainable nutrition
- Direct users to healthcare professionals for medical advice
"""

        # Add user-specific context if available
        if user_profile:
            user_context = f"""

## Current User Profile
- **Conditions**: {', '.join(user_profile.get('conditions', ['General wellness']))}
- **Allergens**: {', '.join(user_profile.get('allergens', ['None specified']))}
- **Dietary Preferences**: {user_profile.get('dietary_preference', 'Not specified')}
- **Primary Goal**: {user_profile.get('primary_goal', 'General health')}
- **Age**: {user_profile.get('age', 'Not specified')}, **Gender**: {user_profile.get('sex', 'Not specified')}

Please tailor your responses to this user's specific health needs, allergies, and goals. Be particularly attentive to their conditions and avoid recommending anything that conflicts with their allergies or health requirements.
"""
            base_context += user_context

        return base_context


    def synthesize_product_from_barcode(self, barcode: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synthesize a realistic product profile for an unknown barcode using Gemini.

        Args:
            barcode: The unknown barcode string
            user_profile: User's health profile and preferences
            
        Returns:
            Dict containing original_product, gemini_analysis, and recommendations.
        """
        try:
            user_context = ""
            if user_profile:
                user_context = f"""
                User Profile for Personalization:
                - Allergens to avoid: {', '.join(user_profile.get('allergens', []))}
                - Health conditions: {', '.join(user_profile.get('health_conditions', []))}
                - Dietary preference: {user_profile.get('dietary_preference', 'General')}
                - Primary goal: {user_profile.get('primary_goal', 'General Wellness')}
                """

            prompt = f"""
            A user has scanned a barcode '{barcode}'. 
            Please try to identify the ACTUAL real-world packaged food product associated with this exact barcode if you know it from your training data (e.g. if it matches a famous brand in India or globally). If you absolutely don't know the exact product, infer what it most likely is based on the manufacturer prefix, or synthesize a realistic plausible product.
            
            Generate a comprehensive nutritional profile and an analysis of its health score (A to F) for this product.

            {user_context}

            IMPORTANT: 
            1. If you absolutely do NOT know the exact real-world product and cannot confidently infer it from the barcode or brand prefix, DO NOT HALLUCINATE A PRODUCT. Instead, return a single JSON object with a single key "NOT_FOUND" set to true, like this: `{{ "NOT_FOUND": true }}`.
            
            2. ALLERGEN STRICTNESS: If an allergen (like peanuts, dairy, etc.) is NOT explicitly present in the inferred or known ingredients list, you MUST NOT flag it as a health concern, even if the user profile lists it. Only flag allergens that are demonstrably present in the food.
            
            3. SCORING FAIRNESS: The health score (A-F, 0-100) MUST be objective, consistent, and strictly based on the nutrition values and ingredients. Do not inflate scores for sugary, highly processed, or saturated fat-heavy products. Score them realistically low.
            
            If you DO know the product, you MUST return a STRICT JSON object that perfectly matches the structure below.
            Do not include any other text except the JSON.
            
            Format:
            {{
                "original_product": {{
                    "product_name": "Synthesized Product Name",
                    "brands": "Plausible Brand Name",
                    "ingredients_text": "Detailed list of ingredients",
                    "nutriments": {{
                        "energy-kcal_100g": 250,
                        "proteins_100g": 10,
                        "carbohydrates_100g": 30,
                        "fat_100g": 5
                    }},
                    "image_url": "https://via.placeholder.com/300x300?text=Scan+Result",
                    "code": "{barcode}"
                }},
                "gemini_analysis": {{
                    "grade": "C",
                    "score": 65,
                    "reasoning": "Reason for health score based objectively on ingredients and nutrition (no inflated scores)",
                    "health_concerns": ["list", "of", "concerns", "strict: only if present in ingredients"],
                    "positive_aspects": ["list", "of", "positives"]
                }},
                "recommendations": [
                    {{
                        "product": {{
                            "product_name": "Healthier Alternative Name",
                            "brands": "Alternative Brand",
                            "code": "0000000000000",
                            "image_url": "https://via.placeholder.com/200x200?text=Alternative"
                        }},
                        "analysis": {{
                            "grade": "A",
                            "score": 90,
                            "reasoning": "Why this is healthier"
                        }},
                        "personalized_recommendation": "Why this is good for the user",
                        "image_url": "https://via.placeholder.com/200x200?text=Alternative",
                        "reasoning": "Why this is a good choice"
                    }}
                ],
                "total_found": 1,
                "message": "AI Synthesized Product Profile",
                "user_context": "Brief summary of personalization context if any"
            }}
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response formatting
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            import json
            result_data = json.loads(result_text)
            
            if result_data.get("NOT_FOUND") is True:
                # Deliberate failure signal to trigger UI contribution flow
                logger.info(f"Gemini declined to synthesize unknown product for barcode: {barcode}")
                return None
            
            return result_data

        except Exception as e:
            logger.error(f"Error synthesizing product from barcode {barcode}: {e}")
            # Mock fallback in case synthesis entirely fails
            return {
                "original_product": {
                    "product_name": f"Unknown Product ({barcode})",
                    "brands": "Unknown",
                    "ingredients_text": "No ingredients available. Could not be synthesized.",
                    "nutriments": {},
                    "image_url": "https://via.placeholder.com/300x300?text=Unknown",
                    "code": barcode
                },
                "gemini_analysis": {
                    "grade": "N",
                    "score": 0,
                    "reasoning": "Could not synthesize analysis.",
                    "health_concerns": [],
                    "positive_aspects": []
                },
                "recommendations": [],
                "total_found": 1,
                "message": "AI analysis failed.",
                "user_context": ""
            }

    def analyze_product_data(self, product_data: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a real product fetched from OpenFoodFacts using Gemini to generate
        a personalized health grade, score, reasoning, and valid alternatives.

        Args:
            product_data: The real product data dictionary from the database/OpenFoodFacts
            user_profile: User's health profile and preferences
            
        Returns:
            Dict containing original_product, gemini_analysis, and recommendations.
        """
        try:
            import json
            
            user_context = ""
            if user_profile:
                user_context = f"""
                User Profile for Personalization:
                - Allergens to avoid: {', '.join(user_profile.get('allergens', []))}
                - Health conditions: {', '.join(user_profile.get('health_conditions', []))}
                - Dietary preference: {user_profile.get('dietary_preference', 'General')}
                - Primary goal: {user_profile.get('primary_goal', 'General Wellness')}
                """

            prompt = f"""
            A user has scanned a product which we actually found in our database.
            Please analyze its nutritional profile, determine its objective health score (A to F), 
            and recommend a healthier alternative if the product receives a grade worse than 'A'.
            
            Here is the REAL product data:
            {json.dumps(product_data, default=str)}

            {user_context}

            IMPORTANT: 
            1. ALLERGEN STRICTNESS: If an allergen (like peanuts, dairy, etc.) is NOT explicitly present in the provided ingredients check, you MUST NOT flag it as a health concern, even if the user profile lists it. Only flag allergens that are demonstrably present in the food.
            
            2. SCORING FAIRNESS: The health score (A-F, 0-100) MUST be objective, consistent, and strictly based on the provided nutrition values and ingredients. Do not inflate scores for sugary, highly processed, or saturated fat-heavy products. Score them realistically low.
            
            You MUST return a STRICT JSON object that perfectly matches the structure below.
            Do not include any other text except the JSON.
            
            Format:
            {{
                "original_product": {{
                    "product_name": "Actual Product Name",
                    "brands": "Actual Brand Name",
                    "ingredients_text": "Actual list of ingredients",
                    "nutriments": {{
                        "energy-kcal_100g": 250,
                        "proteins_100g": 10,
                        "carbohydrates_100g": 30,
                        "fat_100g": 5
                    }},
                    "image_url": "Actual Image URL",
                    "code": "Actual Code"
                }},
                "gemini_analysis": {{
                    "grade": "C",
                    "score": 65,
                    "reasoning": "Reason for health score based objectively on ingredients and nutrition",
                    "health_concerns": ["list", "of", "concerns", "strict: only if present in ingredients"],
                    "positive_aspects": ["list", "of", "positives"]
                }},
                "recommendations": [
                    {{
                        "product": {{
                            "product_name": "Healthier Alternative Name",
                            "brands": "Alternative Brand",
                            "code": "0000000000000",
                            "image_url": "https://via.placeholder.com/200x200?text=Alternative"
                        }},
                        "analysis": {{
                            "grade": "A",
                            "score": 90,
                            "reasoning": "Why this is healthier"
                        }},
                        "personalized_recommendation": "Why this is good for the user",
                        "image_url": "https://via.placeholder.com/200x200?text=Alternative",
                        "reasoning": "Why this is a good choice"
                    }}
                ],
                "total_found": 1,
                "message": "AI Analyzed Product Profile",
                "user_context": "Brief summary of personalization context if any"
            }}
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            result_data = json.loads(result_text)
            return result_data

        except Exception as e:
            logger.error(f"Error analyzing product data: {e}")
            barcode = product_data.get('barcode', 'unknown')
            return {
                "original_product": {
                    "product_name": product_data.get('name', f"Unknown ({barcode})"),
                    "brands": product_data.get('brand', 'Unknown'),
                    "ingredients_text": product_data.get('ingredients_text', ''),
                    "nutriments": product_data.get('nutriments', {}),
                    "image_url": product_data.get('image_url', "https://via.placeholder.com/300x300?text=Unknown"),
                    "code": barcode
                },
                "gemini_analysis": {
                    "grade": product_data.get('health_grade', 'N'),
                    "score": product_data.get('health_score', 0),
                    "reasoning": "AI Analysis failed, showing database values.",
                    "health_concerns": [],
                    "positive_aspects": []
                },
                "recommendations": [],
                "total_found": 1,
                "message": "AI analysis failed.",
                "user_context": ""
            }


# Global service instance
gemini_service = GeminiService()
