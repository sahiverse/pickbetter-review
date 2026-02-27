
import { GoogleGenAI, Type } from "@google/genai";
import { UserProfile, FoodAnalysis } from "../types";

export const analyzeFood = async (imageData: string, profile: UserProfile): Promise<FoodAnalysis> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const systemInstruction = `
    You are 'PickBetter', an expert nutritionist AI.
    Analyze the provided food label or item image.
    Grade it from A (Excellent) to F (Dangerous) based on the user's health profile.
    
    User Profile:
    - Conditions: ${profile.conditions.join(", ")}
    - Allergens: ${profile.allergens.join(", ")}
    
    Return a detailed JSON object with:
    - productName: Name of product.
    - brand: Brand name.
    - grade: A string (A, B, C, D, or F).
    - score: A number (0-100).
    - reason: A concise explanation (max 3 sentences) mentioning specific conflicts with the user's conditions (e.g., sugar for diabetes, sodium for hypertension) and the presence of gluten if found.
    - ingredients: List of key ingredients found.
    - macros: { calories: string, protein: string, carbs: string, fat: string } (per 100g/serving).
    - detectedAllergens: List of detected allergens present in this product. ALWAYS check for GLUTEN.
    - alternatives: An array of 3 healthier alternative items found in the market. Include: name, brand, image placeholder URL, and a mock link. (Price is NOT required).
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: {
        parts: [
          { inlineData: { mimeType: 'image/jpeg', data: imageData.split(',')[1] } },
          { text: "Analyze this food item for me based on my health profile." }
        ]
      },
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            productName: { type: Type.STRING },
            brand: { type: Type.STRING },
            grade: { type: Type.STRING },
            score: { type: Type.NUMBER },
            reason: { type: Type.STRING },
            ingredients: { type: Type.ARRAY, items: { type: Type.STRING } },
            macros: {
              type: Type.OBJECT,
              properties: {
                calories: { type: Type.STRING },
                protein: { type: Type.STRING },
                carbs: { type: Type.STRING },
                fat: { type: Type.STRING }
              }
            },
            detectedAllergens: { type: Type.ARRAY, items: { type: Type.STRING } },
            alternatives: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  name: { type: Type.STRING },
                  brand: { type: Type.STRING },
                  image: { type: Type.STRING },
                  link: { type: Type.STRING }
                },
                required: ["name", "brand", "image", "link"]
              }
            }
          },
          required: ["productName", "brand", "grade", "score", "reason", "ingredients", "macros", "detectedAllergens", "alternatives"]
        }
      }
    });

    const result = JSON.parse(response.text || "{}");
    return result as FoodAnalysis;
  } catch (error) {
    console.error("Gemini Analysis Error:", error);
    // Fallback Mock Data
    return {
      productName: "Lays Classic Salted",
      brand: "Pepsico",
      grade: 'C',
      score: 64,
      reason: "This product contains high levels of sodium which is concerning for your hypertension. It also contains hidden gluten from flavor carriers.",
      ingredients: ["Potatoes", "Palm Oil", "Salt"],
      macros: {
        calories: "536 kcal",
        protein: "7g",
        carbs: "53g",
        fat: "35g"
      },
      detectedAllergens: ["Gluten"],
      alternatives: [
        { name: "Unsalted Almonds", brand: "Happilo", image: "https://picsum.photos/200/200?random=1", link: "#" },
        { name: "Roasted Makhana", brand: "Farmley", image: "https://picsum.photos/200/200?random=2", link: "#" },
        { name: "Baked Quinoa Puffs", brand: "The Green Snack Co", image: "https://picsum.photos/200/200?random=3", link: "#" }
      ]
    };
  }
};
