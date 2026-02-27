import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import AuthScreen from './screens/Auth';
import OnboardingScreen from './screens/Onboarding';
import MainShell from './screens/MainShell';
import ScannerScreen from './screens/Scanner';
import ResultsScreen from './screens/Results';
import ProfileScreen from './screens/Profile';
import ContributionScreen from './screens/Contribution';
import { Screen, UserProfile, FoodAnalysis, Tab, HistoryItem } from './types';
import { AuthProvider, useAuth } from './src/contexts/AuthContext';

// AppContent component that uses authentication context
const AppContent: React.FC = () => {
  const { user, isAuthenticated, loading, getIdToken } = useAuth();
  const [currentScreen, setCurrentScreen] = useState<Screen>('auth');
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: '',
    age: '',
    sex: 'Male',
    height: '',
    weight: '',
    conditions: [],
    allergens: [],
    dietType: 'General',
    primaryGoal: 'General Wellness'
  });
  const [analysisResult, setAnalysisResult] = useState<FoodAnalysis | null>(null);
  const [pendingContributionBarcode, setPendingContributionBarcode] = useState<string | null>(null);
  const [scanHistory, setScanHistory] = useState<HistoryItem[]>([]);

  // Handle authentication-based routing + load history from localStorage
  useEffect(() => {
    if (loading) return;

    if (!isAuthenticated) {
      setCurrentScreen('auth');
      setScanHistory([]);
    } else if (currentScreen === 'auth') {
      setCurrentScreen('main');
      // Load saved history for this user
      if (user?.uid) {
        try {
          const saved = localStorage.getItem(`scanHistory_${user.uid}`);
          if (saved) setScanHistory(JSON.parse(saved));
        } catch { }
      }
    }
  }, [isAuthenticated, loading]);

  // Helper: save a completed scan to history
  const saveToHistory = (analysis: FoodAnalysis) => {
    if (!user?.uid) return;
    const newItem: HistoryItem = {
      id: `${Date.now()}`,
      name: analysis.productName,
      brand: analysis.brand || '',
      grade: analysis.grade,
      score: analysis.score,
      timestamp: new Date().toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true, day: 'numeric', month: 'short' }),
      fullAnalysis: analysis,
    };
    setScanHistory(prev => {
      const updated = [newItem, ...prev].slice(0, 50); // keep last 50
      localStorage.setItem(`scanHistory_${user.uid}`, JSON.stringify(updated));
      return updated;
    });
  };

  // Show loading screen while checking authentication
  if (loading) {
    return (
      <div className="max-w-md mx-auto h-screen bg-[#FFFDE1] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#93BD57] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-bold">Loading...</p>
        </div>
      </div>
    );
  }

  const navigate = (screen: Screen) => setCurrentScreen(screen);

  const handleHistoryItemClick = (item: HistoryItem) => {
    // Use the saved full analysis if available, otherwise build a minimal one
    const analysis: FoodAnalysis = (item as any).fullAnalysis || {
      productName: item.name,
      brand: item.brand,
      grade: item.grade,
      score: item.score || (item.grade === 'A' ? 92 : item.grade === 'B' ? 78 : item.grade === 'C' ? 62 : item.grade === 'D' ? 45 : 20),
      reason: `Historical scan for ${item.name}.`,
      ingredients: [],
      macros: { calories: 'N/A', protein: 'N/A', carbs: 'N/A', fat: 'N/A' },
      detectedAllergens: [],
      alternatives: []
    };
    setAnalysisResult(analysis);
    navigate('results');
  };

  const handleSignOut = () => {
    setCurrentScreen('auth');
  };

  return (
    <div className="max-w-md mx-auto h-screen bg-[#FFFDE1] text-slate-900 overflow-hidden relative shadow-2xl">
      <AnimatePresence mode="wait">
        {currentScreen === 'auth' && (
          <motion.div key="auth" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
            <AuthScreen />
          </motion.div>
        )}

        {currentScreen === 'onboarding' && (
          <motion.div key="onboarding" initial={{ opacity: 0, x: 100 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -100 }} className="h-full">
            <OnboardingScreen
              profile={userProfile}
              setProfile={setUserProfile}
              onComplete={() => navigate('main')}
            />
          </motion.div>
        )}

        {currentScreen === 'main' && (
          <motion.div key="main" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
            <MainShell
              profile={userProfile}
              onScanRequest={() => navigate('scanner')}
              onProfileRequest={() => navigate('profile')}
              onHistoryItemClick={handleHistoryItemClick}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              scanHistory={scanHistory}
            />
          </motion.div>
        )}

        {currentScreen === 'profile' && (
          <motion.div key="profile" initial={{ opacity: 0, x: -100 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 100 }} className="h-full">
            <ProfileScreen
              profile={userProfile}
              setProfile={setUserProfile}
              onBack={() => navigate('main')}
              onSignOut={handleSignOut}
            />
          </motion.div>
        )}

        {currentScreen === 'scanner' && (
          <motion.div key="scanner" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
            <ScannerScreen
              onBarcodeDetected={async (payload: string | { notFound: true, barcode: string }) => {
                let barcode = '';

                // If the scanner inherently tells us it is not found (404), skip backend and route to contribution
                if (typeof payload === 'object' && payload.notFound) {
                  console.log('⚠️ Scanner component flagged product as not found (404). Asking user to contribute.');
                  setPendingContributionBarcode(payload.barcode);
                  navigate('contribution');
                  return;
                } else {
                  barcode = payload as string;
                }

                console.log('📦 Barcode detected:', barcode);
                try {
                  console.log('📡 Fetching product data and analyzing with Gemini...');

                  // Call the scan endpoint which will fetch from DB/Open Food Facts and analyze with Gemini
                  const scanResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL}/products/scan/${barcode}`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${getIdToken ? await getIdToken() : ''}`,
                      'Content-Type': 'application/json'
                    }
                  });

                  if (scanResponse.status === 404) {
                    console.log('⚠️ Product not found in database or OpenFoodFacts. Asking user to contribute.');
                    setPendingContributionBarcode(barcode);
                    navigate('contribution');
                    return;
                  }

                  if (!scanResponse.ok) {
                    throw new Error(`Scan failed: ${scanResponse.status}`);
                  }

                  const scanResult = await scanResponse.json();
                  console.log('✅ Raw scan result:', JSON.stringify(scanResult, null, 2));

                  // Robustly parse the API response - handle any field being null/undefined
                  const geminiData = scanResult?.data ?? scanResult; // some endpoints return data at root
                  const prod = geminiData?.original_product ?? {};
                  const analysis = geminiData?.gemini_analysis ?? {};
                  const nutriments = prod?.nutriments ?? {};

                  // Helper: pull nutriment value trying multiple common key variants
                  const nut = (keys: string[]) => {
                    for (const k of keys) if (nutriments[k] != null) return nutriments[k];
                    return null;
                  };

                  const ingredientsText: string = prod?.ingredients_text ?? '';

                  const foodAnalysis: FoodAnalysis = {
                    productName: prod?.product_name || prod?.name || 'Unknown Product',
                    brand: prod?.brands || prod?.brand || '',
                    grade: (['A', 'B', 'C', 'D', 'F'].includes(analysis?.grade) ? analysis.grade : 'C') as 'A' | 'B' | 'C' | 'D' | 'F',
                    score: typeof analysis?.score === 'number' ? analysis.score : 50,
                    reason: analysis?.reasoning || analysis?.reason || '',
                    ingredients: ingredientsText ? [ingredientsText] : [],
                    macros: {
                      calories: nut(['energy-kcal_100g', 'energy_kcal_100g', 'calories_100g']) != null
                        ? `${nut(['energy-kcal_100g', 'energy_kcal_100g', 'calories_100g'])} kcal` : 'N/A',
                      protein: nut(['proteins_100g', 'protein_100g', 'protein']) != null
                        ? `${nut(['proteins_100g', 'protein_100g', 'protein'])}g` : 'N/A',
                      carbs: nut(['carbohydrates_100g', 'carbohydrate_100g', 'carbs_100g']) != null
                        ? `${nut(['carbohydrates_100g', 'carbohydrate_100g', 'carbs_100g'])}g` : 'N/A',
                      fat: nut(['fat_100g', 'fats_100g', 'total_fat_100g']) != null
                        ? `${nut(['fat_100g', 'fats_100g', 'total_fat_100g'])}g` : 'N/A',
                    },
                    detectedAllergens: (userProfile?.allergens || []).filter(allergen => {
                      const ing = ingredientsText.toLowerCase();
                      const a = allergen.toLowerCase();
                      const keywords: Record<string, string[]> = {
                        'peanuts': ['peanut', 'groundnut'],
                        'nuts': ['almond', 'walnut', 'cashew', 'pistachio', 'nut'],
                        'milk': ['milk', 'dairy', 'lactose', 'cheese', 'yogurt', 'cream', 'butter'],
                        'eggs': ['egg', 'albumin'],
                        'soy': ['soy', 'soya', 'soybean', 'tofu'],
                        'wheat': ['wheat', 'gluten', 'flour', 'maida'],
                      };
                      return (keywords[a] ?? [a]).some(kw => ing.includes(kw));
                    }),
                    alternatives: (geminiData?.recommendations ?? []).map((rec: any) => ({
                      name: rec?.product?.product_name || rec?.product?.name || 'Unknown',
                      brand: rec?.product?.brands || rec?.product?.brand || '',
                      grade: rec?.analysis?.grade || 'B',
                      score: rec?.analysis?.score ?? 70,
                      reasoning: rec?.personalized_recommendation || rec?.reasoning || '',
                      image_url: rec?.image_url || rec?.product?.image_url || null,
                    })),
                    image_url: prod?.image_url || null,
                    gemini_analysis: analysis,
                    user_context: geminiData?.user_context || '',
                  };

                  console.log('📦 Hydrating Results Screen with:', JSON.stringify(foodAnalysis, null, 2));
                  setAnalysisResult(foodAnalysis);
                  saveToHistory(foodAnalysis);
                  navigate('results');
                  return;

                } catch (error: any) {
                  console.error('❌ Error:', error);
                  alert(`Failed to analyze product: ${error.message}`);
                }
              }}
              onBack={() => navigate('main')}
            />
          </motion.div>
        )}

        {currentScreen === 'results' && analysisResult && (
          <motion.div key="results" initial={{ opacity: 0, y: 100 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 100 }} className="h-full">
            <ResultsScreen
              result={analysisResult}
              profile={userProfile}
              onBack={() => navigate('main')}
              onReScan={() => navigate('scanner')}
              onAskAI={(context) => {
                setActiveTab('chat');
                navigate('main');
              }}
            />
          </motion.div>
        )}

        {currentScreen === 'contribution' && pendingContributionBarcode && (
          <motion.div key="contribution" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
            <ContributionScreen
              barcode={pendingContributionBarcode}
              onBack={() => navigate('main')}
              onContributionSuccess={(result) => {
                // Handle Gemini Vision contribution result (new format)
                if (result.status === 'success' && result.data) {
                  const geminiData = result.data;
                  const foodAnalysis: FoodAnalysis = {
                    productName: geminiData.original_product?.product_name || 'Unknown Product',
                    brand: geminiData.original_product?.brands || '',
                    grade: geminiData.gemini_analysis?.grade || 'C',
                    score: geminiData.gemini_analysis?.score || 50,
                    reason: geminiData.gemini_analysis?.reasoning || '',
                    ingredients: geminiData.original_product?.ingredients_text
                      ? [geminiData.original_product.ingredients_text]
                      : [],
                    macros: {
                      calories: geminiData.original_product?.nutriments?.['energy-kcal_100g']
                        ? `${geminiData.original_product.nutriments['energy-kcal_100g']} kcal` : 'N/A',
                      protein: geminiData.original_product?.nutriments?.['proteins_100g']
                        ? `${geminiData.original_product.nutriments['proteins_100g']}g` : 'N/A',
                      carbs: geminiData.original_product?.nutriments?.['carbohydrates_100g']
                        ? `${geminiData.original_product.nutriments['carbohydrates_100g']}g` : 'N/A',
                      fat: geminiData.original_product?.nutriments?.['fat_100g']
                        ? `${geminiData.original_product.nutriments['fat_100g']}g` : 'N/A',
                    },
                    detectedAllergens: [],
                    alternatives: geminiData.recommendations?.map((rec: any) => ({
                      name: rec.product?.product_name,
                      brand: rec.product?.brands,
                      grade: rec.analysis?.grade,
                      score: rec.analysis?.score,
                      reasoning: rec.personalized_recommendation || rec.reasoning,
                      image_url: rec.image_url
                    })) || [],
                    image_url: geminiData.original_product?.image_url,
                    gemini_analysis: geminiData.gemini_analysis,
                  };
                  setAnalysisResult(foodAnalysis);
                  saveToHistory(foodAnalysis);
                  navigate('results');
                }
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Main App component that provides authentication context
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
