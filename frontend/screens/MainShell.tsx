
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProfile, Tab, HistoryItem } from '../types';
import DashboardView from '../views/DashboardView';
import HistoryView from '../views/HistoryView';
import ChatView from '../views/ChatView';

interface MainShellProps {
  profile: UserProfile;
  onScanRequest: () => void;
  onProfileRequest: () => void;
  onHistoryItemClick: (item: HistoryItem) => void;
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  scanHistory: HistoryItem[];
}

const MainShell: React.FC<MainShellProps> = ({ profile, onScanRequest, onProfileRequest, onHistoryItemClick, activeTab, setActiveTab, scanHistory }) => {

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'home':
        return (
          <DashboardView
            profile={profile}
            onScanClick={onScanRequest}
            onProfileClick={onProfileRequest}
            onAskAI={() => setActiveTab('chat')}
            onViewAllHistory={() => setActiveTab('history')}
            recentScans={scanHistory}
            onItemClick={onHistoryItemClick}
          />
        );
      case 'history':
        return <HistoryView items={scanHistory} onItemClick={onHistoryItemClick} />;
      case 'chat':
        return <ChatView profile={profile} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] relative overflow-hidden">
      <div className="flex-1 overflow-hidden relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            {renderActiveTab()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Persistent Bottom Navigation */}
      <nav className="h-20 bg-white/80 backdrop-blur-xl border-t border-[#FBE580]/30 px-6 flex items-center justify-around relative z-50 shrink-0">
        <NavButton
          active={activeTab === 'home'}
          onClick={() => setActiveTab('home')}
          icon={<HomeIcon />}
          label="Home"
        />
        <NavButton
          active={activeTab === 'history'}
          onClick={() => setActiveTab('history')}
          icon={<HistoryIcon />}
          label="History"
        />
        <NavButton
          active={activeTab === 'chat'}
          onClick={() => setActiveTab('chat')}
          icon={<ChatIcon />}
          label="Vitalis"
        />
      </nav>
    </div>
  );
};

const NavButton: React.FC<{ active: boolean; onClick: () => void; icon: React.ReactNode; label: string }> = ({ active, onClick, icon, label }) => (
  <button onClick={onClick} className="flex flex-col items-center gap-1 transition-all">
    <div className={`w-12 h-10 rounded-2xl flex items-center justify-center transition-all ${active ? 'bg-[#93BD57] text-white shadow-lg scale-110' : 'text-slate-400'}`}>
      {icon}
    </div>
    <span className={`text-[9px] font-black uppercase tracking-widest ${active ? 'text-[#93BD57]' : 'text-slate-400'}`}>
      {label}
    </span>
  </button>
);

const HomeIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const HistoryIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ChatIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

export default MainShell;
