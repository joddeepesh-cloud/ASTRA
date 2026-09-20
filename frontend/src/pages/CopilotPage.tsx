import React, { useState, useEffect, useRef } from 'react';
import type { Observation } from '../types';
import { askAstraAI } from '../services/api';
import { buildAskAstraContextPayload } from '../utils/observationContext';
import {
  Bot, Send, Sparkles, User, RefreshCw, CheckCircle2, Info, AlertTriangle
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
      // Fallback
    }
    return [
      {
        id: 'msg-1',
        sender: 'assistant',
        text: 'Greetings Commander. I am ASTRA Space Help AI. Ask me about astronomy, space science, galaxy morphology, domain validation, triage priorities, or active observations.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showClearChatModal, setShowClearChatModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const autoExplainedObsIdRef = useRef<string | null>(null);

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

  useEffect(() => {
    if (activeObservation && autoExplainedObsIdRef.current !== activeObservation.id) {
      autoExplainedObsIdRef.current = activeObservation.id;
      handleSendMessage(`Provide a detailed scientific explanation of observation ${activeObservation.id}.`);
    }
  }, [activeObservation?.id]);

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
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleConfirmClearChat = () => {
    setShowClearChatModal(false);
    const initialMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: activeObservation
        ? `Conversation cleared for target ${activeObservation.id}. Ask follow-up questions or request further analysis.`
        : 'Chat history cleared. Standby for queries regarding astronomy and ASTRA observation triage.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([initialMsg]);
    sessionStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="h-full w-full p-4 md:p-6 max-w-6xl mx-auto flex flex-col font-sans-ui text-[#ECEAF2] overflow-hidden">
      
      {/* Header Bar (Shrink-0) */}
      <div className="flex items-center justify-between border-b border-[#21133B] pb-3 mb-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#15102A] border border-[#9B7FD4]/40 text-[#8FD3FF]">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold font-serif-display text-white tracking-wider uppercase flex items-center gap-2">
              ASTRA Space Help AI
            </h1>
            <p className="text-xs text-[#8E8A9D] font-sans-ui">
              Grounded scientific astronomy assistant & observation triage console Q&A.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowClearChatModal(true)}
          className="text-xs font-mono-tech px-3 py-1.5 rounded-lg bg-[#15102A] hover:bg-[#21133B] text-[#8E8A9D] hover:text-white border border-[#21133B] transition-all cursor-pointer"
        >
          CLEAR CHAT
        </button>
      </div>

      {/* Active Observation Context Bar (Shrink-0) */}
      {activeObservation ? (
        <div className="bg-[#15102A] border border-[#9B7FD4]/40 p-3 rounded-xl flex items-center justify-between text-xs font-mono-tech text-[#ECEAF2] mb-3 shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#58BFA7] shrink-0" />
            <span>
              ACTIVE TARGET CONTEXT: <strong className="text-white font-bold">{activeObservation.id}</strong> ({activeObservation.is_live ? 'LIVE ANALYSIS' : 'ARCHIVE'}) — {activeObservation.broad_morphology} ({activeObservation.confidence != null ? `${(activeObservation.confidence * 100).toFixed(0)}%` : 'N/A'})
            </span>
          </div>
          <span className="text-[10px] font-bold text-[#D6A84F] bg-[#21133B] border border-[#D6A84F]/40 px-2.5 py-0.5 rounded-full">
            PRIORITY: {activeObservation.priority}
          </span>
        </div>
      ) : (
        <div className="bg-[#15102A]/80 border border-[#55C7D9]/30 p-2.5 rounded-xl flex items-center gap-2.5 text-xs font-mono-tech text-[#55C7D9] mb-3 shrink-0">
          <Info className="w-4 h-4 text-[#55C7D9] shrink-0" />
          <span>General astronomy mode active. Ask any space question or select an observation target to provide context.</span>
        </div>
      )}

      {/* Main Conversation Scroll Box (Flex-1) */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 glass-panel rounded-2xl border border-[#21133B] bg-[#070912]/90 min-h-0">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-mono-tech font-bold ${
                msg.sender === 'user'
                  ? 'bg-[#7657B8] text-white shadow-md shadow-[#7657B8]/30'
                  : 'bg-[#15102A] text-[#8FD3FF] border border-[#9B7FD4]/40'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-2xl rounded-2xl p-4 space-y-1.5 text-xs font-sans-ui leading-relaxed shadow-lg ${
                msg.sender === 'user'
                  ? 'bg-[#21133B] text-white border border-[#9B7FD4]/40 rounded-tr-none'
                  : msg.isError
                  ? 'bg-[#3A1D1D] text-rose-200 border border-rose-500/40 rounded-tl-none font-mono-tech'
                  : 'glass-panel text-[#ECEAF2] border border-[#21133B] rounded-tl-none'
              }`}
            >
              <div className="flex justify-between items-center text-[10px] font-mono-tech text-[#8E8A9D] pb-1 border-b border-[#21133B]/60 mb-1">
                <span className="font-bold text-[#8FD3FF]">{msg.sender === 'user' ? 'COMMANDER' : 'ASTRA SPACE AI'}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 text-xs font-mono-tech text-[#8FD3FF] p-3 glass-panel rounded-xl border border-[#9B7FD4]/30 w-fit">
            <RefreshCw className="w-4 h-4 animate-spin text-[#8FD3FF]" />
            <span>Consulting ASTRA scientific knowledge base...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Fixed Composer Bar (Shrink-0) */}
      <div className="mt-3 space-y-2.5 shrink-0 pt-2 border-t border-[#21133B]">
        {/* Suggested Prompt Chips */}
        <div className="flex flex-wrap gap-2 max-h-16 overflow-y-auto">
          {ASTRA_AI_SUGGESTIONS.map((sug, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(sug)}
              className="text-[11px] font-mono-tech px-3 py-1 rounded-full bg-[#15102A] hover:bg-[#21133B] text-[#D8D3E2] hover:text-white border border-[#9B7FD4]/30 transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
            >
              <Sparkles className="w-3 h-3 text-[#D6A84F]" />
              {sug}
            </button>
          ))}
        </div>

        {/* High-Contrast Interactive Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-3 bg-[#0D0A1C] p-2.5 rounded-2xl border-2 border-[#9B7FD4]/60 focus-within:border-[#9B7FD4] focus-within:ring-2 focus-within:ring-[#9B7FD4]/30 transition-all shadow-2xl"
        >
          <textarea
            ref={inputRef as any}
            rows={1}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Ask ASTRA about astronomy, space science, triage scores, or active observations..."
            disabled={isLoading}
            className="flex-1 bg-transparent px-3 py-2 text-xs font-sans-ui text-white placeholder-[#8E8A9D] focus:outline-none resize-none"
          />

          <button
            type="submit"
            disabled={isLoading || !inputQuery.trim()}
            className="px-5 py-2.5 rounded-xl bg-[#7657B8] hover:bg-[#9B7FD4] text-white font-mono-tech text-xs font-bold transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer shadow-lg shadow-[#7657B8]/40 shrink-0"
          >
            <span>SEND</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* CLEAR CHAT CONFIRMATION MODAL OVERLAY */}
      {showClearChatModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto font-sans-ui">
          <div className="relative w-full max-w-md bg-[#090D14] border border-[#21133B] rounded-2xl p-6 space-y-4 shadow-2xl text-[#ECEAF2]">
            <div className="flex items-center gap-3 border-b border-[#21133B] pb-3">
              <AlertTriangle className="w-6 h-6 text-[#D6A84F] shrink-0" />
              <h3 className="text-base font-bold font-serif-display text-white tracking-wider uppercase">
                Clear Conversation?
              </h3>
            </div>

            <p className="text-xs text-[#8E8A9D] font-sans-ui leading-relaxed">
              This will remove all current conversation messages. {activeObservation ? `The active observation context (${activeObservation.id}) will remain attached for follow-up questions.` : ''}
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowClearChatModal(false)}
                className="px-4 py-2 rounded-lg bg-[#15102A] hover:bg-[#21133B] text-slate-300 font-mono-tech text-xs cursor-pointer border border-[#21133B]"
              >
                CANCEL
              </button>

              <button
                onClick={handleConfirmClearChat}
                className="px-4 py-2 rounded-lg bg-[#7657B8] hover:bg-[#9B7FD4] text-white font-mono-tech text-xs font-bold cursor-pointer shadow-lg shadow-[#7657B8]/30"
              >
                CLEAR CHAT
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CopilotPage;
