
import React from 'react';
import { motion } from 'framer-motion';
import { UserProfile } from '../types';

interface HomeProps {
  profile: UserProfile;
  onScanClick: () => void;
  onProfileClick: () => void;
}

const HomeScreen: React.FC<HomeProps> = ({ profile, onScanClick, onProfileClick }) => {
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  const getHealthIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('bp') || t.includes('hypertension')) return '❤️';
    if (t.includes('diabetes') || t.includes('sugar')) return '🍬';
    if (t.includes('nut') || t.includes('peanut')) return '🥜';
    if (t.includes('cholesterol')) return '🥓';
    if (t.includes('pcos')) return '🌸';
    return '✨';
  };

  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] overflow-hidden">
      {/* Header Section */}
      <header className="px-6 pt-12 pb-6 flex justify-between items-start">
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
          <p className="text-slate-500 text-sm font-bold uppercase tracking-widest opacity-60">Good Day,</p>
          <h1 className="text-3xl font-black text-slate-900 tracking-tighter">
            {profile.name || 'Explorer'} ✨
          </h1>
        </motion.div>
        <motion.button 
          whileTap={{ scale: 0.9 }}
          onClick={onProfileClick}
          initial={{ scale: 0 }} 
          animate={{ scale: 1 }}
          className="w-14 h-14 rounded-3xl border-4 border-white shadow-xl overflow-hidden bg-[#FBE580] relative"
        >
          <img src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${profile.name || 'User'}`} className="w-full h-full object-cover" alt="avatar" />
        </motion.button>
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 space-y-8 pb-40">
        {/* Quick Stats Bento */}
        <motion.div variants={itemVariants} initial="hidden" animate="visible" className="bento-card p-6 flex justify-between items-center bg-white/60">
          <div>
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Health Streak</h4>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-black text-slate-900">12</span>
              <span className="text-sm font-bold text-[#93BD57]">DAYS 🔥</span>
            </div>
          </div>
          <div className="flex -space-x-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="w-8 h-8 rounded-full border-2 border-white bg-[#93BD57] flex items-center justify-center text-[10px] text-white font-bold">
                {i}
              </div>
            ))}
            <div className="w-8 h-8 rounded-full border-2 border-white bg-slate-100 flex items-center justify-center text-[10px] text-slate-400 font-bold">
              +
            </div>
          </div>
        </motion.div>

        {/* Personal Profile Bar (Active Filters) */}
        <div className="space-y-3">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-1 flex items-center gap-2">
            <span className="w-4 h-[1px] bg-slate-200"></span>
            Your Filters
            <span className="w-4 h-[1px] bg-slate-200"></span>
          </h3>
          <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2">
            {profile.allergens.map(a => (
              <motion.div key={a} whileTap={{ scale: 0.95 }} className="flex-shrink-0 px-4 py-3 rounded-2xl bg-white border-2 border-[#980404]/20 flex items-center gap-2 shadow-sm">
                <span className="text-xl">🥜</span>
                <span className="text-xs font-black text-[#980404] uppercase">{a}</span>
              </motion.div>
            ))}
            {profile.conditions.map(c => (
              <motion.div key={c} whileTap={{ scale: 0.95 }} className="flex-shrink-0 px-4 py-3 rounded-2xl bg-white border-2 border-[#93BD57]/20 flex items-center gap-2 shadow-sm">
                <span className="text-xl">{getHealthIcon(c)}</span>
                <span className="text-xs font-black text-[#93BD57] uppercase">{c}</span>
              </motion.div>
            ))}
            {(profile.conditions.length === 0 && profile.allergens.length === 0) && (
              <div className="px-6 py-4 rounded-3xl bg-white/40 border-2 border-dashed border-slate-200 text-slate-400 text-xs font-bold italic w-full text-center">
                Tell us about your health to get insights!
              </div>
            )}
          </div>
        </div>

        {/* Idle State / Illustration */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center py-6 text-center space-y-4"
        >
          <div className="w-48 h-48 bg-white/30 rounded-full flex items-center justify-center relative">
            <motion.div 
              animate={{ rotate: 360 }} 
              transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
              className="absolute inset-0 border-2 border-dashed border-[#FBE580]/50 rounded-full"
            />
            <span className="text-8xl animate-bounce">🍎</span>
          </div>
          <div className="space-y-1">
            <h2 className="text-2xl font-black text-slate-900 uppercase tracking-tighter">Scan a snack!</h2>
            <p className="text-slate-500 font-bold text-xs max-w-[200px] mx-auto">Discover secrets hidden behind every label.</p>
          </div>
        </motion.div>

        {/* Community Scan Feed */}
        <div className="space-y-4">
          <div className="flex justify-between items-center px-1">
            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Community Discovery</h3>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-[#93BD57] rounded-full animate-pulse shadow-[0_0_8px_#93BD57]" />
              <span className="text-[10px] font-black text-[#93BD57] uppercase">Live Swaps</span>
            </span>
          </div>
          <div className="space-y-3">
            {[
              { text: "Rohan swapped Lays for Baked Makhana!", icon: "🍿", time: "Just now" },
              { text: "Priya found a low-sodium biscuit alternative.", icon: "🍪", time: "4m ago" },
              { text: "Karan avoided Dairy in his protein shake scan.", icon: "🥛", time: "11m ago" },
            ].map((feed, idx) => (
              <motion.div 
                key={idx} 
                initial={{ x: -20, opacity: 0 }} 
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.2 + idx * 0.1 }}
                className="glass p-4 rounded-3xl flex items-center gap-4"
              >
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-2xl shadow-sm">
                  {feed.icon}
                </div>
                <div className="flex-1">
                  <p className="text-[12px] font-bold text-slate-700 leading-tight">{feed.text}</p>
                  <p className="text-[9px] font-black text-slate-400 uppercase mt-1 tracking-wider">{feed.time}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </main>

      {/* Massive Glowing Scan FAB */}
      <div className="fixed bottom-10 left-0 right-0 px-8 z-50 flex justify-center">
        <motion.button
          whileHover={{ scale: 1.05, y: -5 }}
          whileTap={{ scale: 0.95, y: 5 }}
          onClick={onScanClick}
          className="w-full max-w-xs group bg-[#93BD57] py-6 rounded-[40px] shadow-glow shadow-3d flex items-center justify-center gap-4 border-t-2 border-white/20 overflow-hidden relative"
        >
          <motion.div 
            initial={{ x: '-100%' }}
            animate={{ x: '250%' }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="absolute top-0 bottom-0 w-32 bg-white/20 skew-x-[35deg]"
          />
          <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-lg transform group-hover:rotate-12 transition-transform">
            <svg className="w-7 h-7 text-[#93BD57]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
            </svg>
          </div>
          <span className="text-xl font-black text-white uppercase tracking-tighter drop-shadow-sm">Scan Barcode</span>
        </motion.button>
      </div>
    </div>
  );
};

export default HomeScreen;
