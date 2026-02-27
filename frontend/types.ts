
export type Screen = 'auth' | 'onboarding' | 'main' | 'scanner' | 'results' | 'profile' | 'contribution';
export type Tab = 'home' | 'history' | 'chat';

export interface UserProfile {
  name: string;
  age?: string;
  sex?: 'Male' | 'Female' | 'Other';
  height?: string;
  weight?: string;
  conditions: string[];
  allergens: string[];
  custom_needs?: string[];
  custom_needs_status?: 'pending' | 'reviewed' | 'implemented';
  dietType?: string;
  primaryGoal?: string;
}

export interface FoodAnalysis {
  productName: string;
  brand: string;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  score: number;
  reason: string;
  ingredients: string[];
  macros: {
    calories: string;
    protein: string;
    carbs: string;
    fat: string;
  };
  detectedAllergens: string[];
  alternatives: Alternative[];
  image_url?: string;
  gemini_analysis?: any; // Gemini AI analysis data
  user_context?: string; // User context for personalization
}

export interface Alternative {
  name: string;
  brand: string;
  grade?: 'A' | 'B' | 'C' | 'D' | 'F';
  score?: number;
  reasoning?: string;
  image_url?: string | null;
  // Legacy fields (kept for backward compatibility)
  price?: string;
  image?: string;
  link?: string;
}

export interface HistoryItem {
  id: string;
  name: string;
  brand: string;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  score: number;
  timestamp: string;
  fullAnalysis?: FoodAnalysis;  // Full saved result for re-viewing
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export interface HealthCondition {
  id: string;
  label: string;
  icon: string;
}
