import React, { useState } from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from './PriorityBadge';
import { getAnomalyExplanation } from '../utils/anomalyExplanation';
import { buildAskAstraContextPayload } from '../utils/observationContext';
import {
  FileText, X, Compass, Layers, AlertCircle, HelpCircle,
  CheckCircle2, ChevronDown, ChevronUp, Bot, Sparkles, ArrowRight,
  Activity, Eye
} from 'lucide-react';

interface ObservationDossierModalProps {
  observation: Observation;
  onClose: () => void;
  onAskAstra: (obs: Observation, prompt?: string) => void;
  onAnalyze: (obs: Observation) => void;
}

export const ObservationDossierModal: React.FC<ObservationDossierModalProps> = ({
  observation,
  onClose,
  onAskAstra,
  onAnalyze
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Generate deterministic science explanation
  const anomalyInfo = getAnomalyExplanation(observation);
  const aiContext = buildAskAstraContextPayload(observation);

  // Probability progress bars data
  const probItems = [
    { label: 'Smooth', val: aiContext.probabilities.smooth, color: 'bg-[#8FAFC2]' },
    { label: 'Edge-on Disk', val: aiContext.probabilities.edge_on, color: 'bg-[#5FC7A1]' },
    { label: 'Featured Disk', val: aiContext.probabilities.featured_disk, color: 'bg-[#D6A84F]' },
    { label: 'Spiral Arms', val: aiContext.probabilities.spiral, color: 'bg-[#D5DAE0]' },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 overflow-y-auto font-sans-ui selection:bg-[#C7CDD5]/30">
      <div className="bg-[#070B11] border border-[#C7CDD5]/30 rounded-2xl max-w-2xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden relative text-[#F2F4F7] my-auto">
        
        {/* Header Bar */}
        <div className="p-4 sm:p-5 border-b border-[#252D37] flex items-center justify-between bg-[#0D1219] shrink-0 font-mono-tech">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#151B23] border border-[#C7CDD5]/30 flex items-center justify-center text-[#D5DAE0] font-bold text-sm">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-[#F2F4F7] tracking-wider">
                  OBSERVATION DOSSIER
                </h2>
                <span className="text-[10px] bg-[#151B23] text-[#D5DAE0] border border-[#C7CDD5]/30 px-2 py-0.5 rounded">
                  {observation.id}
                </span>
              </div>
              <span className="text-[11px] text-[#717985] block font-sans-ui">
                {observation.provenance || 'Galaxy Zoo 2 Survey / SDSS DR7'}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#717985] hover:text-white hover:bg-[#151B23] transition-all cursor-pointer"
            title="Close Dossier"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Dossier Content */}
        <div className="p-4 sm:p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          
          {/* Section 1: Image & HUD Display */}
          <div className="relative aspect-[16/9] sm:aspect-[21/9] bg-black rounded-xl border border-[#C7CDD5]/30 overflow-hidden shadow-inner flex items-center justify-center">
            <img
              src={observation.image_url}
              alt={observation.id}
              loading="lazy"
              className="w-full h-full object-cover opacity-90"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#030508] via-transparent to-transparent opacity-85" />
            
            {/* Top Badges */}
            <div className="absolute top-3 left-3 flex items-center gap-2 font-mono-tech">
              <PriorityBadge priority={observation.priority} />
              <span className="text-[10px] bg-[#030508]/90 text-[#D5DAE0] border border-[#252D37] px-2 py-0.5 rounded backdrop-blur-sm">
                {observation.broad_morphology}
              </span>
            </div>

            {/* Bottom HUD Metadata Overlay */}
            <div className="absolute bottom-3 left-3 right-3 flex justify-between items-end font-mono-tech text-[11px]">
              <div>
                <span className="text-white font-bold block">{observation.id}</span>
                <span className="text-[#717985] text-[10px]">SDSS DR7 ObjID: {observation.dr7objid}</span>
              </div>
              <div className="text-right text-[#A8B0BA] text-[10px] bg-[#030508]/90 px-2 py-1 rounded border border-[#252D37] backdrop-blur-sm">
                <span>RA: {observation.ra.toFixed(4)}°</span>
                <span className="ml-2">DEC: {observation.dec.toFixed(4)}°</span>
              </div>
            </div>
          </div>

          {/* Section 2: What Are We Looking At? */}
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] space-y-2">
            <h3 className="text-xs font-mono-tech font-bold text-[#D5DAE0] uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-[#8FAFC2]" /> WHAT ARE WE LOOKING AT?
            </h3>
            <p className="text-[#A8B0BA] leading-relaxed font-sans-ui text-xs">
              {observation.explanation || `This observation is cataloged in the survey dataset under target morphology class '${observation.broad_morphology}'.`}
            </p>
          </div>

          {/* Section 3: ASTRA Morphology & Probability Breakdown */}
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] space-y-3 font-mono-tech">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-[#F2F4F7] uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#8FAFC2]" /> ASTRA MORPHOLOGY BREAKDOWN
              </h3>
              <span className="text-[11px] text-[#5FC7A1] font-bold bg-[#0E241B] border border-[#5FC7A1]/40 px-2 py-0.5 rounded">
                Confidence: {(observation.confidence * 100).toFixed(1)}%
              </span>
            </div>

            {/* 4-Class Probability Progress Bars */}
            <div className="space-y-2.5 pt-1">
              {probItems.map((item) => (
                <div key={item.label} className="space-y-1 text-[11px]">
                  <div className="flex justify-between text-[#A8B0BA]">
                    <span>{item.label}</span>
                    <span className="text-white font-bold">{(item.val * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-[#030508] rounded-full h-1.5 overflow-hidden border border-[#252D37]">
                    <div
                      className={`h-1.5 rounded-full ${item.color}`}
                      style={{ width: `${item.val * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Why Flagged by ASTRA */}
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] space-y-2">
            <h3 className="text-xs font-mono-tech font-bold text-[#D6A84F] uppercase tracking-wider flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#D6A84F]" /> WHY ASTRA FLAGGED THIS TARGET
            </h3>
            <p className="text-[#A8B0BA] font-sans-ui text-xs leading-relaxed">
              {anomalyInfo.whyFlagged}
            </p>
          </div>

          {/* Section 5: Why High/Medium Priority */}
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] space-y-2">
            <h3 className="text-xs font-mono-tech font-bold text-[#F2F4F7] uppercase tracking-wider flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-[#8FAFC2]" /> TRIAGE PRIORITY REASONING
            </h3>
            <p className="text-[#A8B0BA] font-sans-ui text-xs leading-relaxed">
              {anomalyInfo.whyPriority}
            </p>
          </div>

          {/* Section 6: Recommended Next Steps */}
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] space-y-2">
            <h3 className="text-xs font-mono-tech font-bold text-[#5FC7A1] uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#5FC7A1]" /> RECOMMENDED SCIENTIFIC ACTION
            </h3>
            <p className="text-[#A8B0BA] font-sans-ui text-xs leading-relaxed">
              {anomalyInfo.recommendedSteps}
            </p>
          </div>

          {/* Section 7: Collapsible Technical Raw Metadata */}
          <div className="border border-[#252D37] rounded-xl overflow-hidden font-mono-tech">
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className="w-full p-3 bg-[#0D1219] hover:bg-[#151B23] flex items-center justify-between text-xs text-[#D5DAE0] transition-colors cursor-pointer"
            >
              <span className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#8FAFC2]" /> Technical Details & Raw Metadata
              </span>
              {showTechnicalDetails ? <ChevronUp className="w-4 h-4 text-[#8FAFC2]" /> : <ChevronDown className="w-4 h-4 text-[#717985]" />}
            </button>

            {showTechnicalDetails && (
              <div className="p-4 bg-[#030508] border-t border-[#252D37] space-y-3 text-[11px] text-[#A8B0BA]">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-[#717985] block">SDSS DR7 ObjID</span>
                    <span className="text-white">{observation.dr7objid}</span>
                  </div>
                  <div>
                    <span className="text-[#717985] block">Asset ID</span>
                    <span className="text-white">{observation.asset_id}</span>
                  </div>
                  <div>
                    <span className="text-[#717985] block">RA / DEC</span>
                    <span className="text-white">{observation.ra.toFixed(4)}°, {observation.dec.toFixed(4)}°</span>
                  </div>
                  <div>
                    <span className="text-[#717985] block">Triage Score</span>
                    <span className="text-[#D6A84F] font-bold">{observation.anomaly_score.toFixed(3)}</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#252D37]">
                  <span className="text-[#717985] block mb-1">Catalog Entry</span>
                  <span className="text-white">{observation.catalog_name || 'SDSS DR16 Cross-Match Unregistered'}</span>
                </div>

                <div className="pt-2 text-[10px] text-[#717985]">
                  <span>Provenance: {observation.provenance || 'Galaxy Zoo 2 / SDSS DR7'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Section 8: Prominent "ASK ASTRA" Entry Point */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-[#151B23] via-[#0D1219] to-[#15232E] border border-[#C7CDD5]/30 space-y-3 flex flex-col sm:flex-row items-center justify-between gap-4 font-sans-ui">
            <div>
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-[#8FAFC2]" />
                <h4 className="text-sm font-bold font-mono-tech text-[#F2F4F7] tracking-wider">
                  ASK ASTRA SPACE HELP AI
                </h4>
              </div>
              <p className="text-xs text-[#A8B0BA] font-sans-ui mt-0.5">
                Have a question about target {observation.id}? Open the dedicated AI exploration experience.
              </p>
            </div>

            <button
              onClick={() => {
                onAskAstra(observation);
              }}
              className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold transition-all shadow-lg shadow-black/40 flex items-center justify-center gap-2 cursor-pointer shrink-0"
            >
              <Bot className="w-4 h-4" />
              ASK ASTRA <Sparkles className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#252D37] bg-[#0D1219] flex items-center justify-between gap-3 shrink-0 font-mono-tech text-xs">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] border border-[#252D37] cursor-pointer transition-all"
          >
            Close Dossier
          </button>

          <button
            onClick={() => {
              onClose();
              onAnalyze(observation);
            }}
            className="px-4 py-2 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-bold border border-[#C7CDD5]/40 flex items-center gap-1.5 cursor-pointer transition-all"
          >
            <Eye className="w-4 h-4" /> Open Full Diagnostic View <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>
    </div>
  );
};
