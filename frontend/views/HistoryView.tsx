
import React from 'react';
import { motion } from 'framer-motion';
import { HistoryItem } from '../types';

interface HistoryViewProps {
  items: HistoryItem[];
  onItemClick?: (item: HistoryItem) => void;
}

const HistoryView: React.FC<HistoryViewProps> = ({ items, onItemClick }) => {
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

  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] overflow-hidden">
      <header className="px-6 pt-12 pb-6">
        <h2 className="text-3xl font-black text-slate-900 tracking-tighter uppercase">Scan History</h2>
        <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest opacity-60">
          {items.length > 0 ? `${items.length} product${items.length === 1 ? '' : 's'} scanned` : 'Your Nutrition Journal'}
        </p>
      </header>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 space-y-4 pb-12">
        {items.length > 0 ? items.map((item, idx) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.04 }}
            onClick={() => onItemClick?.(item)}
            className="bento-card p-4 flex items-center gap-4 bg-white hover:border-[#93BD57]/30 transition-all cursor-pointer group active:scale-[0.98]"
          >
            <div className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center shadow-inner ${getGradeColor(item.grade)}`}>
              <span className="text-2xl font-black leading-none">{item.grade}</span>
              <span className="text-[8px] font-black opacity-80">{item.score}</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <h4 className="font-black text-slate-900 text-sm truncate uppercase tracking-tighter">{item.name}</h4>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{item.brand}</p>
              <p className="text-[9px] font-black text-[#93BD57] mt-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {item.timestamp}
              </p>
            </div>
            <div className="text-slate-200 group-hover:text-[#93BD57] transition-colors">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </motion.div>
        )) : (
          <div className="flex flex-col items-center justify-center py-20 text-center opacity-40">
            <svg className="w-20 h-20 text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-black uppercase tracking-widest text-slate-500">No scans yet</p>
            <p className="text-xs font-bold text-slate-400 mt-1">Scan your first product to get started</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default HistoryView;
