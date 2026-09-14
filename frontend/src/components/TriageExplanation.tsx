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
  HelpCircle
} from 'lucide-react';

interface TriageExplanationProps {
  signals: TriageInputSignals;
  _compact?: boolean;
}

export const TriageExplanation: React.FC<TriageExplanationProps> = ({ signals }) => {
  const [showTechnical, setShowTechnical] = useState(false);
  const explanation = generateTriageExplanation(signals);

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
    <div className="glass-panel p-5 md:p-6 rounded-xl border border-slate-800 bg-[#070B11]/90 space-y-6 font-sans">
      {/* Header: Priority & Score Overview */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-amber-400 shrink-0" />
            <h3 className="text-sm font-mono font-bold text-white tracking-wider uppercase">
              WHY ASTRA PRIORITIZED THIS OBSERVATION
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            {explanation.priorityDescription}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-start sm:self-auto">
          <PriorityBadge priority={explanation.priority} />
          <div className={`px-3 py-1 rounded-lg border font-mono font-bold text-sm flex items-center gap-1.5 ${getPriorityColor(explanation.priority)}`}>
            <span className="text-[10px] text-slate-400 uppercase tracking-widest">SCORE:</span>
            <span>{explanation.triageScore !== null ? explanation.triageScore.toFixed(2) : 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Primary Reasons / Dominant Drivers */}
      <div className="space-y-2.5">
        <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-[#8FAFC2]" /> PRIMARY TRIAGE DRIVERS
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {explanation.dominantReasons.map((reason) => (
            <div key={reason.name} className="bg-[#0D1219] p-3 rounded-lg border border-[#252D37] space-y-1">
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                <span className="font-bold text-[#8FAFC2]">0{reason.rank} {reason.name.toUpperCase()}</span>
                <span className="text-slate-400">{reason.label}</span>
              </div>
              <p className="text-xs text-slate-300 font-sans leading-snug">
                {reason.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Signal Contribution Breakdown */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Calculator className="w-4 h-4 text-emerald-400" /> CONTRIBUTION BREAKDOWN (WEIGHTED)
          </h4>
          <span className="text-[10px] font-mono text-slate-400">
            SCORE = 35% NOVELTY + 35% UNCERTAINTY + 30% ODDITY
          </span>
        </div>

        <div className="space-y-3.5 pt-1">
          {explanation.contributions.map((contrib) => {
            const hasScore = contrib.score !== null;
            const percentage = hasScore ? Math.round(contrib.score! * 100) : 0;
            const weightedVal = contrib.weightedContribution !== null ? contrib.weightedContribution.toFixed(3) : 'N/A';

            return (
              <div key={contrib.key} className="bg-[#0D1219] p-3.5 rounded-lg border border-[#252D37] space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white uppercase tracking-wider">{contrib.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold ${getMagnitudeColor(contrib.magnitudeLabel)}`}>
                      {contrib.magnitudeLabel}
                    </span>
                    <span className="text-[11px] text-slate-400">({(contrib.weight * 100)}% Weight)</span>
                  </div>

                  <div className="text-right font-mono">
                    {hasScore ? (
                      <span className="text-[#8FAFC2] font-bold">
                        {contrib.score?.toFixed(2)} × {(contrib.weight * 100)}% = <span className="text-white">{weightedVal}</span>
                      </span>
                    ) : (
                      <span className="text-amber-400 text-[11px]">SIGNAL UNAVAILABLE</span>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800 flex">
                  {hasScore ? (
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        contrib.key === 'novelty'
                          ? 'bg-amber-400'
                          : contrib.key === 'uncertainty'
                          ? 'bg-cyan-400'
                          : 'bg-purple-400'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  ) : (
                    <div className="h-full w-full bg-slate-800/50" />
                  )}
                </div>

                {/* Simple Wording */}
                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {contrib.simpleExplanation}
                </p>
              </div>
            );
          })}
        </div>

        {/* Sum Result Bar */}
        {explanation.triageScore !== null && (
          <div className="flex justify-between items-center bg-[#0B0F16] p-3 rounded-lg border border-[#252D37] text-xs font-mono">
            <span className="text-slate-400">CALCULATED TRIAGE SCORE SUM:</span>
            <span className="text-white font-bold text-sm">
              {explanation.contributions[0].weightedContribution?.toFixed(3)} (Novelty) +{' '}
              {explanation.contributions[1].weightedContribution?.toFixed(3)} (Uncertainty) +{' '}
              {explanation.contributions[2].weightedContribution?.toFixed(3)} (Oddity) ={' '}
              <span className="text-emerald-400">{explanation.triageScore.toFixed(3)}</span>
            </span>
          </div>
        )}
      </div>

      {/* Simple Language Terms Guide */}
      <div className="bg-[#0B0E14] p-4 rounded-lg border border-[#252D37] space-y-2">
        <h4 className="text-xs font-mono font-bold text-[#8FAFC2] uppercase tracking-wider flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-indigo-400" /> WHAT THESE SIGNALS MEAN IN SIMPLE TERMS
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-sans text-slate-300">
          <div>
            <span className="font-mono text-amber-400 font-bold block text-[11px]">NOVELTY / DISTANCE</span>
            <span>{explanation.simpleTerms.noveltyMeaning}</span>
          </div>
          <div>
            <span className="font-mono text-cyan-400 font-bold block text-[11px]">UNCERTAINTY / AMBIGUITY</span>
            <span>{explanation.simpleTerms.uncertaintyMeaning}</span>
          </div>
          <div>
            <span className="font-mono text-purple-400 font-bold block text-[11px]">ODDITY / IRREGULARITY</span>
            <span>{explanation.simpleTerms.oddityMeaning}</span>
          </div>
        </div>
      </div>

      {/* Technical & Mathematical Breakdown Toggle */}
      <div className="pt-1 border-t border-slate-800/80">
        <button
          onClick={() => setShowTechnical(!showTechnical)}
          className="text-xs font-mono text-[#8FAFC2] hover:text-white transition-colors flex items-center gap-1.5 cursor-pointer py-1"
        >
          {showTechnical ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          <span>{showTechnical ? 'HIDE TECHNICAL & MATHEMATICAL DETAILS' : 'VIEW TECHNICAL & MATHEMATICAL DETAILS'}</span>
        </button>

        {showTechnical && (
          <div className="mt-3 p-4 rounded-lg bg-black/80 border border-slate-800 space-y-3 text-xs font-mono text-slate-300">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
              <div>
                <span className="text-slate-400 block">RAW EMBEDDING DISTANCE</span>
                <span className="text-amber-400 font-bold">{explanation.technicalDetails.rawEmbeddingDistance?.toFixed(6) ?? 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block">TOP-1 CONFIDENCE</span>
                <span className="text-emerald-400 font-bold">
                  {explanation.technicalDetails.confidence !== null ? `${(explanation.technicalDetails.confidence * 100).toFixed(2)}%` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">ODD PROBABILITY (P_ODD)</span>
                <span className="text-purple-400 font-bold">{explanation.technicalDetails.pOdd?.toFixed(4) ?? 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block">MODEL VERSION</span>
                <span className="text-slate-300 font-bold">{explanation.technicalDetails.modelVersion}</span>
              </div>
            </div>

            <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[11px] text-[#8FAFC2] font-mono overflow-x-auto">
              <span className="text-slate-400 block mb-1">CANONICAL EQUATION:</span>
              <code>{explanation.technicalDetails.mathBreakdown}</code>
            </div>
          </div>
        )}
      </div>

      {/* Mandatory Scientific Disclaimer */}
      <div className="p-3.5 bg-slate-950/80 rounded-lg border border-amber-900/30 text-[11px] font-sans text-amber-200/80 leading-relaxed flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-mono font-bold text-amber-400 block text-[10px] uppercase">SCIENTIFIC PRIORITIZATION DISCLAIMER</span>
          <span>{explanation.scientificDisclaimer}</span>
        </div>
      </div>
    </div>
  );
};
