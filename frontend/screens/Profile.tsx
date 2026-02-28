
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProfile } from '../types';
import { useAuth } from '../src/contexts/AuthContext';

interface ProfileProps {
  profile: UserProfile;
  setProfile: React.Dispatch<React.SetStateAction<UserProfile>>;
  onBack: () => void;
  onSignOut: () => void;
}

const ALLERGEN_OPTIONS = [
  "Peanuts",
  "Tree Nuts (Cashews, Almonds, Walnuts)",
  "Milk/Dairy",
  "Wheat/Gluten",
  "Mustard",
  "Soy",
  "Egg",
  "Sesame",
  "Shellfish/Fish"
];

const CONDITION_OPTIONS = [
  "Diabetes / Prediabetes",
  "Hypertension (High BP)",
  "PCOS / PCOD",
  "High Cholesterol",
  "Celiac Disease",
  "IBS / Sensitive Gut"
];
const DIET_TYPES = ["Vegan", "Vegetarian", "Keto", "Paleo", "General", "Mediterranean", "Low Carb"];
const GOALS = ["Weight Loss", "Muscle Gain", "Heart Health", "General Wellness", "Sugar Control"];

const ProfileScreen: React.FC<ProfileProps> = ({ profile, setProfile, onBack, onSignOut }) => {
  const { signOut } = useAuth();
  const [activeTab, setActiveTab] = useState<'essentials' | 'health' | 'lifestyle'>('essentials');
  const [showOtherAllergen, setShowOtherAllergen] = useState(false);
  const [showOtherCondition, setShowOtherCondition] = useState(false);
  const [customAllergen, setCustomAllergen] = useState('');
  const [customCondition, setCustomCondition] = useState('');
  const [showCustomPopup, setShowCustomPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState('');

  const updateProfile = (field: keyof UserProfile, value: any) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const toggleTag = (field: 'allergens' | 'conditions', tag: string) => {
    const current = profile[field];
    if (current.includes(tag)) {
      updateProfile(field, current.filter(t => t !== tag));
    } else {
      updateProfile(field, [...current, tag]);
    }
  };

  const handleAddCustomAllergen = () => {
    if (!customAllergen.trim()) return;

    const value = customAllergen.trim();
    toggleTag('allergens', value);
    setCustomAllergen('');
    setShowOtherAllergen(false);
    setPopupMessage(`We've noted your unique requirement! 📝 Our team is currently studying the nutritional markers for ${value}. We will update your profile and notify you once we can provide accurate flags for this condition.`);
    setShowCustomPopup(true);
    setTimeout(() => setShowCustomPopup(false), 4000);
  };

  const handleAddCustomCondition = () => {
    if (!customCondition.trim()) return;

    const value = customCondition.trim();
    toggleTag('conditions', value);
    setCustomCondition('');
    setShowOtherCondition(false);
    setPopupMessage(`We've noted your unique requirement! 📝 Our team is currently studying the nutritional markers for ${value}. We will update your profile and notify you once we can provide accurate flags for this condition.`);
    setShowCustomPopup(true);
    setTimeout(() => setShowCustomPopup(false), 4000);
  };

  const handleSave = async () => {
    console.log("Saving Profile Payload:", JSON.stringify(profile, null, 2));

    // Prepare custom_needs from any non-standard allergens/conditions
    const customNeeds = [];

    // Check for custom allergens (not in the standard list)
    const standardAllergens = new Set(ALLERGEN_OPTIONS);
    profile.allergens.forEach(allergen => {
      if (!standardAllergens.has(allergen)) {
        customNeeds.push(`Allergen: ${allergen}`);
      }
    });

    // Check for custom conditions (not in the standard list)
    const standardConditions = new Set(CONDITION_OPTIONS);
    profile.conditions.forEach(condition => {
      if (!standardConditions.has(condition)) {
        customNeeds.push(`Condition: ${condition}`);
      }
    });

    // Prepare profile data for backend
    const profileData = {
      user_id: 'user_123', // TODO: Get actual user ID from auth
      name: profile.name,
      age: profile.age ? parseInt(profile.age) : undefined,
      sex: profile.sex,
      height: profile.height ? parseInt(profile.height) : undefined,
      weight: profile.weight ? parseInt(profile.weight) : undefined,
      allergens: profile.allergens,
      health_conditions: profile.conditions,
      custom_needs: customNeeds.length > 0 ? customNeeds : undefined,
      custom_needs_status: customNeeds.length > 0 ? 'pending_review' : undefined,
      diet_type: profile.dietType,
      primary_goal: profile.primaryGoal
    };

    // Filter out undefined values
    Object.keys(profileData).forEach(key => {
      if (profileData[key] === undefined) {
        delete profileData[key];
      }
    });

    try {
      console.log("Sending to backend:", JSON.stringify(profileData, null, 2));

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/user/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Profile saved successfully:", result);

      // Update local state with any backend changes
      setProfile(prev => ({
        ...prev,
        custom_needs: result.custom_needs || prev.custom_needs,
        custom_needs_status: result.custom_needs_status || prev.custom_needs_status
      }));

    } catch (error) {
      console.error("Failed to save profile:", error);
      // Still allow navigation even if save fails
    }

    onBack();
  };

  const handleOtherClick = (type: 'allergens' | 'conditions') => {
    if (type === 'allergens') {
      setShowOtherAllergen(!showOtherAllergen);
      setShowOtherCondition(false);
    } else {
      setShowOtherCondition(!showOtherCondition);
      setShowOtherAllergen(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      console.log('✅ Signed out successfully');
      onSignOut();
    } catch (error) {
      console.error('❌ Sign out failed:', error);
    }
  };

  return (
    <div className="h-full bg-[#FFFDE1] flex flex-col relative overflow-hidden">
      {/* Header with Sign Out */}
      <div className="relative z-10 p-6 pt-12">
        <div className="flex items-center justify-between mb-6">
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onBack}
            className="w-12 h-12 glass rounded-2xl flex items-center justify-center border border-white/20"
          >
            <svg className="w-6 h-6 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 19l-7-7 7-7" />
            </svg>
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleSignOut}
            className="px-4 py-2 bg-red-500 text-white font-bold rounded-full text-sm uppercase tracking-tighter"
          >
            Sign Out
          </motion.button>
        </div>
        <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">My Profile</h2>
      </div>

      {/* Custom Needs Popup */}
      <AnimatePresence>
        {showCustomPopup && (
          <motion.div
            initial={{ y: -60, opacity: 0 }}
            animate={{ y: 20, opacity: 1 }}
            exit={{ y: -60, opacity: 0 }}
            className="absolute top-0 left-6 right-6 z-[100] bg-white border-4 border-[#FBE580] rounded-[24px] p-5 shadow-2xl flex flex-col items-start gap-1"
          >
            <h4 className="font-black text-[#93BD57] text-sm uppercase tracking-tight">Noted!</h4>
            <div className="flex items-center gap-2">
              <p className="text-slate-600 text-[11px] leading-snug font-bold flex-1">
                {popupMessage}
              </p>
              <svg className="w-5 h-5 text-[#93BD57]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tabs */}
      <div className="px-6 py-2 flex gap-2">
        {(['essentials', 'health', 'lifestyle'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === tab
              ? 'bg-[#93BD57] text-white shadow-md'
              : 'bg-white text-slate-400 border border-slate-100'
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 py-4 pb-24">
        <AnimatePresence mode="wait">
          {activeTab === 'essentials' && (
            <motion.div
              key="essentials"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="bento-card p-6 bg-white/60 space-y-4">
                <h3 className="text-[10px] font-black text-[#93BD57] uppercase tracking-widest">Basic Information</h3>

                <div className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-[10px] font-black text-slate-400 uppercase ml-1">Full Name</label>
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => updateProfile('name', e.target.value)}
                      placeholder="e.g. Rahul Sharma"
                      className="w-full bg-white border border-slate-100 rounded-2xl py-4 px-5 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-black text-slate-400 uppercase ml-1">Age</label>
                      <input
                        type="number"
                        value={profile.age}
                        onChange={(e) => updateProfile('age', e.target.value)}
                        placeholder="25"
                        className="w-full bg-white border border-slate-100 rounded-2xl py-4 px-5 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-black text-slate-400 uppercase ml-1">Sex</label>
                      <select
                        value={profile.sex}
                        onChange={(e) => updateProfile('sex', e.target.value)}
                        className="w-full bg-white border border-slate-100 rounded-2xl py-4 px-5 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all appearance-none"
                      >
                        <option>Male</option>
                        <option>Female</option>
                        <option>Other</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-black text-slate-400 uppercase ml-1">Height (cm)</label>
                      <input
                        type="number"
                        value={profile.height}
                        onChange={(e) => updateProfile('height', e.target.value)}
                        placeholder="175"
                        className="w-full bg-white border border-slate-100 rounded-2xl py-4 px-5 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-black text-slate-400 uppercase ml-1">Weight (kg)</label>
                      <input
                        type="number"
                        value={profile.weight}
                        onChange={(e) => updateProfile('weight', e.target.value)}
                        placeholder="70"
                        className="w-full bg-white border border-slate-100 rounded-2xl py-4 px-5 text-slate-900 font-bold focus:outline-none focus:border-[#93BD57] transition-all"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'health' && (
            <motion.div
              key="health"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              {/* Allergens Section */}
              <div className="bento-card p-6 bg-white/60 space-y-4">
                <h3 className="text-[10px] font-black text-[#980404] uppercase tracking-widest">Safety: Allergens</h3>

                <div className="grid grid-cols-2 gap-3">
                  {ALLERGEN_OPTIONS.map(allergen => (
                    <button
                      key={allergen}
                      onClick={() => toggleTag('allergens', allergen)}
                      className={`p-4 rounded-2xl text-left transition-all ${profile.allergens.includes(allergen)
                        ? 'bg-[#980404] text-white border-[#980404] shadow-lg scale-[1.02]'
                        : 'bg-white text-slate-600 border-slate-200'
                        } border-2`}
                    >
                      <span className="font-bold text-sm">{allergen}</span>
                    </button>
                  ))}
                  <button
                    onClick={() => handleOtherClick('allergens')}
                    className={`p-4 rounded-2xl bg-white border-2 border-dashed border-slate-200 flex flex-col items-center justify-center gap-2 text-slate-400 transition-all ${showOtherAllergen ? 'bg-[#FFFDE1] border-[#980404]' : ''}`}
                  >
                    <span className="font-bold text-sm">Other</span>
                  </button>
                </div>

                <AnimatePresence>
                  {showOtherAllergen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-white p-4 rounded-2xl border-2 border-[#980404] shadow-sm flex items-center gap-3"
                    >
                      <input
                        autoFocus
                        value={customAllergen}
                        onChange={(e) => setCustomAllergen(e.target.value)}
                        placeholder="E.g. Kiwi, Mustard..."
                        className="flex-1 bg-transparent text-slate-900 outline-none font-bold placeholder:text-slate-300"
                        onKeyDown={(e) => e.key === 'Enter' && handleAddCustomAllergen()}
                      />
                      <button
                        onClick={handleAddCustomAllergen}
                        className="bg-[#980404] text-white px-4 py-2 rounded-xl font-black text-xs uppercase"
                      >
                        Add
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="flex flex-wrap gap-2">
                  {profile.allergens.map(tag => (
                    <motion.button
                      layout
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      key={tag}
                      onClick={() => toggleTag('allergens', tag)}
                      className="bg-[#980404] text-white px-3 py-1.5 rounded-full text-[10px] font-black uppercase flex items-center gap-2 shadow-sm"
                    >
                      {tag}
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </motion.button>
                  ))}
                  {profile.allergens.length === 0 && (
                    <p className="text-slate-400 text-[10px] font-medium italic">No allergens selected.</p>
                  )}
                </div>
              </div>

              {/* Conditions Section */}
              <div className="bento-card p-6 bg-white/60 space-y-4">
                <h3 className="text-[10px] font-black text-[#93BD57] uppercase tracking-widest">Health Conditions</h3>

                <div className="grid grid-cols-2 gap-3">
                  {CONDITION_OPTIONS.map(condition => (
                    <button
                      key={condition}
                      onClick={() => toggleTag('conditions', condition)}
                      className={`p-4 rounded-2xl text-left transition-all ${profile.conditions.includes(condition)
                        ? 'bg-[#93BD57] text-white border-[#93BD57] shadow-lg scale-[1.02]'
                        : 'bg-white text-slate-600 border-slate-200'
                        } border-2`}
                    >
                      <span className="font-bold text-sm">{condition}</span>
                    </button>
                  ))}
                  <button
                    onClick={() => handleOtherClick('conditions')}
                    className={`p-4 rounded-2xl bg-white border-2 border-dashed border-slate-200 flex flex-col items-center justify-center gap-2 text-slate-400 transition-all ${showOtherCondition ? 'bg-[#FFFDE1] border-[#93BD57]' : ''}`}
                  >
                    <span className="font-bold text-sm">Other</span>
                  </button>
                </div>

                <AnimatePresence>
                  {showOtherCondition && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-white p-4 rounded-2xl border-2 border-[#93BD57] shadow-sm flex items-center gap-3"
                    >
                      <input
                        autoFocus
                        value={customCondition}
                        onChange={(e) => setCustomCondition(e.target.value)}
                        placeholder="E.g. Thyroid, Low Salt..."
                        className="flex-1 bg-transparent text-slate-900 outline-none font-bold placeholder:text-slate-300"
                        onKeyDown={(e) => e.key === 'Enter' && handleAddCustomCondition()}
                      />
                      <button
                        onClick={handleAddCustomCondition}
                        className="bg-[#93BD57] text-white px-4 py-2 rounded-xl font-black text-xs uppercase"
                      >
                        Add
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="flex flex-wrap gap-2">
                  {profile.conditions.map(tag => (
                    <motion.button
                      layout
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      key={tag}
                      onClick={() => toggleTag('conditions', tag)}
                      className="bg-[#93BD57] text-white px-3 py-1.5 rounded-full text-[10px] font-black uppercase flex items-center gap-2 shadow-sm"
                    >
                      {tag}
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </motion.button>
                  ))}
                  {profile.conditions.length === 0 && (
                    <p className="text-slate-400 text-[10px] font-medium italic">No chronic conditions added.</p>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'lifestyle' && (
            <motion.div
              key="lifestyle"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="bento-card p-6 bg-white/60 space-y-6">
                <div className="space-y-3">
                  <h3 className="text-[10px] font-black text-[#93BD57] uppercase tracking-widest">Dietary Preference</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {DIET_TYPES.map(type => (
                      <button
                        key={type}
                        onClick={() => updateProfile('dietType', type)}
                        className={`py-3 px-4 rounded-2xl text-[10px] font-black uppercase transition-all ${profile.dietType === type
                          ? 'bg-[#93BD57] text-white shadow-md scale-[1.02]'
                          : 'bg-white text-slate-400 border border-slate-100'
                          }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-[10px] font-black text-[#93BD57] uppercase tracking-widest">Primary Health Goal</h3>
                  <div className="flex flex-col gap-2">
                    {GOALS.map(goal => (
                      <button
                        key={goal}
                        onClick={() => updateProfile('primaryGoal', goal)}
                        className={`py-4 px-6 rounded-2xl text-[11px] font-black uppercase text-left transition-all flex justify-between items-center ${profile.primaryGoal === goal
                          ? 'bg-slate-900 text-white shadow-xl scale-[1.02]'
                          : 'bg-white text-slate-500 border border-slate-100'
                          }`}
                      >
                        {goal}
                        {profile.primaryGoal === goal && (
                          <svg className="w-5 h-5 text-[#93BD57]" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Floating Save Button */}
      <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[#FFFDE1] to-transparent">
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={handleSave}
          className="w-full bg-[#93BD57] text-white font-black py-5 rounded-[32px] text-lg shadow-glow shadow-3d uppercase tracking-tighter"
        >
          Save Profile
        </motion.button>
      </div>
    </div>
  );
};

export default ProfileScreen;
