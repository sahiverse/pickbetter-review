import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ScanResult {
  original_product: any;
  gemini_analysis: {
    grade: string;
    score: number;
    reasoning: string;
    health_concerns: string[];
    positive_aspects: string[];
    recommendations: string[];
  };
  recommendations: Array<{
    product: any;
    analysis: any;
    personalized_recommendation?: string;
    image_url?: string;
    reasoning?: string;
  }>;
  message: string;
  user_context: string;
}

interface ScanResultsScreenProps {
  result: ScanResult;
  onBack: () => void;
  onRescan: () => void;
}

const ScanResultsScreen: React.FC<ScanResultsScreenProps> = ({ result, onBack, onRescan }) => {
  const { original_product, gemini_analysis, recommendations, message, user_context } = result;

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return '#22c55e'; // green
      case 'B': return '#3b82f6'; // blue
      case 'C': return '#f59e0b'; // yellow
      case 'D': return '#f97316'; // orange
      case 'F': return '#ef4444'; // red
      default: return '#6b7280'; // gray
    }
  };

  const getGradeEmoji = (grade: string) => {
    switch (grade) {
      case 'A': return '🥇';
      case 'B': return '🥈';
      case 'C': return '🥉';
      case 'D': return '⚠️';
      case 'F': return '🚫';
      default: return '🤔';
    }
  };

  return (
    <div className="h-full bg-[#FFFDE1] relative overflow-hidden">
      {/* Header */}
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

          <div className="text-center">
            <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">Analysis Results</h2>
            <p className="text-[10px] font-medium text-slate-500 uppercase tracking-widest mt-1">
              Gemini AI Health Analysis
            </p>
          </div>

          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={onRescan}
            className="w-12 h-12 glass rounded-2xl flex items-center justify-center border border-white/20"
          >
            <svg className="w-6 h-6 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </motion.button>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto no-scrollbar px-6 pb-24">
        {/* Original Product Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >

          {/* Product Header */}
          <div className="bento-card p-6 bg-white/60">
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <h3 className="text-lg font-black text-slate-900 mb-2">
                  {original_product.name}
                </h3>
                <p className="text-slate-600 font-medium mb-3">
                  {original_product.brand}
                </p>

                {/* Health Grade */}
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-black"
                    style={{ backgroundColor: getGradeColor(gemini_analysis.grade) }}
                  >
                    {gemini_analysis.grade}
                  </div>
                  <div>
                    <p className="text-2xl font-black text-slate-900">
                      {getGradeEmoji(gemini_analysis.grade)} Grade {gemini_analysis.grade}
                    </p>
                    <p className="text-slate-600 font-medium">
                      Score: {gemini_analysis.score}/100
                    </p>
                  </div>
                </div>

                <p className="text-slate-700 text-sm leading-relaxed">
                  {gemini_analysis.reasoning}
                </p>
              </div>

              {original_product.image_url && (
                <img
                  src={original_product.image_url}
                  alt={original_product.name}
                  className="w-24 h-24 object-cover rounded-2xl shadow-md"
                />
              )}
            </div>
          </div>

          {/* Message */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bento-card p-6"
            style={{
              backgroundColor: gemini_analysis.grade <= 'C' ? '#fef3c7' : '#d1fae5',
              borderColor: gemini_analysis.grade <= 'C' ? '#f59e0b' : '#10b981'
            }}
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl">
                {gemini_analysis.grade <= 'C' ? '💡' : '✅'}
              </div>
              <div>
                <h4 className="font-black text-slate-900 text-sm uppercase mb-1">
                  {gemini_analysis.grade <= 'C' ? 'Consider Alternatives' : 'Great Choice!'}
                </h4>
                <p className="text-slate-700 text-sm">
                  {message}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Health Concerns */}
          {gemini_analysis.health_concerns.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bento-card p-6 bg-red-50 border-red-200"
            >
              <h4 className="font-black text-red-900 text-sm uppercase mb-3 flex items-center gap-2">
                <span className="text-lg">⚠️</span> Health Concerns
              </h4>
              <ul className="space-y-2">
                {gemini_analysis.health_concerns.map((concern, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-red-500 mt-1">•</span>
                    <span className="text-red-800 text-sm font-medium">{concern}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Positive Aspects */}
          {gemini_analysis.positive_aspects.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bento-card p-6 bg-green-50 border-green-200"
            >
              <h4 className="font-black text-green-900 text-sm uppercase mb-3 flex items-center gap-2">
                <span className="text-lg">✅</span> Positive Aspects
              </h4>
              <ul className="space-y-2">
                {gemini_analysis.positive_aspects.map((aspect, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">•</span>
                    <span className="text-green-800 text-sm font-medium">{aspect}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h4 className="font-black text-slate-900 text-lg uppercase mb-4 flex items-center gap-2">
                <span className="text-2xl">🚀</span> Healthier Alternatives
              </h4>

              <div className="space-y-4">
                {recommendations.map((rec, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="bento-card p-6 bg-white/80 border-2"
                    style={{ borderColor: getGradeColor(rec.analysis.grade) }}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <div
                            className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-black text-white"
                            style={{ backgroundColor: getGradeColor(rec.analysis.grade) }}
                          >
                            {rec.analysis.grade}
                          </div>
                          <div>
                            <h5 className="font-black text-slate-900 text-base">
                              {rec.product.product_name}
                            </h5>
                            <p className="text-slate-600 font-medium text-sm">
                              {rec.product.brands}
                            </p>
                          </div>
                        </div>

                        <p className="text-slate-700 text-sm mb-3">
                          {rec.personalized_recommendation || rec.reasoning}
                        </p>

                        <div className="flex items-center gap-4 text-xs">
                          <span className="bg-slate-100 text-slate-700 px-2 py-1 rounded-full font-bold">
                            Score: {rec.analysis.score}/100
                          </span>
                          <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full font-bold">
                            +{rec.analysis.score - gemini_analysis.score} pts better
                          </span>
                        </div>
                      </div>

                      {rec.image_url && (
                        <img
                          src={rec.image_url}
                          alt={rec.product.product_name}
                          className="w-20 h-20 object-cover rounded-xl shadow-md"
                        />
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* User Context */}
          {user_context && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bento-card p-6 bg-blue-50 border-blue-200"
            >
              <h4 className="font-black text-blue-900 text-sm uppercase mb-3 flex items-center gap-2">
                <span className="text-lg">👤</span> Personalized For You
              </h4>
              <p className="text-blue-800 text-sm font-medium">
                {user_context}
              </p>
            </motion.div>
          )}

        </motion.div>
      </main>
    </div>
  );
};

export default ScanResultsScreen;
