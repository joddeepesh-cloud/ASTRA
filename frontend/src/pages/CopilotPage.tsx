import React, { useState } from 'react';
import type { Observation, CopilotMessage } from '../types';
import { MOCK_COPILOT_SUGGESTIONS, MOCK_COPILOT_INITIAL_MESSAGES } from '../data/mockData';
import { Bot, Send, Sparkles, Info, CheckCircle2 } from 'lucide-react';

interface CopilotPageProps {
  activeObservation?: Observation;
}

export const CopilotPage: React.FC<CopilotPageProps> = ({ activeObservation }) => {
  const [messages, setMessages] = useState<CopilotMessage[]>(MOCK_COPILOT_INITIAL_MESSAGES);
  const [input, setInput] = useState('');

  const handleSend = (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg: CopilotMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      content: query,
      is_demo: false
    };

    let replyText = '';
    const qLower = query.toLowerCase();

    if (activeObservation && activeObservation.triage_response) {
      const tr = activeObservation.triage_response;
      const prio = tr.priority_level ?? activeObservation.priority;
      const score = (tr.experimental_triage_score ?? activeObservation.anomaly_score);
      const nov = (tr.novelty_score ?? activeObservation.ood_score);
      const unc = (tr.uncertainty_score ?? 0.0);
      const odd = (tr.oddity_score ?? 0.0);
      const rawEmb = (tr.raw_embedding_distance ?? 0.0);
      const refCls = tr.nearest_reference_class ?? 'UNKNOWN';
      const predCls = tr.predicted_class ?? activeObservation.gz2class;
      const conf = (tr.class_confidence ?? activeObservation.confidence) * 100;
      const attrs = tr.scientific_attributes;

      if (qLower.includes('priority') || qLower.includes('high') || qLower.includes('medium') || qLower.includes('low')) {
        replyText = `Target ${activeObservation.id} is assigned priority ${prio} based on an experimental triage score of ${score.toFixed(2)}. Signals: Novelty (${nov.toFixed(2)}), Uncertainty (${unc.toFixed(2)}), Oddity (${odd.toFixed(2)}).`;
      } else if (qLower.includes('novelty') || qLower.includes('distance') || qLower.includes('ood')) {
        replyText = `Novelty Score is ${nov.toFixed(2)} (embedding distance ${rawEmb.toFixed(2)} to reference centroid class '${refCls}'). High novelty indicates latent features divergent from typical training clusters.`;
      } else if (qLower.includes('morphology') || qLower.includes('class') || qLower.includes('predict')) {
        const smoothP = attrs ? (attrs.prob_smooth * 100).toFixed(0) : 'N/A';
        const featP = attrs ? (attrs.prob_features * 100).toFixed(0) : 'N/A';
        const spiralP = attrs ? (attrs.prob_spiral * 100).toFixed(0) : 'N/A';
        replyText = `Predicted Morphology: ${predCls} with ${conf.toFixed(1)}% model confidence. Continuous attribute probabilities: Smooth (${smoothP}%), Features (${featP}%), Spiral (${spiralP}%).`;
      } else if (qLower.includes('oddity') || qLower.includes('unusual') || qLower.includes('anomaly')) {
        replyText = `Oddity Score is ${odd.toFixed(2)} (prob_odd attribute). ${tr.explanation}`;
      } else {
        replyText = `Target ${activeObservation.id} Analysis Context: Predicted Class=${predCls} (${conf.toFixed(1)}%), Triage Score=${score.toFixed(2)}, Priority=${prio}. ${tr.explanation}`;
      }
    } else if (activeObservation) {
      replyText = `Observation ${activeObservation.id}: Broad Morphology=${activeObservation.broad_morphology}, Priority=${activeObservation.priority}, Anomaly Score=${activeObservation.anomaly_score.toFixed(2)}. ${activeObservation.explanation || 'Curated mission archive observation.'}`;
    } else {
      replyText = `[COPILOT CONTEXT] — Ask about priority scoring, novelty metrics, predicted morphology, or oddity signals. Upload an image in Research Mode to enable live target context.`;
    }

    const copilotMsg: CopilotMessage = {
      id: `copilot-${Date.now()}`,
      sender: 'copilot',
      timestamp: new Date().toLocaleTimeString(),
      content: replyText,
      is_demo: false
    };

    setMessages((prev) => [...prev, userMsg, copilotMsg]);
    setInput('');
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-5xl mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* Top Header */}
      <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono text-white tracking-wider flex items-center gap-2">
              <Bot className="w-5 h-5 text-indigo-400" />
              ASTRA MISSION COPILOT
            </h1>
            <span className="text-xs font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded">
              DETERMINISTIC CONTEXT ASSISTANT
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Autonomous scientific assistant designed to explain triage decisions, anomaly scores, and catalog alignments.
          </p>
        </div>
      </div>

      {/* Integration Context Notice */}
      {activeObservation ? (
        <div className="bg-cyan-950/40 border border-cyan-500/40 p-3 rounded-lg flex items-center justify-between text-xs font-mono text-cyan-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              ACTIVE TARGET CONTEXT: <strong className="text-white">{activeObservation.id}</strong> ({activeObservation.is_live ? 'LIVE ANALYSIS' : 'ARCHIVE'}) — {activeObservation.gz2class} ({(activeObservation.confidence * 100).toFixed(0)}%)
            </span>
          </div>
          <span className="text-[10px] font-bold text-amber-400 bg-amber-950/60 border border-amber-500/30 px-2 py-0.5 rounded">
            PRIORITY: {activeObservation.priority}
          </span>
        </div>
      ) : (
        <div className="bg-indigo-950/30 border border-indigo-500/30 p-3 rounded-lg flex items-center gap-3 text-xs font-mono text-indigo-200">
          <Info className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>
            No active upload context selected. Upload an observation in Research Mode to enable live target explanation.
          </span>
        </div>
      )}

      {/* Chat Messages Scroll Window */}
      <div className="flex-1 glass-panel p-4 md:p-6 rounded-xl border border-slate-800 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-2xl p-4 rounded-xl text-xs font-sans leading-relaxed space-y-2 border ${
                msg.sender === 'user'
                  ? 'bg-cyan-950/80 border-cyan-800/60 text-cyan-100 rounded-br-none font-mono'
                  : msg.sender === 'system'
                  ? 'bg-slate-900/90 border-slate-800 text-slate-300 font-mono text-[11px]'
                  : 'bg-slate-900/80 border-slate-800 text-slate-200 rounded-bl-none'
              }`}
            >
              <div className="flex items-center justify-between gap-4 border-b border-slate-800/60 pb-1.5 text-[10px] font-mono text-slate-400">
                <span className="font-bold uppercase tracking-wider flex items-center gap-1">
                  {msg.sender === 'copilot' && <Bot className="w-3.5 h-3.5 text-indigo-400" />}
                  {msg.sender === 'user' ? 'LION-COMMANDER' : msg.sender === 'system' ? 'SYSTEM LOG' : 'ASTRA COPILOT'}
                </span>
                <span>{msg.timestamp}</span>
              </div>

              <p>{msg.content}</p>

              {msg.suggested_actions && (
                <div className="pt-2 flex flex-wrap gap-2">
                  {msg.suggested_actions.map((act, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(act)}
                      className="px-2.5 py-1 rounded bg-indigo-950/60 hover:bg-indigo-900 text-indigo-300 border border-indigo-800/50 text-[10px] font-mono transition-all cursor-pointer"
                    >
                      {act}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Suggested Prompt Quick Buttons */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block">
          SUGGESTED EXPLANATION QUERIES:
        </span>
        <div className="flex flex-wrap gap-2">
          {MOCK_COPILOT_SUGGESTIONS.map((sug, i) => (
            <button
              key={i}
              onClick={() => handleSend(sug)}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-800 hover:border-cyan-800/60 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Sparkles className="w-3 h-3 text-amber-400" />
              {sug}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Input Field */}
      <div className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask ASTRA Copilot about observations, anomalies, or catalog matches..."
          className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-4 pr-12 py-3 text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-all shadow-inner"
        />
        <button
          onClick={() => handleSend()}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono transition-all cursor-pointer shadow-md shadow-cyan-950"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
