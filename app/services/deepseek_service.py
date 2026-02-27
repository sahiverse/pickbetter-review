"""DeepSeek AI service for Vitalis AI chat functionality."""
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DeepSeekService:
    """Service for interacting with DeepSeek AI."""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"  # or deepseek-coder depending on needs

    async def chat_completion(self, messages: list, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Get chat completion from DeepSeek AI.

        Args:
            messages: List of chat messages
            user_profile: User profile information

        Returns:
            AI response string
        """
        try:
            # Prepare system prompt with business context
            system_prompt = self._get_system_prompt(user_profile)

            # Prepare messages for DeepSeek API
            deepseek_messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history
            for msg in messages[-10:]:  # Limit to last 10 messages
                role = "user" if msg["role"] == "user" else "assistant"
                deepseek_messages.append({
                    "role": role,
                    "content": msg["content"]
                })

            # Make API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": deepseek_messages,
                        "max_tokens": 1000,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return "I'm sorry, I'm having trouble connecting right now. Please try again later."

        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return "I'm experiencing some technical difficulties. Please try again in a moment."

    def _get_system_prompt(self, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Get the system prompt with business context."""

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
- **Grade A**: Whole foods, minimal processing, nutrient-dense
- **Grade B**: Good nutritional profile with some processing
- **Grade C**: Moderate nutrition, may have concerns
- **Grade D**: High in sugar/fat/salt, processed ingredients
- **Grade E**: Poor nutritional value, multiple red flags
- **Grade F**: Extremely unhealthy, avoid when possible

### Key Features
- **Allergen Detection**: Real-time scanning of ingredients against user allergies
- **Nutrient Analysis**: Detailed breakdown of calories, macros, vitamins, minerals
- **Health Impact Assessment**: How products affect specific health conditions
- **Meal Planning**: Integration with daily nutritional goals
- **Progress Tracking**: Long-term health trend analysis

## Response Guidelines

### Communication Style
- Friendly, knowledgeable, and encouraging
- Use "we" when referring to PickBetter features
- Be conversational but informative
- Provide actionable advice
- Encourage healthy habits without being judgmental

### Expertise Areas
- Nutrition science and dietary guidelines
- Food chemistry and ingredient analysis
- Health conditions and their nutritional management
- Sustainable and ethical food choices
- Cultural dietary preferences (especially Indian cuisine)

### Answer Structure
1. **Acknowledge the query** and show understanding
2. **Provide evidence-based information** with reasoning
3. **Give practical recommendations** when applicable
4. **Suggest app features** that could help
5. **Encourage further questions** or scanning

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


# Global service instance
deepseek_service = DeepSeekService()
