import React, { useState, useEffect, useRef } from 'react';
import type { Observation } from '../types';
import { askAstraAI } from '../services/api';
import { buildAskAstraContextPayload } from '../utils/observationContext';
import {
  Bot, Send, Sparkles, User, RefreshCw, CheckCircle2, Info
} from 'lucide-react';

const ASTRA_AI_SUGGESTIONS = [
  "Why was this observation prioritized?",
  "Explain the triage score calculation",
  "What is a spiral galaxy?",
  "How does ASTRA detect unusual observations?",
  "What does the domain gate do?",
  "How do astronomers detect exoplanets?"
];

interface CopilotPageProps {
  activeObservation?: Observation | null;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isError?: boolean;
}

const STORAGE_KEY = 'astra_copilot_messages';

export const CopilotPage: React.FC<CopilotPageProps> = ({ activeObservation }) => {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // Fallback if parsing fails
    }
    return [
      {
        id: 'msg-1',
        sender: 'assistant',
        text: 'Greetings Commander. I am ASTRA Space Help AI. Ask me about astronomy, space science, galaxy morphology, domain validation, triage scores, or active observations.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Persist messages in sessionStorage for active browser session
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save chat state:', e);
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: nowStr
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsLoading(true);

    try {
      // Build context payload if an observation is active
      const contextPayload = activeObservation
        ? buildAskAstraContextPayload(activeObservation)
        : undefined;

      // Extract recent conversation history for contextual follow-up
      const conversationHistory = messages
        .filter((m) => !m.isError)
        .slice(-6)
        .map((m) => ({
          sender: m.sender,
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text,
        }));

      const response = await askAstraAI({
        question: query,
        observation_context: contextPayload,
        conversation_history: conversationHistory,
      });

      const assistantMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: err.message || 'Apologies Commander. I was unable to process your request at this moment.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    const initialMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: 'Chat history cleared. Standby for queries regarding astronomy and ASTRA observation triage.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([initialMsg]);
    sessionStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto space-y-6 flex flex-col h-[calc(100vh-80px)] font-sans-ui selection:bg-[#C7CDD5]/30">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#252D37] pb-4 shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-[#151B23] border border-[#C7CDD5]/30 text-[#D5DAE0]">
              <Bot className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold font-serif-display text-[#F2F4F7] tracking-wider uppercase">
              ASTRA Space Help AI
            </h1>
          </div>
          <p className="text-xs text-[#A8B0BA] font-sans-ui mt-1">
            Scientific assistant for astronomy Q&A, space science, galaxy morphology, triage priorities, and observation data.
          </p>
        </div>

        <button
          onClick={handleClearHistory}
          className="text-xs font-mono-tech px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] hover:text-[#F2F4F7] border border-[#252D37] transition-all cursor-pointer"
        >
          CLEAR CHAT
        </button>
      </div>

      {/* Integration Context Notice */}
      {activeObservation ? (
        <div className="bg-[#151B23] border border-[#C7CDD5]/30 p-3 rounded-lg flex items-center justify-between text-xs font-mono-tech text-[#D5DAE0] shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#5FC7A1] shrink-0" />
            <span>
              ACTIVE TARGET CONTEXT: <strong className="text-white">{activeObservation.id}</strong> ({activeObservation.is_live ? 'LIVE ANALYSIS' : 'ARCHIVE'}) — {activeObservation.broad_morphology} ({(activeObservation.confidence * 100).toFixed(0)}%)
            </span>
          </div>
          <span className="text-[10px] font-bold text-[#D6A84F] bg-[#3A2B15] border border-[#D6A84F]/40 px-2 py-0.5 rounded">
            PRIORITY: {activeObservation.priority}
          </span>
        </div>
      ) : (
        <div className="bg-[#15232E] border border-[#8FAFC2]/30 p-3 rounded-lg flex items-center gap-3 text-xs font-mono-tech text-[#8FAFC2] shrink-0">
          <Info className="w-4 h-4 text-[#8FAFC2] shrink-0" />
          <span>General astronomy mode active. Select an observation from Research or Library to provide optional target context.</span>
        </div>
      )}

      {/* Chat Conversation Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 glass-panel rounded-2xl border border-[#252D37] bg-[#030508]/80">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-mono-tech font-bold ${
                msg.sender === 'user'
                  ? 'bg-[#D5DAE0] text-[#070B11]'
                  : 'bg-[#151B23] text-[#8FAFC2] border border-[#C7CDD5]/30'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-2xl rounded-xl p-4 space-y-1.5 text-xs font-sans-ui leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[#252D37] text-[#F2F4F7] border border-[#C7CDD5]/30 rounded-tr-none'
                  : msg.isError
                  ? 'bg-[#3A1D1D] text-rose-200 border border-rose-500/40 rounded-tl-none font-mono-tech'
                  : 'glass-panel text-[#A8B0BA] border border-[#252D37] rounded-tl-none'
              }`}
            >
              <div className="flex justify-between items-center text-[10px] font-mono-tech text-[#717985] pb-1 border-b border-[#252D37]/50 mb-1">
                <span>{msg.sender === 'user' ? 'YOU' : 'ASTRA AI'}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 text-xs font-mono-tech text-[#8FAFC2] p-2">
            <RefreshCw className="w-4 h-4 animate-spin text-[#8FAFC2]" />
            <span>Consulting ASTRA knowledge base...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips & Input Area */}
      <div className="space-y-3 shrink-0">
        <div className="flex flex-wrap gap-2">
          {ASTRA_AI_SUGGESTIONS.map((sug, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(sug)}
              className="text-[11px] font-mono-tech px-3 py-1.5 rounded-full bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] hover:text-[#F2F4F7] border border-[#252D37] transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Sparkles className="w-3 h-3 text-[#D6A84F]" />
              {sug}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask ASTRA about astronomy, astrophysics, domain gate, triage scores, or active observations..."
            disabled={isLoading}
            className="flex-1 bg-[#0D1219] border border-[#252D37] focus:border-[#C7CDD5] rounded-xl px-4 py-3 text-xs font-sans-ui text-[#F2F4F7] placeholder-[#717985] focus:outline-none transition-all"
          />
          <button
            type="submit"
            disabled={isLoading || !inputQuery.trim()}
            className="px-5 py-3 rounded-xl bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-md"
          >
            SEND <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default CopilotPage;

