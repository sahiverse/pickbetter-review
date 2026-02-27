
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProfile, ChatMessage } from '../types';

interface ChatProps {
  profile: UserProfile;
}

const SUGGESTIONS = [
  "Find healthier snacks for weight loss",
  "Is high sodium bad for PCOS?",
  "Analyze my sugar intake today",
  "Top 3 keto friendly Indian snacks"
];

const ChatView: React.FC<ChatProps> = ({ profile }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const callVitalisAPI = async (messages: ChatMessage[]): Promise<string> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000); // 45 second timeout for AI responses

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          user_profile: {
            conditions: profile.conditions || [],
            allergens: profile.allergens || [],
            dietary_preference: profile.dietary_preference,
            primary_goal: profile.primary_goal,
            age: profile.age,
            sex: profile.sex
          }
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return data.response;
      } else {
        console.error('Chat API error:', response.status, response.statusText);
        return "I'm sorry, I'm having trouble connecting right now. Please try again later.";
      }
    } catch (error: any) {
      console.error('Chat API call failed:', error);
      
      if (error.name === 'AbortError') {
        return "The request timed out. Please try again.";
      }
      
      return "I'm experiencing some technical difficulties. Please try again in a moment.";
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Call Vitalis AI
      const aiResponse = await callVitalisAPI([...messages, userMsg]);

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: aiResponse
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I'm having trouble processing your request right now. Please try again."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#FFFDE1] overflow-hidden">
      <header className="px-6 pt-12 pb-4 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tighter uppercase">Vitalis AI</h2>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-[#93BD57] rounded-full animate-pulse shadow-[0_0_8px_#93BD57]" />
            <p className="text-slate-400 text-[9px] font-black uppercase tracking-widest">Health Expert Online</p>
          </div>
        </div>
        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-[#93BD57] shadow-xl border border-[#FBE580]/50">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
        </div>
      </header>

      <main 
        ref={scrollRef}
        className="flex-1 overflow-y-auto no-scrollbar px-6 py-4 space-y-6"
      >
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="pt-10 space-y-8">
              <div className="text-center space-y-2">
                <h3 className="text-xl font-black text-slate-900 uppercase tracking-tighter">How can I help you today?</h3>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">
                  Ask me anything about your scanned items or nutrition goals.
                </p>
              </div>
              
              <div className="grid gap-3">
                {SUGGESTIONS.map((s, idx) => (
                  <motion.button
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    onClick={() => handleSend(s)}
                    className="glass p-4 text-left text-[11px] font-black uppercase text-slate-600 tracking-tight hover:border-[#93BD57] transition-all flex items-center justify-between"
                  >
                    <span>{s}</span>
                    <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" /></svg>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] p-4 rounded-[32px] ${
                msg.role === 'user' 
                ? 'bg-slate-900 text-white rounded-tr-lg shadow-xl' 
                : 'bg-white border-2 border-[#FBE580]/30 text-slate-800 rounded-tl-lg shadow-sm'
              }`}>
                <p className="text-sm font-bold leading-relaxed">{msg.content}</p>
              </div>
            </motion.div>
          ))}

          {isTyping && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
               <div className="bg-white border-2 border-[#FBE580]/30 p-4 rounded-[32px] rounded-tl-lg flex gap-1">
                  <div className="w-1.5 h-1.5 bg-[#93BD57] rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-[#93BD57] rounded-full animate-bounce delay-75" />
                  <div className="w-1.5 h-1.5 bg-[#93BD57] rounded-full animate-bounce delay-150" />
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Input Area */}
      <div className="p-6 bg-white/50 backdrop-blur-lg">
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(inputValue)}
            placeholder="Type your nutrition query..."
            className="w-full bg-white border-2 border-[#FBE580] rounded-[32px] py-5 px-6 pr-16 text-sm font-bold focus:outline-none focus:border-[#93BD57] transition-all shadow-sm"
          />
          <button 
            onClick={() => handleSend(inputValue)}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-12 h-12 bg-[#93BD57] rounded-2xl flex items-center justify-center text-white shadow-glow"
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatView;
