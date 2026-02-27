
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProfile, HealthCondition } from '../types';

const CONDITIONS: HealthCondition[] = [
  { id: 'diabetes', label: 'Diabetes', icon: 'sugar' },
  { id: 'hypertension', label: 'High BP', icon: 'heart' },
  { id: 'cholesterol', label: 'Cholesterol', icon: 'shield' },
  { id: 'pcos', label: 'PCOS', icon: 'sparkle' },
];

const ALLERGENS: HealthCondition[] = [
  { id: 'peanuts', label: 'Peanuts', icon: 'nut' },
  { id: 'gluten', label: 'Gluten', icon: 'grain' },
  { id: 'dairy', label: 'Dairy', icon: 'milk' },
  { id: 'shellfish', label: 'Shellfish', icon: 'shell' },
];

const Icon = ({ name, className = "w-8 h-8" }: { name: string, className?: string }) => {
  switch (name) {
    case 'sugar': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.61.285a2 2 0 01-1.096.218l-1.503-.131a2 2 0 00-1.13.188l-1.612.806a2 2 0 01-1.92 0l-1.612-.806a2 2 0 00-1.13-.188l-1.503.131a2 2 0 01-1.096-.218l-.61-.285a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547l-.271.271a2 2 0 000 2.828l2.121 2.121a2 2 0 002.828 0l2.121-2.121z" /></svg>;
    case 'heart': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>;
    case 'shield': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>;
    case 'sparkle': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-7.714 2.143L11 21l-2.286-6.857L1 12l7.714-2.143L11 3z" /></svg>;
    case 'nut': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>;
    case 'grain': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 002 2h1.5a3 3 0 013 3V16.5a1.5 1.5 0 00.332.964L20.25 19.5" /></svg>;
    case 'milk': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.61.285a2 2 0 01-1.096.218l-1.503-.131a2 2 0 00-1.13.188l-1.612.806a2 2 0 01-1.92 0l-1.612-.806a2 2 0 00-1.13-.188l-1.503.131a2 2 0 01-1.096-.218l-.61-.285a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547l-.271.271a2 2 0 000 2.828l2.121 2.121a2 2 0 002.828 0l2.121-2.121z" /></svg>;
    case 'shell': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>;
    case 'others': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>;
    case 'rocket': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464L19.07 5M5 19.071L8.536 15.536M11.607 11.607L15.143 8.071M8.071 15.143L4.536 18.678" /></svg>;
    case 'magnifier': return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>;
    default: return null;
  }
};

interface OnboardingProps {
  profile: UserProfile;
  setProfile: React.Dispatch<React.SetStateAction<UserProfile>>;
  onComplete: () => void;
}

