import React, { useState, useEffect } from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from '../components/PriorityBadge';
import { ConfidenceBar } from '../components/ConfidenceBar';
import { TriageExplanation } from '../components/TriageExplanation';
import { EvidenceEnrichmentPanel } from '../components/EvidenceEnrichmentPanel';

import { useObservationImage } from '../hooks/useObservationImage';
import {
  getObservationReviewState,
  recordReviewEvent,
  pinObservation,
  REVIEW_EVENT_CUSTOM_TYPE,
  type ReviewState
} from '../services/reviewEventsService';
import { ArrowLeft, CheckCircle2, AlertOctagon, UserCheck, Shield, Bot, Bookmark, ArrowRight, X } from 'lucide-react';

interface ObservationDetailPageProps {
  observation: Observation;
  onBack: () => void;
  onAskAI?: (observation: Observation) => void;
  onPinToQueue?: (observation: Observation) => void;
}

export const ObservationDetailPage: React.FC<ObservationDetailPageProps> = ({
  observation,
  onBack,
  onAskAI,
  onPinToQueue
}) => {
  const [reviewState, setReviewState] = useState<ReviewState>(() =>
    getObservationReviewState(observation.id)
  );
  const [showChoiceModal, setShowChoiceModal] = useState<boolean>(false);
  const { imageUrl: resolvedImageUrl, isFallback } = useObservationImage(observation);

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

  const handleAction = (action: 'APPROVE' | 'DEEP_ANALYSIS') => {
    const { state } = recordReviewEvent(observation.id, action, {
      priority: observation.priority,
      morphology: observation.broad_morphology
    });
    setReviewState(state);

    if (action === 'DEEP_ANALYSIS') {
      setShowChoiceModal(true);
    }
  };

  const isLive = observation.is_live;
  const triage = observation.triage_response;

  const triageSignals = {
    score: observation.anomaly_score,
    priority: observation.priority,
    novelty_score: triage?.novelty_score ?? observation.ood_score,
    uncertainty_score: triage?.uncertainty_score ?? (observation.confidence != null ? (1.0 - observation.confidence) / 0.75 : 0.5),
    oddity_score: triage?.oddity_score ?? observation.p_odd ?? triage?.scientific_attributes?.prob_odd,
    raw_embedding_distance: triage?.raw_embedding_distance,
    confidence: observation.confidence,
    p_odd: observation.p_odd ?? triage?.scientific_attributes?.prob_odd,
    predicted_class: observation.gz2class,
    nearest_reference_class: triage?.nearest_reference_class || observation.broad_morphology,
    model_version: triage?.model_version,
    domain_status: triage?.domain_validation?.decision,
    object_type: triage?.object_type || observation.object_type,
    morphology: triage?.morphology
  };

  const [imageError, setImageError] = useState(false);

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Navigation Top Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <button
          onClick={onBack}
          className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-800 transition-all flex items-center gap-2 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> BACK
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
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: High-Res Image Display & Probabilities */}
        <div className="lg:col-span-6 space-y-6">
          <div className="glass-panel p-4 rounded-xl border border-[#252D37] bg-[#070B11]/90 relative overflow-hidden">
            <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-black border border-slate-800 flex items-center justify-center">
              {resolvedImageUrl && !imageError && !isFallback ? (
                <img
                  src={resolvedImageUrl}
                  alt={observation.id}
                  className="w-full h-full object-cover"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950 text-slate-400 font-mono text-xs p-6 text-center space-y-3">
                  <AlertOctagon className="w-10 h-10 text-amber-400/80" />
                  <span className="font-semibold text-slate-300">Original image unavailable for this historical record</span>
                  <span className="text-[11px] text-slate-500 max-w-xs">The image binary was not found in browser storage or may have expired.</span>
                </div>
              )}

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

          {/* Model Morphology Probability Bars or Object Identification Evidence */}
          {(observation.object_type === 'Galaxy' || observation.object_type === 'GALAXY' || triage?.predicted_object_type === 'GALAXY') && observation.confidence != null && observation.confidence > 0 && observation.morphology_probs && observation.morphology_probs.length > 0 ? (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center justify-between">
                <span>MODEL MORPHOLOGY PROBABILITIES</span>
                <span className="text-xs font-normal text-emerald-400">MODEL CONFIDENCE: {observation.confidence != null ? `${(observation.confidence * 100).toFixed(1)}%` : 'N/A'}</span>
              </h3>

              <div className="space-y-3 pt-2">
                {observation.morphology_probs.map((prob) => {
                  const pVal = prob.probability ?? 0;
                  return (
                    <ConfidenceBar
                      key={prob.label}
                      label={prob.label}
                      value={pVal}
                      color={pVal > 0.7 ? 'silver' : pVal > 0.1 ? 'emerald' : 'amber'}
                    />
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-sm font-mono font-bold text-white tracking-wider flex items-center justify-between">
                <span>OBJECT IDENTIFICATION EVIDENCE</span>
                <span className="text-xs font-normal text-slate-400">STATUS: {triage?.object_type_status || 'EXPERIMENTAL_ZERO_SHOT'}</span>
              </h3>

              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                    <span className="text-slate-400 block text-[10px] uppercase">Experimental Visual Score</span>
                    <span className="text-cyan-300 font-bold text-sm">
                      {triage?.visual_similarity_score !== undefined && triage?.visual_similarity_score !== null
                        ? triage.visual_similarity_score.toFixed(2)
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="bg-[#0D1219] p-3 rounded border border-[#252D37]">
                    <span className="text-slate-400 block text-[10px] uppercase">Decision Margin</span>
                    <span className="text-emerald-300 font-bold text-sm">
                      {triage?.object_margin !== undefined && triage?.object_margin !== null
                        ? `+${triage.object_margin.toFixed(2)}`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-slate-900/80 rounded border border-slate-800 text-slate-300 text-[11px] leading-relaxed">
                  Galaxy Zoo morphology specialist was not executed because this target was resolved as a non-galaxy observation ({triage?.predicted_object_type || observation.object_type || 'Point source'}).
                </div>
              </div>
            </div>
          )}

          {/* Continuous Scientific Attributes (Real Model Prediction for Galaxy Targets) */}
          {(observation.object_type === 'Galaxy' || observation.object_type === 'GALAXY' || triage?.predicted_object_type === 'GALAXY') && triage?.scientific_attributes && (
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

          {/* Multi-Modal Evidence Enrichment Panel */}
          <EvidenceEnrichmentPanel
            observationId={observation.id}
            initialObjectType={triage?.predicted_object_type || observation.object_type}
            ra={observation.ra}
            dec={observation.dec}
          />

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

            {/* Action Buttons (Strictly 2 balanced buttons: APPROVE & DEEP ANALYSIS) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => handleAction('APPROVE')}
                disabled={reviewState === 'APPROVED'}
                className={`py-3 px-4 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 ${
                  reviewState === 'APPROVED'
                    ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-emerald-950 hover:text-emerald-200 hover:border-emerald-500/50'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                {reviewState === 'APPROVED' ? 'APPROVED' : 'APPROVE'}
              </button>

              <button
                onClick={() => handleAction('DEEP_ANALYSIS')}
                disabled={reviewState === 'DEEP_ANALYSIS_REQUESTED'}
                className={`py-3 px-4 rounded font-mono text-xs font-bold border transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 ${
                  reviewState === 'DEEP_ANALYSIS_REQUESTED'
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-950'
                    : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-indigo-950 hover:text-indigo-200 hover:border-indigo-500/50'
                }`}
              >
                <AlertOctagon className="w-4 h-4" />
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
                  {reviewState === 'DEEP_ANALYSIS_REQUESTED' && `Observation ${observation.id} has been flagged for further scientific analysis.`}
                  {reviewState === 'REVIEW_PENDING' && `Observation ${observation.id} is queued in ASTRA for human scientific review.`}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* DEEP ANALYSIS CHOICE MODAL OVERLAY */}
      {showChoiceModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="relative w-full max-w-lg bg-[#090D14] border border-[#21133B] rounded-2xl p-6 space-y-6 shadow-2xl text-[#ECEAF2]">
            {/* Header with Close X */}
            <div className="flex items-start justify-between border-b border-[#21133B] pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-lg font-bold font-serif-display text-white tracking-wider">
                    Further Analysis Required
                  </h3>
                </div>
                <p className="text-xs text-[#8E8A9D] font-sans-ui">
                  ASTRA has flagged this observation for deeper investigation. Choose how you want to continue.
                </p>
              </div>
              <button
                onClick={() => setShowChoiceModal(false)}
                className="p-1.5 rounded-lg bg-[#15102A] text-slate-400 hover:text-white border border-[#21133B] transition-colors cursor-pointer"
                title="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Choice Buttons */}
            <div className="space-y-4">
              {/* Choice 1: ASK ASTRA AI */}
              <button
                onClick={() => {
                  setShowChoiceModal(false);
                  if (onAskAI) {
                    onAskAI(observation);
                  }
                }}
                className="w-full text-left p-4 rounded-xl bg-[#15102A] hover:bg-[#21133B] border border-[#9B7FD4]/40 hover:border-[#9B7FD4] transition-all group cursor-pointer space-y-1.5 shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[#8FD3FF] group-hover:text-white flex items-center gap-2">
                    <Bot className="w-4 h-4 text-[#8FD3FF]" />
                    [ ASK ASTRA AI ]
                  </span>
                  <ArrowRight className="w-4 h-4 text-[#8E8A9D] group-hover:text-white group-hover:translate-x-1 transition-transform" />
                </div>
                <p className="text-xs text-[#8E8A9D] group-hover:text-slate-200 font-sans-ui leading-relaxed">
                  Open this observation in ASTRA Space Help AI for a detailed scientific explanation and follow-up questions.
                </p>
              </button>

              {/* Choice 2: ADD TO ANOMALY QUEUE */}
              <button
                onClick={() => {
                  setShowChoiceModal(false);
                  pinObservation(observation.id);
                  if (onPinToQueue) {
                    onPinToQueue(observation);
                  }
                }}
                className="w-full text-left p-4 rounded-xl bg-[#15102A] hover:bg-[#21133B] border border-[#9B7FD4]/40 hover:border-[#9B7FD4] transition-all group cursor-pointer space-y-1.5 shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-amber-300 group-hover:text-amber-200 flex items-center gap-2">
                    <Bookmark className="w-4 h-4 text-amber-400" />
                    [ ADD TO ANOMALY QUEUE ]
                  </span>
                  <ArrowRight className="w-4 h-4 text-[#8E8A9D] group-hover:text-white group-hover:translate-x-1 transition-transform" />
                </div>
                <p className="text-xs text-[#8E8A9D] group-hover:text-slate-200 font-sans-ui leading-relaxed">
                  Pin this observation to the Anomaly Queue for further investigation.
                </p>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

