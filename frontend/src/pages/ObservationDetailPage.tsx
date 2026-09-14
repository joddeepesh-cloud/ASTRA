import React, { useState, useEffect } from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from '../components/PriorityBadge';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { TriageExplanation } from '../components/TriageExplanation';
import {
  getObservationReviewState,
  recordReviewEvent,
  REVIEW_EVENT_CUSTOM_TYPE,
  type ReviewState
} from '../services/reviewEventsService';
import { ArrowLeft, Database, CheckCircle2, AlertOctagon, UserCheck, Shield, FileSearch } from 'lucide-react';

interface ObservationDetailPageProps {
  observation: Observation;
  onBack: () => void;
}

export const ObservationDetailPage: React.FC<ObservationDetailPageProps> = ({ observation, onBack }) => {
  const [reviewState, setReviewState] = useState<ReviewState>(() =>
    getObservationReviewState(observation.id)
  );

  useEffect(() => {
    // Sync review state whenever observation changes or custom review event triggers
    setReviewState(getObservationReviewState(observation.id));

    const handleStateUpdate = () => {
      setReviewState(getObservationReviewState(observation.id));
    };

    window.addEventListener(REVIEW_EVENT_CUSTOM_TYPE, handleStateUpdate);
    return () => {
      window.removeEventListener(REVIEW_EVENT_CUSTOM_TYPE, handleStateUpdate);
    };
  }, [observation.id]);

  const handleAction = (action: 'HUMAN_REVIEW' | 'APPROVE' | 'DEEP_ANALYSIS') => {
    const { state } = recordReviewEvent(observation.id, action, {
      priority: observation.priority,
      morphology: observation.broad_morphology
    });
    setReviewState(state);
  };

  const isLive = observation.is_live;
  const triage = observation.triage_response;

  const triageSignals = {
    score: observation.anomaly_score,
    priority: observation.priority,
    novelty_score: triage?.novelty_score ?? observation.ood_score,
    uncertainty_score: triage?.uncertainty_score ?? (1.0 - observation.confidence) / 0.75,
    oddity_score: triage?.oddity_score ?? observation.p_odd ?? triage?.scientific_attributes?.prob_odd,
    raw_embedding_distance: triage?.raw_embedding_distance,
    confidence: observation.confidence,
    p_odd: observation.p_odd ?? triage?.scientific_attributes?.prob_odd,
    predicted_class: observation.gz2class,
    nearest_reference_class: triage?.nearest_reference_class || observation.broad_morphology,
    model_version: triage?.model_version
  };

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
            <span className="text-xs font-mono text-[#D5DAE0] bg-[#151B23]/80 border border-[#4B5563]/60 px-2.5 py-1 rounded font-bold">
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
        {/* Left Column: High-Res Image Display & Probabilities */}
        <div className="lg:col-span-6 space-y-6">
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] bg-[#070B11]/90 relative overflow-hidden">
            <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-black border border-slate-800">
              <img
                src={observation.image_url}
                alt={observation.id}
                className="w-full h-full object-cover"
              />

              {/* Overlaid Coordinate HUD */}
              <div className="absolute top-4 left-4 bg-[#070B11]/90 border border-[#4B5563]/50 p-2.5 rounded font-mono text-xs text-[#D5DAE0] space-y-1 backdrop-blur-md">
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
                  color={prob.probability > 0.7 ? 'silver' : prob.probability > 0.1 ? 'emerald' : 'amber'}
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
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Smooth</span>
                  <span className="text-[#D5DAE0] font-bold text-sm">{(triage.scientific_attributes.prob_smooth * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Features / Disk</span>
                  <span className="text-[#D5DAE0] font-bold text-sm">{(triage.scientific_attributes.prob_features * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Edge-on</span>
                  <span className="text-[#D5DAE0] font-bold text-sm">{(triage.scientific_attributes.prob_edgeon * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Spiral Arms</span>
                  <span className="text-[#D5DAE0] font-bold text-sm">{(triage.scientific_attributes.prob_spiral * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Bar Structure</span>
                  <span className="text-[#D5DAE0] font-bold text-sm">{(triage.scientific_attributes.prob_bar * 100).toFixed(1)}%</span>
                </div>
                <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                  <span className="text-slate-400 block">Odd / Irregular</span>
                  <span className="text-amber-400 font-bold text-sm">{(triage.scientific_attributes.prob_odd * 100).toFixed(1)}%</span>
                </div>
              </div>
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
                <span className="text-[#8FAFC2]">{triage?.nearest_reference_class || observation.broad_morphology}</span>
              </div>
              <div className="flex justify-between p-2.5 bg-slate-900/60 rounded border border-slate-800">
                <span className="text-slate-400">Catalog Entry:</span>
                <span className="text-amber-400">{observation.catalog_name || 'Unregistered User Upload'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Triage Explanation & Human Review Controls */}
        <div className="lg:col-span-6 space-y-6">
          {/* Target Header */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 flex justify-between items-center">
            <div>
              <span className="text-xs font-mono text-slate-400 block">TARGET DESIGNATION</span>
              <h2 className="text-2xl font-bold font-mono text-white tracking-tight">{observation.id}</h2>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono text-slate-400 block">PREDICTED MORPHOLOGY</span>
              <span className="text-lg font-mono font-bold text-[#8FAFC2]">{observation.gz2class}</span>
            </div>
          </div>

          {/* Interactive Dynamic Triage Explanation Component */}
          <TriageExplanation signals={triageSignals} />

          {/* Scientific Review Action Panel */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-400" />
                HUMAN SCIENTIFIC REVIEW DECISION
              </h3>

              {/* Status Badge */}
              <span
                className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded border uppercase tracking-wider ${
                  reviewState === 'APPROVED'
                    ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50'
                    : reviewState === 'DEEP_ANALYSIS_REQUESTED'
                    ? 'bg-indigo-950/80 text-indigo-300 border-indigo-500/50'
                    : reviewState === 'REVIEW_PENDING'
                    ? 'bg-amber-950/80 text-amber-300 border-amber-500/50'
                    : 'bg-slate-900 text-slate-400 border-slate-800'
                }`}
              >
                STATUS: {reviewState.replace(/_/g, ' ')}
              </span>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button
                onClick={() => handleAction('HUMAN_REVIEW')}
                disabled={reviewState === 'REVIEW_PENDING'}
                className={`py-2.5 px-3 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 ${
                  reviewState === 'REVIEW_PENDING'
                    ? 'bg-amber-950/60 text-amber-300 border-amber-500/50 shadow-md'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <FileSearch className="w-3.5 h-3.5" />
                {reviewState === 'REVIEW_PENDING' ? 'REVIEW PENDING' : 'HUMAN REVIEW'}
              </button>

              <button
                onClick={() => handleAction('APPROVE')}
                disabled={reviewState === 'APPROVED'}
                className={`py-2.5 px-3 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 ${
                  reviewState === 'APPROVED'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-emerald-950 hover:text-emerald-200'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                {reviewState === 'APPROVED' ? 'APPROVED' : 'APPROVE'}
              </button>

              <button
                onClick={() => handleAction('DEEP_ANALYSIS')}
                disabled={reviewState === 'DEEP_ANALYSIS_REQUESTED'}
                className={`py-2.5 px-3 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 ${
                  reviewState === 'DEEP_ANALYSIS_REQUESTED'
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-indigo-950 hover:text-indigo-200'
                }`}
              >
                <AlertOctagon className="w-3.5 h-3.5" />
                {reviewState === 'DEEP_ANALYSIS_REQUESTED' ? 'DEEP ANALYSIS' : 'DEEP ANALYSIS'}
              </button>
            </div>

            {/* Review Status Log Notice */}
            {reviewState !== 'UNREVIEWED' && (
              <div className="p-3 bg-slate-900/90 rounded border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                <div className="flex items-center gap-2 font-bold text-[#8FAFC2]">
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  <span>ASTRA REVIEW DECISION RECORDED</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {reviewState === 'APPROVED' && `ASTRA recorded your approval for observation ${observation.id} for continued scientific workflow.`}
                  {reviewState === 'DEEP_ANALYSIS_REQUESTED' && `ASTRA recorded observation ${observation.id} for deeper scientific follow-up.`}
                  {reviewState === 'REVIEW_PENDING' && `Observation ${observation.id} is queued in ASTRA for human scientific review.`}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