const OnboardingScreen: React.FC<OnboardingProps> = ({ profile, setProfile, onComplete }) => {
  const [step, setStep] = useState(1);
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const [customValue, setCustomValue] = useState('');

  const toggleItem = (listName: 'conditions' | 'allergens', label: string) => {
    setProfile(prev => {
      const currentList = prev[listName];
      const newList = currentList.includes(label) 
        ? currentList.filter(i => i !== label) 
        : [...currentList, label];
      return { ...prev, [listName]: newList };
    });
  };

  const handleAddCustom = (listName: 'conditions' | 'allergens') => {
    if (!customValue.trim()) return;
    
    const value = customValue.trim();
    toggleItem(listName, value);
    setCustomValue('');
    setShowOtherInput(false);
    setShowPopup(true);
    
    setTimeout(() => setShowPopup(false), 3000);
  };

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
      setShowOtherInput(false);
    } else {
      onComplete();
    }
  };

  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <div className="space-y-6">
            <header className="space-y-2">
              <h2 className="text-3xl font-black text-slate-900 leading-tight">Any <span className="text-[#93BD57]">Allergies?</span></h2>
              <p className="text-slate-500 font-bold">We'll scan labels for these specifically. <Icon name="shield" className="w-5 h-5 inline-block text-[#93BD57]" /></p>
            </header>
            <div className="grid grid-cols-2 gap-4">
              {ALLERGENS.map(a => (
                <button
                  key={a.id}
                  onClick={() => toggleItem('allergens', a.label)}
                  className={`p-6 rounded-3xl flex flex-col items-center gap-3 transition-all ${
                    profile.allergens.includes(a.label) 
                    ? 'bg-[#93BD57] text-white border-[#93BD57] shadow-lg scale-[1.02]' 
                    : 'bg-white text-slate-600 border-[#FBE580]'
                  } border-2`}
                >
                  <Icon name={a.icon} className="w-10 h-10" />
                  <span className="font-bold">{a.label}</span>
                </button>
              ))}
              <button
                onClick={() => setShowOtherInput(!showOtherInput)}
                className={`p-6 rounded-3xl bg-white border-2 border-dashed border-[#FBE580] flex flex-col items-center gap-3 text-slate-400 transition-all ${showOtherInput ? 'bg-[#FFFDE1] border-[#93BD57]' : ''}`}
              >
                <Icon name="others" className="w-10 h-10" />
                <span className="font-bold">Others</span>
              </button>
            </div>
            <AnimatePresence>
              {showOtherInput && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-white p-4 rounded-3xl border-2 border-[#93BD57] shadow-sm flex items-center gap-3"
                >
                  <input
                    autoFocus
                    value={customValue}
                    onChange={(e) => setCustomValue(e.target.value)}
                    placeholder="E.g. Soy, Walnuts..."
                    className="flex-1 bg-transparent text-slate-900 outline-none font-bold placeholder:text-slate-300"
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCustom('allergens')}
                  />
                  <button 
                    onClick={() => handleAddCustom('allergens')}
                    className="bg-[#93BD57] text-white px-4 py-2 rounded-xl font-black text-xs uppercase"
                  >
                    Add
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <header className="space-y-2">
              <h2 className="text-3xl font-black text-slate-900 leading-tight">Your <span className="text-[#93BD57]">Health Profile?</span></h2>
              <p className="text-slate-500 font-bold">Help us calculate your perfect grade. <Icon name="sparkle" className="w-5 h-5 inline-block text-[#93BD57]" /></p>
            </header>
            <div className="grid grid-cols-2 gap-4">
              {CONDITIONS.map(c => (
                <button
                  key={c.id}
                  onClick={() => toggleItem('conditions', c.label)}
                  className={`p-6 rounded-3xl flex flex-col items-center gap-3 transition-all ${
                    profile.conditions.includes(c.label) 
                    ? 'bg-[#93BD57] text-white border-[#93BD57] shadow-lg scale-[1.02]' 
                    : 'bg-white text-slate-600 border-[#FBE580]'
                  } border-2`}
                >
                  <Icon name={c.icon} className="w-10 h-10" />
                  <span className="font-bold">{c.label}</span>
                </button>
              ))}
              <button
                onClick={() => setShowOtherInput(!showOtherInput)}
                className={`p-6 rounded-3xl bg-white border-2 border-dashed border-[#FBE580] flex flex-col items-center gap-3 text-slate-400 transition-all ${showOtherInput ? 'bg-[#FFFDE1] border-[#93BD57]' : ''}`}
              >
                <Icon name="others" className="w-10 h-10" />
                <span className="font-bold">Others</span>
              </button>
            </div>
            <AnimatePresence>
              {showOtherInput && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-white p-4 rounded-3xl border-2 border-[#93BD57] shadow-sm flex items-center gap-3"
                >
                  <input
                    autoFocus
                    value={customValue}
                    onChange={(e) => setCustomValue(e.target.value)}
                    placeholder="E.g. Thyroid, Low Salt..."
                    className="flex-1 bg-transparent text-slate-900 outline-none font-bold placeholder:text-slate-300"
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCustom('conditions')}
                  />
                  <button 
                    onClick={() => handleAddCustom('conditions')}
                    className="bg-[#93BD57] text-white px-4 py-2 rounded-xl font-black text-xs uppercase"
                  >
                    Add
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      case 3:
        return (
          <div className="space-y-8 flex flex-col items-center pt-8">
            <motion.div 
              initial={{ scale: 0, rotate: -20 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="w-40 h-40 bg-[#FBE580] rounded-full flex items-center justify-center text-6xl shadow-xl relative"
            >
              <Icon name="rocket" className="w-20 h-20 text-[#93BD57]" />
              <div className="absolute -top-2 -right-2 bg-[#93BD57] text-white p-2 rounded-full shadow-lg">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            </motion.div>
            <div className="text-center">
              <h2 className="text-4xl font-black mb-2 text-slate-900 tracking-tighter uppercase">PickBetter Ready!</h2>
              <p className="text-slate-500 font-bold px-4">Your personalized AI engine is now tailored just for you.</p>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full px-6 pt-16 pb-12 justify-between bg-[#FFFDE1] relative overflow-hidden">
      <AnimatePresence>
        {showPopup && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 20, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            className="absolute top-0 left-6 right-6 z-[100] bg-white border-4 border-[#FBE580] rounded-[24px] p-5 shadow-2xl flex flex-col items-start gap-1"
          >
            <h4 className="font-black text-[#93BD57] text-sm uppercase tracking-tight">Noted!</h4>
            <div className="flex items-center gap-2">
              <p className="text-slate-600 text-[11px] leading-snug font-bold flex-1">
                Our food detectives are on the case! We'll learn this flavor just for you.
              </p>
              <Icon name="magnifier" className="w-5 h-5 text-[#93BD57]" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex gap-2 mb-8 relative z-10">
        {[1, 2, 3].map(i => (
          <div key={i} className={`h-2.5 flex-1 rounded-full transition-all duration-700 ${i <= step ? 'bg-[#93BD57]' : 'bg-[#FBE580]/40'}`} />
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ x: 40, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -40, opacity: 0 }}
          className="flex-1 overflow-y-auto no-scrollbar relative z-10"
        >
          {renderStep()}
        </motion.div>
      </AnimatePresence>

      <div className="relative z-10 mt-8 space-y-4">
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={handleNext}
          className="w-full bg-[#93BD57] text-white font-black py-6 rounded-[32px] text-xl shadow-glow uppercase tracking-tighter border-b-8 border-[#7ea34a]"
        >
          {step === 3 ? "Start Scanning" : "Next Step"}
        </motion.button>
        {step < 3 && (
          <p className="text-center text-slate-400 font-bold text-[10px] uppercase tracking-widest">
            Step {step} of 3
          </p>
        )}
      </div>
    </div>
  );
};

export default OnboardingScreen;
