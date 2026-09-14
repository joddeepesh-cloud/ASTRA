import React, { useState, useEffect, useRef } from 'react';
import type { Observation } from '../types';
import { askAstraAI } from '../services/api';
import { buildAskAstraContextPayload } from '../utils/observationContext';
import {
  Bot, X, Send, Sparkles, User, RefreshCw, FileText, RotateCcw
} from 'lucide-react';

interface AskAstraModalProps {
  observation: Observation;
  onClose: () => void;
  onOpenDossier?: (obs: Observation) => void;
  initialQuestion?: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isError?: boolean;
}

export const AskAstraModal: React.FC<AskAstraModalProps> = ({
  observation,
  onClose,
  onOpenDossier,
  initialQuestion
}) => {
  const storageKey = `ask_astra_chat_${observation.id}`;

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // Fallback
    }

    const defaultMsgText = `Greetings Commander. I am ready to answer your questions regarding observation ${observation.id} (${observation.broad_morphology} morphology).`;

    return [
      {
        id: 'msg-1',
        sender: 'assistant',
        text: defaultMsgText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasAutoSubmittedInitialRef = useRef(false);

  // Persist conversation state per observation ID
  useEffect(() => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save Ask Astra modal state:', e);
    }
  }, [messages, storageKey]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (queryToSend?: string) => {
    const query = (queryToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: nowStr
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryToSend) setInputQuery('');
    setIsLoading(true);

    try {
      // Structured observation context payload
      const contextPayload = buildAskAstraContextPayload(observation);
      const response = await askAstraAI(query, contextPayload);

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
        text: err.message || 'Apologies Commander. Unable to process observation question.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-submit initial question if provided
  useEffect(() => {
    if (initialQuestion && !hasAutoSubmittedInitialRef.current) {
      hasAutoSubmittedInitialRef.current = true;
      handleSendMessage(initialQuestion);
    }
  }, [initialQuestion]);

  const handleClearChat = () => {
    const defaultMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `Chat history cleared for target ${observation.id}. Standby for questions.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([defaultMsg]);
    sessionStorage.removeItem(storageKey);
  };

  const quickPrompts = [
    `Why was ${observation.id} flagged with priority ${observation.priority}?`,
    `Explain the ${observation.broad_morphology} features of this galaxy.`,
    `What are the celestial coordinates and catalog status?`,
    `What does ASTRA recommend for next steps?`
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 selection:bg-[#C7CDD5]/30 font-sans-ui">
      <div className="bg-[#070B11] border border-[#C7CDD5]/30 rounded-2xl max-w-2xl w-full h-[90vh] flex flex-col shadow-2xl overflow-hidden text-[#F2F4F7]">
        
        {/* Modal Header */}
        <div className="px-5 py-3.5 bg-[#0D1219] border-b border-[#252D37] flex items-center justify-between shrink-0 font-mono-tech">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[#151B23] border border-[#C7CDD5]/30 text-[#D5DAE0]">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#F2F4F7] uppercase tracking-wider">
                SPACE HELP AI — TARGET QA
              </h2>
              <p className="text-[10px] text-[#A8B0BA] font-sans-ui">
                Target-Grounded Scientific Assistant
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearChat}
              className="p-1.5 rounded-lg text-[#717985] hover:text-[#F2F4F7] hover:bg-[#151B23] transition-all cursor-pointer"
              title="Clear Conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#717985] hover:text-white hover:bg-[#151B23] transition-all cursor-pointer"
              title="Close Space Help AI"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Active Target Attachment Card Header */}
        <div className="px-4 py-2.5 bg-[#151B23]/70 border-b border-[#252D37] flex items-center justify-between gap-3 text-xs shrink-0 font-mono-tech">
          <div className="flex items-center gap-3">
            <img
              src={observation.image_url}
              alt={observation.id}
              loading="lazy"
              className="w-10 h-10 rounded object-cover border border-[#C7CDD5]/30 bg-black shrink-0"
            />
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">{observation.id}</span>
                <span className="text-[10px] text-[#D5DAE0]">{observation.broad_morphology}</span>
                <span className="text-[10px] text-[#5FC7A1]">{(observation.confidence * 100).toFixed(0)}% Conf</span>
              </div>
              <div className="text-[10px] text-[#717985]">
                RA {observation.ra.toFixed(2)}°, DEC {observation.dec.toFixed(2)}° &bull; {observation.provenance || 'GZ2 / SDSS DR7'}
              </div>
            </div>
          </div>

          {onOpenDossier && (
            <button
              onClick={() => {
                onClose();
                onOpenDossier(observation);
              }}
              className="px-2.5 py-1 rounded bg-[#0D1219] hover:bg-[#252D37] text-[#D5DAE0] font-mono-tech text-[10px] border border-[#252D37] transition-all cursor-pointer shrink-0 flex items-center gap-1"
              title="Return to Science Dossier"
            >
              <FileText className="w-3 h-3 text-[#8FAFC2]" /> Dossier
            </button>
          )}
        </div>

        {/* Chat Conversation Scroll Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#030508]/80">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-mono-tech font-bold ${
                  msg.sender === 'user'
                    ? 'bg-[#D5DAE0] text-[#070B11]'
                    : 'bg-[#151B23] text-[#8FAFC2] border border-[#C7CDD5]/30'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div
                className={`max-w-lg rounded-xl p-3.5 space-y-1 text-xs leading-relaxed font-sans-ui ${
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
            <div className="flex items-center gap-2 text-xs font-mono-tech text-[#8FAFC2] p-2">
              <RefreshCw className="w-4 h-4 animate-spin text-[#8FAFC2]" />
              <span>Analyzing target science context...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bottom Prompts & Input Area */}
        <div className="p-4 bg-[#0D1219] border-t border-[#252D37] space-y-3 shrink-0">
          <div className="flex flex-wrap gap-1.5">
            {quickPrompts.map((promptText, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(promptText)}
                className="text-[10px] font-mono-tech px-2.5 py-1 rounded-full bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] hover:text-[#F2F4F7] border border-[#252D37] transition-all cursor-pointer flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3 text-[#D6A84F]" />
                {promptText}
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
              placeholder={`Ask a question about ${observation.id}...`}
              disabled={isLoading}
              className="flex-1 bg-[#030508] border border-[#252D37] focus:border-[#C7CDD5] rounded-xl px-3.5 py-2.5 text-xs font-sans-ui text-[#F2F4F7] placeholder-[#717985] focus:outline-none transition-all"
            />
            <button
              type="submit"
              disabled={isLoading || !inputQuery.trim()}
              className="px-4 py-2.5 rounded-xl bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 cursor-pointer shadow-md"
            >
              SEND <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
