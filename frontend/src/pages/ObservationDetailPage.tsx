import React, { useState } from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from '../components/PriorityBadge';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { ArrowLeft, Sparkles, Database, CheckCircle2, AlertOctagon, UserCheck } from 'lucide-react';

interface ObservationDetailPageProps {
  observation: Observation;
  onBack: () => void;
}

export const ObservationDetailPage: React.FC<ObservationDetailPageProps> = ({ observation, onBack }) => {
  const [reviewStatus, setReviewStatus] = useState<'PENDING' | 'APPROVED' | 'FLAGGED'>('PENDING');

  const isLive = observation.is_live;
  const triage = observation.triage_response;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Navigation Top Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <button
          onClick={onBack}
          className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-800 transition-all flex items-center gap-2 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> BACK TO MISSION DASHBOARD
        </button>

        <div className="flex items-center gap-3">
          {isLive ? (
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-500/40 px-2.5 py-1 rounded font-bold">
              LIVE UPLOAD ANALYSIS
            </span>
          ) : (
            <span className="text-xs font-mono text-amber-400/90 bg-amber-950/40 border border-amber-500/30 px-2.5 py-1 rounded">
              MISSION ARCHIVE RECORD
            </span>
          )}
          <PriorityBadge priority={observation.priority} />
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: High-Res Image Display */}
        <div className="lg:col-span-7 space-y-4">
          <div className="glass-panel p-4 rounded-xl border border-cyan-900/40 bg-slate-950/90 relative overflow-hidden">
            <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-black border border-slate-800">
              <img
                src={observation.image_url}
                alt={observation.id}
                className="w-full h-full object-cover"
              />

              {/* Overlaid Coordinate HUD */}
              <div className="absolute top-4 left-4 bg-slate-950/80 border border-cyan-900/50 p-2.5 rounded font-mono text-xs text-cyan-300 space-y-1 backdrop-blur-md">
                {isLive ? (
                  <>
                    <div>SOURCE: USER UPLOAD</div>
                    <div>STATUS: REAL-TIME INFERENCE</div>
                    <div>ID: {observation.id}</div>
                  </>
                ) : (
                  <>
                    <div>RA: {observation.ra.toFixed(6)}°</div>
                    <div>DEC: {observation.dec.toFixed(6)}°</div>
                    <div>OBJID: {observation.dr7objid}</div>
                  </>
                )}
              </div>

              <div className="absolute bottom-4 right-4 bg-slate-950/80 border border-slate-800 px-3 py-1.5 rounded font-mono text-xs text-slate-300 backdrop-blur-md">
                SPLIT: <span className="text-amber-400">{observation.split?.toUpperCase() || 'LIVE'}</span>
              </div>
            </div>
          </div>

          {/* Model Morphology Probability Bars */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center justify-between">
              <span>MODEL MORPHOLOGY PROBABILITIES</span>
              <span className="text-xs font-normal text-emerald-400">MODEL CONFIDENCE: {(observation.confidence * 100).toFixed(1)}%</span>
            </h3>

            <div className="space-y-3 pt-2">
              {observation.morphology_probs.map((prob) => (
                <ConfidenceBar
                  key={prob.label}
                  label={prob.label}
                  value={prob.probability}
                  color={prob.probability > 0.7 ? 'cyan' : prob.probability > 0.1 ? 'emerald' : 'amber'}
                />
              ))}
            </div>
          </div>

          {/* Continuous Scientific Attributes (Real Model Prediction) */}
          {triage?.scientific_attributes && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-mono font-bold text-white tracking-wider">
                SCIENTIFIC ATTRIBUTE HEAD PREDICTIONS
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Smooth</span>
                  <span className="text-cyan-300 font-bold text-sm">{(triage.scientific_attributes.prob_smooth * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Features / Disk</span>
                  <span className="text-cyan-300 font-bold text-sm">{(triage.scientific_attributes.prob_features * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Edge-on</span>
                  <span className="text-cyan-300 font-bold text-sm">{(triage.scientific_attributes.prob_edgeon * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Spiral Arms</span>
                  <span className="text-cyan-300 font-bold text-sm">{(triage.scientific_attributes.prob_spiral * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Bar Structure</span>
                  <span className="text-cyan-300 font-bold text-sm">{(triage.scientific_attributes.prob_bar * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                  <span className="text-slate-400 block">Odd / Irregular</span>
                  <span className="text-amber-400 font-bold text-sm">{(triage.scientific_attributes.prob_odd * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Scientific Summary & Diagnostic Analysis */}
        <div className="lg:col-span-5 space-y-6">
          {/* Summary Box */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="border-b border-slate-800 pb-3 flex justify-between items-start">
              <div>
                <span className="text-xs font-mono text-slate-400">TARGET DESIGNATION</span>
                <h2 className="text-2xl font-bold font-mono text-white tracking-tight">{observation.id}</h2>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-slate-400">ASTRA TRIAGE SCORE</span>
                <div className="text-2xl font-mono font-bold text-cyan-300">{observation.anomaly_score.toFixed(2)}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-500 block">PREDICTED CLASS</span>
                <span className="text-cyan-300 font-bold text-sm">{observation.gz2class}</span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-500 block">NOVELTY SCORE</span>
                <span className="text-amber-400 font-bold text-sm">{observation.ood_score.toFixed(2)}</span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-500 block">DOWNLINK PRIORITY</span>
                <span className="text-rose-400 font-bold text-sm">{observation.priority}</span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
                <span className="text-slate-500 block">CATALOG STATUS</span>
                <span className="text-emerald-400 font-bold text-sm truncate block">{observation.catalog_status}</span>
              </div>
            </div>
          </div>

          {/* Why ASTRA Flagged This */}
          <div className="glass-panel p-6 rounded-xl border border-cyan-900/30 space-y-3 bg-slate-950/80">
            <h3 className="text-sm font-mono font-bold text-cyan-300 tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              DETERMINISTIC SCIENTIFIC TRIAGE EXPLANATION
            </h3>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {observation.explanation}
            </p>
            <div className="pt-2 text-[10px] font-mono text-cyan-400/90 bg-cyan-950/30 p-2 rounded border border-cyan-500/20">
              {isLive
                ? `REAL FASTAPI PIPELINE: Inference latency ${triage?.inference_time_ms}ms | Total Triage ${triage?.total_triage_ms}ms`
                : 'MISSION ARCHIVE EXPLANATION: Generated by statistical manifold feature distance logic.'}
            </div>
          </div>

          {/* Scientific Disclaimer */}
          {triage?.score_interpretation && (
            <div className="p-3.5 bg-amber-950/30 rounded-lg border border-amber-500/20 text-xs font-sans text-amber-200/90 leading-relaxed">
              {triage.score_interpretation}
            </div>
          )}

          {/* Catalog Cross-Match Section */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              CATALOG CROSS-MATCH & ALIGNMENT
            </h3>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2.5 bg-slate-900/60 rounded border border-slate-800">
                <span className="text-slate-400">Nearest Ref Centroid Class:</span>
                <span className="text-cyan-300">{triage?.nearest_reference_class || observation.broad_morphology}</span>
              </div>
              <div className="flex justify-between p-2.5 bg-slate-900/60 rounded border border-slate-800">
                <span className="text-slate-400">Catalog Entry:</span>
                <span className="text-amber-400">{observation.catalog_name || 'Unregistered User Upload'}</span>
              </div>
            </div>
          </div>

          {/* Scientific Review Action Panel */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-400" />
              HUMAN SCIENTIFIC REVIEW DECISION
            </h3>

            <div className="flex gap-2">
              <button
                onClick={() => setReviewStatus('APPROVED')}
                className={`flex-1 py-2.5 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  reviewStatus === 'APPROVED'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" /> APPROVE DOWNLINK
              </button>

              <button
                onClick={() => setReviewStatus('FLAGGED')}
                className={`flex-1 py-2.5 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  reviewStatus === 'FLAGGED'
                    ? 'bg-rose-600 text-white border-rose-500 shadow-md shadow-rose-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <AlertOctagon className="w-4 h-4" /> FLAG DEEP ANALYSIS
              </button>
            </div>

            {reviewStatus !== 'PENDING' && (
              <div className="p-3 bg-slate-900/90 rounded border border-slate-800 text-xs font-mono text-emerald-400 text-center">
                Review Decision Logged: {reviewStatus} by Lead Astronomer.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
