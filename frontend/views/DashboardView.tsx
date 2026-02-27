
import React from 'react';
import { motion } from 'framer-motion';
import { UserProfile, HistoryItem } from '../types';

interface DashboardProps {
  profile: UserProfile;
  onScanClick: () => void;
  onProfileClick: () => void;
  onAskAI: () => void;
  onViewAllHistory: () => void;
  recentScans: HistoryItem[];
  onItemClick: (item: HistoryItem) => void;
}

const DashboardView: React.FC<DashboardProps> = ({ profile, onScanClick, onProfileClick, onAskAI, onViewAllHistory, recentScans, onItemClick }) => {
  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] overflow-hidden">
      <header className="px-6 pt-12 pb-4 flex justify-between items-center shrink-0">
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
          <h2 className="text-2xl font-black text-slate-900 tracking-tighter uppercase">PickBetter</h2>
        </motion.div>
        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={onProfileClick}
          className="w-12 h-12 rounded-2xl border-2 border-white shadow-lg overflow-hidden bg-[#Butter]"
        >
          <img src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${profile.name || 'User'}`} className="w-full h-full object-cover" alt="avatar" />
        </motion.button>
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 space-y-8 pb-10">
        {/* Hero Section */}
        <section className="pt-2 space-y-6">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="space-y-2"
          >
            <h1 className="text-5xl font-black text-slate-900 leading-[0.9] tracking-tight">
              KNOW WHAT <br />
              <span className="text-[#93BD57]">YOU EAT.</span>
            </h1>
            <p className="text-slate-500 font-bold text-sm tracking-wide">AI-powered labels analysis for your unique health goals.</p>
          </motion.div>

          <div className="relative">
            <motion.div
              animate={{ scale: [1, 1.05, 1], opacity: [0.2, 0.4, 0.2] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute -inset-8 bg-[#93BD57]/30 rounded-full blur-3xl pointer-events-none"
            />
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onScanClick}
              className="w-full bg-[#93BD57] py-6 rounded-[32px] shadow-glow shadow-3d flex items-center justify-center gap-4 border-t-2 border-white/20"
            >
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-xl font-black text-white uppercase tracking-tighter">Scan Product</span>
            </motion.button>
          </div>
        </section>

        {/* Recent Scans */}
        {recentScans.length > 0 && (
          <section className="space-y-4">
            <div className="flex justify-between items-end px-1">
              <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Recent Scans</h3>
              <button
                onClick={onViewAllHistory}
                className="text-[10px] font-black text-[#93BD57] uppercase hover:underline underline-offset-4"
              >
                View All
              </button>
            </div>
            <div className="flex gap-4 overflow-x-auto no-scrollbar pb-2">
              {recentScans.slice(0, 5).map((scan) => (
                <motion.div
                  key={scan.id}
                  onClick={() => onItemClick(scan)}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex-shrink-0 w-32 glass p-3 rounded-[24px] border-2 border-[#FBE580]/20 space-y-2 cursor-pointer active:scale-95 transition-transform"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-black text-white text-[10px] ${scan.grade === 'A' ? 'bg-[#93BD57]' : scan.grade === 'B' ? 'bg-[#93BD57]/70' : scan.grade === 'C' ? 'bg-[#FBE580] !text-slate-900' : scan.grade === 'D' ? 'bg-orange-500' : 'bg-[#980404]'}`}>
                    {scan.grade}
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-slate-900 truncate tracking-tight">{scan.name}</p>
                    <p className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">{scan.timestamp}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </section>
        )}

        {/* Value Props */}
        <section className="grid grid-cols-1 gap-3">
          <div className="bento-card p-5 flex items-center gap-4 bg-white/40">
            <div className="w-12 h-12 bg-[#93BD57]/10 rounded-2xl flex items-center justify-center text-[#93BD57]">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <div>
              <h4 className="text-[11px] font-black text-slate-900 uppercase tracking-tight">Health Score</h4>
              <p className="text-[10px] font-bold text-slate-500 leading-tight">Evaluation of the product based on nutritional density and your profile.</p>
            </div>
          </div>
          <div className="bento-card p-5 flex items-center gap-4 bg-white/40">
            <div className="w-12 h-12 bg-[#980404]/10 rounded-2xl flex items-center justify-center text-[#980404]">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            </div>
            <div>
              <h4 className="text-[11px] font-black text-slate-900 uppercase tracking-tight">Personal Alerts</h4>
              <p className="text-[10px] font-bold text-slate-500 leading-tight">Instant warnings for hidden allergens and harmful additives.</p>
            </div>
          </div>
          <div className="bento-card p-5 flex items-center gap-4 bg-white/40">
            <div className="w-12 h-12 bg-[#FBE580]/20 rounded-2xl flex items-center justify-center text-[#FBE580]">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-7.714 2.143L11 21l-2.286-6.857L1 12l7.714-2.143L11 3z" /></svg>
            </div>
            <div>
              <h4 className="text-[11px] font-black text-slate-900 uppercase tracking-tight">Smarter Swaps</h4>
              <p className="text-[10px] font-bold text-slate-500 leading-tight">Discover healthier alternatives tailored to your unique diet.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardView;
