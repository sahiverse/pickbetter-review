
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FoodAnalysis, UserProfile, Alternative } from '../types';

interface ResultsProps {
  result: FoodAnalysis;
  profile: UserProfile;
  onBack: () => void;
  onReScan: () => void;
  onAskAI: (context: string) => void;
}

const ResultsScreen: React.FC<ResultsProps> = ({ result: initialResult, profile, onBack, onReScan, onAskAI }) => {
  const [currentResult, setCurrentResult] = useState<FoodAnalysis>(initialResult);
  const [shopModalProduct, setShopModalProduct] = useState<string | null>(null);

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-[#93BD57] text-white';
      case 'B': return 'bg-[#93BD57]/80 text-white';
      case 'C': return 'bg-[#FBE580] text-slate-900';
      case 'D': return 'bg-orange-500 text-white';
      case 'F': return 'bg-[#980404] text-white';
      default: return 'bg-slate-100 text-slate-400';
    }
  };

  const matchedAllergens = (profile?.allergens || []).filter(a =>
    currentResult.detectedAllergens.some(da => da.toLowerCase().includes(a.toLowerCase()))
  );

  const glutenDetected = currentResult.detectedAllergens.some(a => a.toLowerCase().includes('gluten')) ||
    currentResult.reason.toLowerCase().includes('gluten');

  const hasAllergyWarning = matchedAllergens.length > 0 || glutenDetected;

  const matchedConditions = (profile?.conditions || []).filter(c =>
    currentResult.reason.toLowerCase().includes(c.toLowerCase()) ||
    (c.toLowerCase().includes('diabetes') && (currentResult.reason.toLowerCase().includes('sugar') || currentResult.reason.toLowerCase().includes('glucose') || (currentResult.macros.carbs && parseInt(currentResult.macros.carbs) > 15))) ||
    (c.toLowerCase().includes('hypertension') && (currentResult.reason.toLowerCase().includes('sodium') || currentResult.reason.toLowerCase().includes('salt')))
  );

  const hasConditionWarning = matchedConditions.length > 0;

  // Logic to hide shop button for C, D, F grades
  const isShoppable = currentResult.grade === 'A' || currentResult.grade === 'B';

  const openShop = (platform: string, productName: string) => {
    let url = '';
    const query = encodeURIComponent(productName);
    switch (platform) {
      case 'Blinkit': url = `https://blinkit.com/s/?q=${query}`; break;
      case 'BigBasket': url = `https://www.bigbasket.com/ps/?q=${query}`; break;
      case 'Amazon': url = `https://www.amazon.in/s?k=${query}`; break;
      case 'Flipkart': url = `https://www.flipkart.com/search?q=${query}`; break;
    }
    window.open(url, '_blank');
    setShopModalProduct(null);
  };

  const handleViewSwap = (swap: Alternative) => {
    const swapResult: FoodAnalysis = {
      productName: swap.name || 'Unknown Product',
      brand: swap.brand || '',
      grade: (['A', 'B', 'C', 'D', 'F'].includes(swap.grade ?? '') ? swap.grade! : 'B') as 'A' | 'B' | 'C' | 'D' | 'F',
      score: swap.score ?? 70,
      reason: swap.reasoning || `A healthier alternative for your ${(profile?.conditions || [])[0] || 'wellness'} goals.`,
      ingredients: [],
      macros: { calories: 'N/A', protein: 'N/A', carbs: 'N/A', fat: 'N/A' },
      detectedAllergens: [],
      alternatives: [],
      image_url: swap.image_url || null,
    };
    setCurrentResult(swapResult);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] overflow-hidden relative">
      {/* Header */}
      <header className="px-6 pt-12 pb-4 flex items-center justify-between relative z-10 shrink-0">
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={() => currentResult.productName !== initialResult.productName ? setCurrentResult(initialResult) : onBack()}
          className="w-10 h-10 glass rounded-xl flex items-center justify-center shadow-sm"
        >
          <svg className="w-6 h-6 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
          </svg>
        </motion.button>
        <h2 className="text-sm font-black text-slate-900 tracking-widest uppercase">Product Information</h2>
        <div className="w-10" />
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar pb-32">
        {/* Score Bubble Hero */}
        <section className="px-6 pt-4 flex flex-col items-center gap-6">
          <div className="relative flex items-center justify-center">
            {/* Outer glow ring */}
            <motion.div
              key={currentResult.productName}
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 18 }}
              className={`relative w-52 h-52 rounded-full flex flex-col items-center justify-center shadow-2xl border-8 border-white ${getGradeColor(currentResult.grade)}`}
            >
              {/* Subtle pulse ring */}
              <motion.div
                animate={{ scale: [1, 1.08, 1], opacity: [0.4, 0.1, 0.4] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
                className={`absolute inset-0 rounded-full ${getGradeColor(currentResult.grade)}`}
              />
              <span className="text-8xl font-black text-white leading-none z-10 drop-shadow-lg">
                {currentResult.grade}
              </span>
              <span className="text-white/80 font-black text-sm uppercase tracking-widest z-10 mt-1">
                {currentResult.score} / 100
              </span>
            </motion.div>
          </div>

          <div className="text-center space-y-1">
            <h1 className="text-3xl font-black text-slate-900 tracking-tighter uppercase leading-none">{currentResult.productName}</h1>
            <p className="text-slate-400 font-black text-xs uppercase tracking-widest">{currentResult.brand}</p>
          </div>
        </section>


        {/* Personalized Health Alerts */}
        <section className="px-6 mt-8 space-y-3">
          <AnimatePresence>
            {(matchedAllergens.length > 0 || glutenDetected) && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                className="bg-[#980404] text-white p-5 rounded-[28px] shadow-lg flex items-center gap-4 border-b-4 border-black/20"
              >
                <div className="text-[#980404] bg-white rounded-full p-2">
                  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-[10px] font-black uppercase tracking-widest">Alert: Contains</h4>
                  <p className="text-[11px] font-bold opacity-90 leading-tight">
                    {glutenDetected && <span className="underline decoration-2">GLUTEN</span>}
                    {matchedAllergens.length > 0 && <span> {matchedAllergens.join(', ')}</span>}
                    . Unsafe for your profile.
                  </p>
                </div>
              </motion.div>
            )}

            {hasConditionWarning && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                className="bg-orange-600 text-white p-5 rounded-[28px] shadow-lg flex items-center gap-4 border-b-4 border-black/20"
              >
                <div className="text-orange-600 bg-white rounded-full p-2">
                  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-[10px] font-black uppercase tracking-widest">Health Conflict</h4>
                  <p className="text-[11px] font-bold opacity-90 leading-tight">
                    Bad for your <b>{matchedConditions.join(', ')}</b>. {currentResult.reason}
                  </p>
                </div>
              </motion.div>
            )}

            {!hasAllergyWarning && !hasConditionWarning && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-[#93BD57]/10 border-2 border-[#93BD57]/20 p-5 rounded-[28px] flex items-center gap-4"
              >
                <div className="text-[#93BD57] bg-white rounded-full p-2 border border-[#93BD57]/20 shadow-sm">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-[10px] font-black text-[#93BD57] uppercase tracking-widest">Safe For You</h4>
                  <p className="text-[11px] font-bold text-slate-600 leading-tight">
                    No allergens, gluten, or health conflicts detected.
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Nutrition Pulse */}
        <section className="px-6 mt-6">
          <div className="bento-card p-6 bg-white/60">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Nutrition Pulse</h3>
              <span className="text-[9px] font-bold text-[#93BD57] uppercase">Per 100g</span>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {[
                { label: 'CAL', val: currentResult.macros.calories, risk: false },
                { label: 'PRO', val: currentResult.macros.protein, risk: false },
                { label: 'CRB', val: currentResult.macros.carbs, risk: hasConditionWarning && matchedConditions.some(c => c.toLowerCase().includes('diabetes')) },
                { label: 'FAT', val: currentResult.macros.fat, risk: false },
              ].map((m, i) => (
                <div key={i} className={`flex flex-col items-center p-2 rounded-2xl ${m.risk ? 'bg-[#980404]/10 border border-[#980404]/20' : 'bg-white/40'}`}>
                  <span className={`text-[8px] font-black mb-1 ${m.risk ? 'text-[#980404]' : 'text-slate-400'}`}>{m.label}</span>
                  <span className="text-xs font-black text-slate-900">{m.val}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Shop & Ask AI Actions */}
        <section className={`px-6 mt-6 grid ${isShoppable ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
          <AnimatePresence>
            {isShoppable && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShopModalProduct(currentResult.productName)}
                className="glass p-5 rounded-[28px] flex flex-col items-center justify-center border-2 border-[#93BD57]/20 bg-[#93BD57]/5 shadow-sm"
              >
                <div className="w-10 h-10 bg-[#93BD57] text-white rounded-xl flex items-center justify-center shadow-lg mb-2">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                </div>
                <h4 className="text-[10px] font-black text-slate-900 uppercase">Shop Item</h4>
                <p className="text-[8px] font-bold text-slate-400 uppercase tracking-tighter">Order Now</p>
              </motion.button>
            )}
          </AnimatePresence>

          <motion.button
            layout
            whileTap={{ scale: 0.98 }}
            onClick={() => onAskAI(`Tell me more about ${currentResult.productName}`)}
            className={`glass p-5 rounded-[28px] flex ${isShoppable ? 'flex-col items-center justify-center' : 'flex-row items-center justify-between px-8'} border-2 border-slate-900/10 bg-slate-900/5 shadow-sm`}
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-slate-900 text-white rounded-xl flex items-center justify-center shadow-lg mb-2 sm:mb-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              </div>
              {!isShoppable && (
                <div className="text-left">
                  <h4 className="text-[10px] font-black text-slate-900 uppercase">Ask Vitalis AI</h4>
                  <p className="text-[8px] font-bold text-slate-400 uppercase tracking-tighter">Get Personalized Help</p>
                </div>
              )}
            </div>
            {isShoppable ? (
              <>
                <h4 className="text-[10px] font-black text-slate-900 uppercase">Ask AI</h4>
                <p className="text-[8px] font-bold text-slate-400 uppercase tracking-tighter">Vitalis Help</p>
              </>
            ) : (
              <div className="w-8 h-8 rounded-full bg-slate-900/10 flex items-center justify-center text-slate-900">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            )}
          </motion.button>
        </section>

        {/* Recommended Swaps (Hidden if Grade A) */}
        {currentResult.grade !== 'A' && currentResult.alternatives.length > 0 && (
          <section className="mt-10 space-y-4">
            <div className="px-6 flex justify-between items-center">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Recommended Swaps</h3>
              <span className="px-2 py-0.5 bg-[#93BD57]/10 text-[#93BD57] text-[8px] font-black rounded-md uppercase tracking-widest">Healthier</span>
            </div>
            <div className="flex gap-4 overflow-x-auto px-6 pb-6 no-scrollbar">
              {currentResult.alternatives.map((item, idx) => (
                <motion.div
                  key={idx}
                  onClick={() => handleViewSwap(item)}
                  className="flex-shrink-0 w-44 bento-card overflow-hidden bg-white shadow-lg border-2 border-[#FBE580]/30 cursor-pointer active:scale-95 transition-transform"
                >
                  {/* Grade bubble instead of image */}
                  <div className={`h-28 relative flex flex-col items-center justify-center ${getGradeColor(item.grade)}`}>
                    <span className="text-5xl font-black text-white leading-none drop-shadow-md">{item.grade}</span>
                    <span className="text-white/80 font-black text-[10px] uppercase tracking-widest mt-1">{item.score} / 100</span>
                    {/* Subtle pulse */}
                    <motion.div
                      animate={{ scale: [1, 1.12, 1], opacity: [0.3, 0.05, 0.3] }}
                      transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
                      className={`absolute inset-0 ${getGradeColor(item.grade)}`}
                    />
                  </div>
                  <div className="p-4 space-y-3">
                    <h4 className="font-black text-slate-900 text-[10px] leading-tight truncate uppercase tracking-tighter">{item.name}</h4>
                    <button
                      onClick={(e) => { e.stopPropagation(); setShopModalProduct(item.name); }}
                      className="w-full bg-slate-900 text-white text-[9px] font-black py-2 rounded-xl uppercase tracking-widest shadow-lg"
                    >
                      Shop
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#FFFDE1] via-[#FFFDE1] to-transparent z-20 flex gap-4">
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={onBack}
          className="flex-1 glass text-slate-400 font-black py-4 rounded-3xl border-2 border-[#FBE580] uppercase text-xs tracking-widest shadow-xl"
        >
          Exit
        </motion.button>
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={onReScan}
          className="flex-[2] bg-[#93BD57] text-white font-black py-4 rounded-3xl shadow-glow shadow-3d uppercase text-xs tracking-widest"
        >
          Scan Another
        </motion.button>
      </footer>

      {/* Shop Platform Modal */}
      <AnimatePresence>
        {shopModalProduct && (
          <div className="fixed inset-0 z-[100] flex items-end justify-center px-6 pb-12">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShopModalProduct(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              className="relative w-full max-w-sm bg-white rounded-[40px] p-8 space-y-6 shadow-2xl border-t-8 border-[#93BD57]"
            >
              <div className="text-center">
                <h3 className="text-xl font-black text-slate-900 uppercase tracking-tighter">Order Product</h3>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select your preferred platform</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {[
                  { name: 'Blinkit', color: 'bg-yellow-400' },
                  { name: 'BigBasket', color: 'bg-green-600' },
                  { name: 'Amazon', color: 'bg-orange-400' },
                  { name: 'Flipkart', color: 'bg-blue-500' }
                ].map(platform => (
                  <motion.button
                    key={platform.name}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => openShop(platform.name, shopModalProduct)}
                    className={`p-4 rounded-2xl flex flex-col items-center gap-2 border-2 border-slate-50 hover:border-[#93BD57] transition-all`}
                  >
                    <div className={`w-10 h-10 rounded-xl ${platform.color} shadow-lg flex items-center justify-center`}>
                      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                    </div>
                    <span className="text-[10px] font-black text-slate-700 uppercase">{platform.name}</span>
                  </motion.button>
                ))}
              </div>

              <button
                onClick={() => setShopModalProduct(null)}
                className="w-full text-slate-400 font-black text-[10px] uppercase tracking-widest py-2"
              >
                Cancel
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResultsScreen;