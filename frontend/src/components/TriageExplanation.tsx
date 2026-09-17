import React, { useState } from 'react';
import {
  generateTriageExplanation,
  type TriageInputSignals
} from '../utils/triageExplanation';
import { PriorityBadge } from './PriorityBadge';
import {
  Sparkles,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  Calculator,
  AlertCircle,
  Info,
  CheckCircle2
} from 'lucide-react';

interface TriageExplanationProps {
  signals: TriageInputSignals;
  _compact?: boolean;
}

export const TriageExplanation: React.FC<TriageExplanationProps> = ({ signals }) => {
  const [showTechnical, setShowTechnical] = useState(false);
  const explanation = generateTriageExplanation(signals);
  const interp = explanation.interpretation;

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'text-purple-400 border-purple-500/50 bg-purple-950/40';
      case 'HIGH':
        return 'text-rose-400 border-rose-500/50 bg-rose-950/40';
      case 'MEDIUM':
        return 'text-amber-400 border-amber-500/50 bg-amber-950/40';
      default:
        return 'text-emerald-400 border-emerald-500/50 bg-emerald-950/40';
    }
  };

  const getMagnitudeColor = (magnitude: string) => {
    switch (magnitude) {
      case 'VERY HIGH':
        return 'bg-rose-500 text-white';
      case 'HIGH':
        return 'bg-amber-500 text-black';
      case 'MODERATE':
        return 'bg-cyan-600 text-white';
      case 'LOW':
        return 'bg-slate-700 text-slate-300';
      default:
        return 'bg-slate-800 text-slate-400';
    }
  };

  return (
    <div className="glass-panel p-5 md:p-6 rounded-2xl border border-[#9B7FD4]/30 bg-[#070912]/95 space-y-6 font-sans-ui text-[#ECEAF2]">
      
      {/* ========================================================= */}
      {/* 1. PROMINENT ANOMALY INTERPRETATION CARD                   */}
      {/* ========================================================= */}
      <div className="bg-[#0D0A1C] p-5 rounded-2xl border border-[#9B7FD4]/40 space-y-4 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#9B7FD4]/05 blur-3xl rounded-full pointer-events-none" />

        {/* Section Header */}
        <div className="flex flex-wrap items-start sm:items-center justify-between gap-3 border-b border-[#21133B] pb-3 min-w-0">
          <div className="flex items-center gap-2.5 min-w-0 flex-1">
            <Sparkles className="w-5 h-5 text-[#D6A84F] shrink-0" />
            <h3
              className="text-sm sm:text-base font-mono-tech font-bold text-white tracking-wider uppercase font-sans-ui min-w-0"
              style={{ wordBreak: 'normal', overflowWrap: 'normal', whiteSpace: 'normal' }}
            >
              ANOMALY & INTERPRETATION
            </h3>
          </div>
          <div className="flex items-center gap-2 shrink-0 flex-wrap">
            <PriorityBadge priority={interp.priority} />
            <div className={`px-2.5 py-1 rounded-lg border font-mono-tech font-bold text-xs flex items-center gap-1.5 shrink-0 whitespace-nowrap ${getPriorityColor(interp.priority)}`}>
              <span className="text-[10px] text-[#8E8A9D] uppercase tracking-wider">SCORE:</span>
              <span className="whitespace-nowrap">{explanation.triageScore !== null ? explanation.triageScore.toFixed(2) : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* 1. WHAT ASTRA SEES */}
        {interp.objectType === 'GALAXY' ? (
          <div className="bg-[#03040A] p-3.5 rounded-xl border border-[#21133B] space-y-2.5 font-mono-tech text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">OBJECT TYPE</span>
                <span className="text-white font-bold block mt-0.5">GALAXY</span>
              </div>
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">MORPHOLOGY SPECIALIST</span>
                <span className="text-[#8FD3FF] font-bold block mt-0.5">{interp.morphology} ({interp.confidencePct})</span>
              </div>
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">EVIDENCE STATUS</span>
                <span className="text-[#58BFA7] font-bold block mt-0.5">
                  {signals.object_type_info?.status ? signals.object_type_info.status.replace(/_/g, ' ') : 'SUPERVISED SPECIALIST SUPPORTED'}
                </span>
              </div>
            </div>
            {signals.object_type_info?.evidence && signals.object_type_info.evidence.length > 0 && (
              <div className="pt-2 border-t border-[#21133B]/60 text-[11px] space-y-1">
                <span className="text-[#8E8A9D] font-bold block uppercase tracking-wider text-[10px]">EVIDENCE NOTES:</span>
                {signals.object_type_info.evidence.map((note, idx) => (
                  <div key={idx} className={note.includes("RESOLVED IN FAVOR") ? "text-amber-300 font-semibold" : "text-[#D8D3E2]"}>
                    • {note}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-[#03040A] p-3.5 rounded-xl border border-[#21133B] space-y-2.5 font-mono-tech text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">OBJECT TYPE</span>
                <span className="text-amber-300 font-bold block mt-0.5">{interp.objectType}</span>
              </div>
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">STATUS / EVIDENCE QUALITY</span>
                <span className="text-rose-300 font-bold block mt-0.5">
                  {signals.object_type_info?.status ? signals.object_type_info.status.replace(/_/g, ' ') : 'INSUFFICIENT VISUAL EVIDENCE'}
                  {signals.object_type_info?.evidence_quality ? ` (${signals.object_type_info.evidence_quality})` : ''}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">VISUAL SIMILARITY SCORE</span>
                <span className="text-cyan-300 font-bold block mt-0.5">
                  {signals.object_type_info?.visual_similarity_score !== undefined && signals.object_type_info?.visual_similarity_score !== null
                    ? signals.object_type_info.visual_similarity_score.toFixed(2)
                    : (signals.object_type_info?.top_score !== undefined && signals.object_type_info?.top_score !== null
                        ? signals.object_type_info.top_score.toFixed(2)
                        : 'N/A')}
                </span>
              </div>
            </div>
            {signals.object_type_info?.evidence && signals.object_type_info.evidence.length > 0 && (
              <div className="pt-2 border-t border-[#21133B]/60 text-[11px] space-y-1">
                <span className="text-[#8E8A9D] font-bold block uppercase tracking-wider text-[10px]">EVIDENCE EXPLANATION:</span>
                {signals.object_type_info.evidence.map((note, idx) => (
                  <div key={idx} className="text-[#D8D3E2]">
                    • {note}
                  </div>
                ))}
              </div>
            )}
            <div className="pt-2 border-t border-[#21133B]/60 text-[#8E8A9D] text-[11px] flex items-center justify-between">
              <span>Galaxy morphology specialist:</span>
              <span className="text-slate-400 font-semibold">Non-applicable — target object is not routed to galaxy morphology specialist</span>
            </div>
          </div>
        )}

        {/* 2. WHAT LOOKS DIFFERENT */}
        <div className="space-y-1 font-sans-ui text-xs">
          <span className="font-mono-tech font-bold text-[#8FD3FF] block text-[11px] uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#8FD3FF]" /> WHAT LOOKS DIFFERENT
          </span>
          <p className="text-[#ECEAF2] leading-relaxed bg-[#03040A]/70 p-3 rounded-xl border border-[#21133B]">
            {interp.whatLooksDifferent}
          </p>
        </div>

        {/* 3. PRIMARY REASON */}
        <div className="p-3 bg-[#15102A] rounded-xl border border-[#9B7FD4]/40 font-mono-tech text-xs text-[#9B7FD4] font-semibold">
          {interp.primaryReason}
        </div>

        {/* 4. WHY THIS PRIORITY */}
        <div className="space-y-1 font-sans-ui text-xs">
          <span className="font-mono-tech font-bold text-[#D6A84F] block text-[11px] uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-[#D6A84F]" /> WHY THIS PRIORITY ({interp.priority})
          </span>
          <p className="text-[#D8D3E2] leading-relaxed bg-[#03040A]/70 p-3 rounded-xl border border-[#21133B]">
            {interp.whyThisPriority}
          </p>
        </div>

        {/* 5. RECOMMENDED ACTION FOR SPACE STATION OPERATOR */}
        <div className="p-3.5 bg-[#0E241B] rounded-xl border border-[#58BFA7]/40 font-mono-tech text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[#58BFA7]">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#58BFA7] shrink-0" />
            <span>RECOMMENDED ACTION: <strong className="text-white font-bold">{interp.recommendedAction}</strong></span>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#03040A] text-[#58BFA7] border border-[#58BFA7]/30 self-start sm:self-auto">
            OPERATIONAL
          </span>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. SECONDARY TECHNICAL TRIAGE SIGNALS (COLLAPSIBLE)        */}
      {/* ========================================================= */}
      <div className="border border-[#21133B] rounded-2xl overflow-hidden font-mono-tech">
        <button
          onClick={() => setShowTechnical(!showTechnical)}
          className="w-full p-4 bg-[#0D0A1C] hover:bg-[#15102A] flex items-center justify-between text-xs text-[#8FD3FF] transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-2 font-bold tracking-wider uppercase">
            <Calculator className="w-4 h-4 text-[#8FD3FF]" /> Technical Triage Signals & Math Breakdown
          </span>
          {showTechnical ? <ChevronUp className="w-4 h-4 text-[#8FD3FF]" /> : <ChevronDown className="w-4 h-4 text-[#8E8A9D]" />}
        </button>

        {showTechnical && (
          <div className="p-5 bg-[#03040A] border-t border-[#21133B] space-y-6">
            {/* Primary Reasons / Dominant Drivers */}
            <div className="space-y-2.5">
              <h4 className="text-xs font-mono-tech font-bold text-[#8E8A9D] uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#8FAFC2]" /> PRIMARY TRIAGE DRIVERS
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {explanation.dominantReasons.map((reason) => (
                  <div key={reason.name} className="bg-[#0D0A1C] p-3 rounded-xl border border-[#21133B] space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono-tech text-[#8E8A9D]">
                      <span className="font-bold text-[#8FD3FF]">0{reason.rank} {reason.name.toUpperCase()}</span>
                      <span>{reason.label}</span>
                    </div>
                    <p className="text-xs text-[#D8D3E2] font-sans-ui leading-snug">
                      {reason.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Signal Contribution Breakdown */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h4 className="text-xs font-mono-tech font-bold text-[#8E8A9D] uppercase tracking-wider flex items-center gap-2">
                  <Calculator className="w-4 h-4 text-[#58BFA7]" /> CONTRIBUTION BREAKDOWN (WEIGHTED)
                </h4>
                <span className="text-[10px] font-mono-tech text-[#8E8A9D]">
                  SCORE = 35% NOVELTY + 35% UNCERTAINTY + 30% ODDITY
                </span>
              </div>

              <div className="space-y-3 pt-1">
                {explanation.contributions.map((contrib) => {
                  const hasScore = contrib.score !== null;
                  const percentage = hasScore ? Math.round(contrib.score! * 100) : 0;
                  const weightedVal = contrib.weightedContribution !== null ? contrib.weightedContribution.toFixed(3) : 'N/A';

                  return (
                    <div key={contrib.key} className="bg-[#0D0A1C] p-3.5 rounded-xl border border-[#21133B] space-y-2">
                      <div className="flex items-center justify-between text-xs font-mono-tech">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white uppercase tracking-wider">{contrib.name}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono-tech font-semibold ${getMagnitudeColor(contrib.magnitudeLabel)}`}>
                            {contrib.magnitudeLabel}
                          </span>
                          <span className="text-[11px] text-[#8E8A9D]">({(contrib.weight * 100)}% Weight)</span>
                        </div>

                        <div className="text-right font-mono-tech">
                          {hasScore ? (
                            <span className="text-[#8FD3FF] font-bold">
                              {contrib.score?.toFixed(2)} × {(contrib.weight * 100)}% = <span className="text-white">{weightedVal}</span>
                            </span>
                          ) : (
                            <span className="text-amber-400 text-[11px]">SIGNAL UNAVAILABLE</span>
                          )}
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-2 bg-[#03040A] rounded-full overflow-hidden border border-[#21133B] flex">
                        {hasScore ? (
                          <div
                            className={`h-full transition-all duration-500 rounded-full ${
                              contrib.key === 'novelty'
                                ? 'bg-[#D6A84F]'
                                : contrib.key === 'uncertainty'
                                ? 'bg-[#8FD3FF]'
                                : 'bg-[#9B7FD4]'
                            }`}
                            style={{ width: `${percentage}%` }}
                          />
                        ) : (
                          <div className="h-full w-full bg-[#15102A]/50" />
                        )}
                      </div>

                      {/* Simple Wording */}
                      <p className="text-xs text-[#8E8A9D] font-sans-ui leading-relaxed">
                        {contrib.simpleExplanation}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Sum Result Bar */}
              {explanation.triageScore !== null && (
                <div className="flex justify-between items-center bg-[#0D0A1C] p-3 rounded-xl border border-[#21133B] text-xs font-mono-tech">
                  <span className="text-[#8E8A9D]">CALCULATED TRIAGE SCORE SUM:</span>
                  <span className="text-white font-bold text-xs sm:text-sm">
                    {explanation.contributions[0].weightedContribution?.toFixed(3)} (Novelty) +{' '}
                    {explanation.contributions[1].weightedContribution?.toFixed(3)} (Uncertainty) +{' '}
                    {explanation.contributions[2].weightedContribution?.toFixed(3)} (Oddity) ={' '}
                    <span className="text-[#58BFA7] font-extrabold">{explanation.triageScore.toFixed(3)}</span>
                  </span>
                </div>
              )}
            </div>

            {/* Technical Parameters */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] font-mono-tech pt-2 border-t border-[#21133B]">
              <div>
                <span className="text-[#8E8A9D] block">RAW EMBEDDING DISTANCE</span>
                <span className="text-[#D6A84F] font-bold">{explanation.technicalDetails.rawEmbeddingDistance?.toFixed(6) ?? 'N/A'}</span>
              </div>
              <div>
                <span className="text-[#8E8A9D] block">TOP-1 CONFIDENCE</span>
                <span className="text-[#58BFA7] font-bold">
                  {explanation.technicalDetails.confidence !== null ? `${(explanation.technicalDetails.confidence * 100).toFixed(2)}%` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-[#8E8A9D] block">ODD PROBABILITY (P_ODD)</span>
                <span className="text-[#9B7FD4] font-bold">{explanation.technicalDetails.pOdd?.toFixed(4) ?? 'N/A'}</span>
              </div>
              <div>
                <span className="text-[#8E8A9D] block">MODEL VERSION</span>
                <span className="text-white font-bold">{explanation.technicalDetails.modelVersion}</span>
              </div>
            </div>

            <div className="p-3 bg-[#0D0A1C] rounded-xl border border-[#21133B] text-[11px] text-[#8FD3FF] font-mono-tech overflow-x-auto">
              <span className="text-[#8E8A9D] block mb-1">CANONICAL EQUATION:</span>
              <code>{explanation.technicalDetails.mathBreakdown}</code>
            </div>
          </div>
        )}
      </div>

      {/* Mandatory Scientific Disclaimer */}
      <div className="p-3.5 bg-[#0D0A1C] rounded-xl border border-[#D6A84F]/30 text-[11px] font-sans-ui text-[#D6A84F]/90 leading-relaxed flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-[#D6A84F] shrink-0 mt-0.5" />
        <div>
          <span className="font-mono-tech font-bold text-[#D6A84F] block text-[10px] uppercase">SCIENTIFIC PRIORITIZATION DISCLAIMER</span>
          <span>{explanation.scientificDisclaimer}</span>
        </div>
      </div>
    </div>
  );
};

