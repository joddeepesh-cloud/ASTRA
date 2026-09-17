import React, { useState, useMemo, useEffect } from 'react';
import type { Observation, PriorityLevel } from '../types';
import libraryData from '../data/observationLibrary.json';
import { getAnalysisHistory } from '../services/analysisHistory';
import {
  getAllObservationReviewStates,
  REVIEW_EVENT_CUSTOM_TYPE
} from '../services/reviewEventsService';
import { generateTriageExplanation } from '../utils/triageExplanation';
import { PriorityBadge } from '../components/PriorityBadge';
import { EmptyState } from '../components/EmptyState';
import { TriageExplanation } from '../components/TriageExplanation';
import {
  ShieldAlert,
  Filter,
  ArrowUpDown,
  ExternalLink,
  Cpu,
  AlertTriangle,
  Layers,
  Inbox,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  UserCheck,
  X
} from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

interface AnomalyQueuePageProps {
  onInspectObservation: (obs: Observation) => void;
}

export const AnomalyQueuePage: React.FC<AnomalyQueuePageProps> = ({ onInspectObservation }) => {
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [reviewFilter, setReviewFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'anomaly_score' | 'confidence' | 'time'>('anomaly_score');
  const [reviewStates, setReviewStates] = useState<Record<string, string>>(() => getAllObservationReviewStates());
  const [expandedObsId, setExpandedObsId] = useState<string | null>(null);
  const [modalObs, setModalObs] = useState<Observation | null>(null);

  useEffect(() => {
    const syncStates = () => {
      setReviewStates(getAllObservationReviewStates());
    };
    window.addEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncStates);
    return () => {
      window.removeEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncStates);
    };
  }, []);

  // Complete genuine observations dataset: Curated GZ2 dataset + user analysis runs
  const allObservations = useMemo(() => {
    const userHistory = getAnalysisHistory();
    const userRuns: Observation[] = userHistory.map((rec) => ({
      id: rec.observation_id,
      dr7objid: 'USER-UPLOAD',
      asset_id: 999999,
      ra: 0.0,
      dec: 0.0,
      gz2class: rec.morphology,
      broad_morphology: rec.morphology === 'SPIRAL' ? 'SPIRAL' : rec.morphology === 'SMOOTH' ? 'SMOOTH' : 'DISK_FEATURE',
      object_type: (rec.object_type === 'GALAXY' || rec.object_type === 'Galaxy' || rec.filename?.startsWith('LIB-')) ? 'Galaxy' : 'Unresolved astronomical source',
      confidence: rec.confidence,
      anomaly_score: rec.triage_score,
      ood_score: rec.triage_score,
      priority: rec.priority,
      catalog_status: 'UNCHECKED',
      catalog_name: rec.filename,
      observation_time: rec.timestamp,
      image_url: rec.image_url || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23070B11"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%238FAFC2" font-size="10" font-family="monospace">USER FILE</text></svg>',
      explanation: `User observation cutout ${rec.filename} analyzed in Research Mode.`,
      morphology_probs: [{ label: rec.morphology, probability: rec.confidence }],
      is_demo: false,
      is_live: true,
      triage_response: rec.triage_response
    }));

    return [...userRuns, ...LIBRARY_OBSERVATIONS];
  }, []);

  // Operational metrics derived from genuine dataset
  const metrics = useMemo(() => {
    const totalCount = allObservations.length;
    const criticalCount = allObservations.filter((o) => o.priority === 'CRITICAL').length;
    const highCount = allObservations.filter((o) => o.priority === 'HIGH').length;
    const mediumCount = allObservations.filter((o) => o.priority === 'MEDIUM').length;
    const lowCount = allObservations.filter((o) => o.priority === 'LOW').length;

    const pendingReviewCount = allObservations.filter((o) => (reviewStates[o.id] || 'UNREVIEWED') === 'REVIEW_PENDING').length;
    const approvedCount = allObservations.filter((o) => reviewStates[o.id] === 'APPROVED').length;
    const deepAnalysisCount = allObservations.filter((o) => reviewStates[o.id] === 'DEEP_ANALYSIS_REQUESTED').length;

    return {
      totalCount,
      criticalCount,
      highCount,
      mediumCount,
      lowCount,
      pendingReviewCount,
      approvedCount,
      deepAnalysisCount
    };
  }, [allObservations, reviewStates]);

  // Filtered and sorted queue items
  const filteredObservations = useMemo(() => {
    return allObservations
      .filter((obs) => {
        if (priorityFilter !== 'ALL' && obs.priority !== priorityFilter) {
          return false;
        }
        const state = reviewStates[obs.id] || 'UNREVIEWED';
        if (reviewFilter === 'REVIEW_PENDING' && state !== 'REVIEW_PENDING') return false;
        if (reviewFilter === 'APPROVED' && state !== 'APPROVED') return false;
        if (reviewFilter === 'DEEP_ANALYSIS' && state !== 'DEEP_ANALYSIS_REQUESTED') return false;
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'anomaly_score') return b.anomaly_score - a.anomaly_score;
        if (sortBy === 'confidence') return (b.confidence ?? 0) - (a.confidence ?? 0);
        return new Date(b.observation_time).getTime() - new Date(a.observation_time).getTime();
      });
  }, [allObservations, priorityFilter, reviewFilter, sortBy, reviewStates]);

  const toggleExpand = (obsId: string) => {
    setExpandedObsId(expandedObsId === obsId ? null : obsId);
  };

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-6xl mx-auto font-sans-ui text-[#ECEAF2]" data-tour="anomaly-queue-page">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21133B] pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold font-serif-display text-white tracking-wider uppercase flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-400" /> ANOMALY QUEUE
            </h1>
            <span className="text-xs font-mono-tech bg-[#21133B] text-rose-300 border border-rose-500/40 px-2.5 py-0.5 rounded font-bold">
              TRIAGE CONSOLE
            </span>
          </div>
          <p className="text-xs text-[#8E8A9D] font-sans-ui mt-1">
            Astronomical observations prioritized for scientific review by ASTRA's out-of-distribution triage pipeline.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800 self-start md:self-auto">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-slate-300 font-semibold">STREAM:</span>
            <span className="text-emerald-400 font-bold">ACTIVE OBSERVATIONS & SESSION RUNS</span>
          </div>
        </div>
      </div>

      {/* Operational Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setPriorityFilter(priorityFilter === 'CRITICAL' ? 'ALL' : 'CRITICAL')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'CRITICAL'
              ? 'border-purple-500 bg-purple-950/40 shadow-lg shadow-purple-950/30'
              : 'border-slate-800 hover:border-purple-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-purple-400">CRITICAL PRIORITY</span>
            <AlertTriangle className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{metrics.criticalCount}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Top OOD Divergence Target</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'HIGH' ? 'ALL' : 'HIGH')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'HIGH'
              ? 'border-rose-500 bg-rose-950/40 shadow-lg shadow-rose-950/30'
              : 'border-slate-800 hover:border-rose-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-rose-400">HIGH PRIORITY</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{metrics.highCount}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Scientific Review Required</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'MEDIUM' ? 'ALL' : 'MEDIUM')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'MEDIUM'
              ? 'border-amber-500 bg-amber-950/40 shadow-lg shadow-amber-950/30'
              : 'border-slate-800 hover:border-amber-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-amber-400">MEDIUM PRIORITY</span>
            <Layers className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{metrics.mediumCount}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Secondary Review Queue</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'LOW' ? 'ALL' : 'LOW')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'LOW'
              ? 'border-emerald-500 bg-emerald-950/40 shadow-lg shadow-emerald-950/30'
              : 'border-slate-800 hover:border-emerald-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-emerald-400">LOW PRIORITY</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{metrics.lowCount}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Standard Reference Baseline</div>
        </div>
      </div>

      {/* Filter and Sort Toolbar */}
      <div className="space-y-3 bg-slate-900/90 p-4 rounded-xl border border-slate-800">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          {/* Priority Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs font-mono text-slate-400">PRIORITY:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all cursor-pointer ${
                  priorityFilter === p
                    ? 'bg-rose-950 text-rose-300 border border-rose-500/50 font-bold'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-950/60 border border-slate-800'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-2 self-start lg:self-auto">
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-mono text-slate-400">SORT BY:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 font-mono text-xs text-slate-200 focus:outline-none focus:border-rose-500/50 cursor-pointer"
            >
              <option value="anomaly_score">Triage Anomaly Score (High → Low)</option>
              <option value="confidence">Model Confidence (High → Low)</option>
              <option value="time">Observation Time (Recent First)</option>
            </select>
          </div>
        </div>

        {/* Review Status Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
          <UserCheck className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-xs font-mono text-slate-400">HUMAN REVIEW STATUS:</span>
          {[
            { key: 'ALL', label: 'ALL' },
            { key: 'REVIEW_PENDING', label: `REVIEW PENDING (${metrics.pendingReviewCount})` },
            { key: 'APPROVED', label: `APPROVED (${metrics.approvedCount})` },
            { key: 'DEEP_ANALYSIS', label: `DEEP ANALYSIS (${metrics.deepAnalysisCount})` }
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setReviewFilter(item.key)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-all cursor-pointer ${
                reviewFilter === item.key
                  ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/50 font-bold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-950/60 border border-slate-800'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Unified Queue Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/70 flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            ANOMALY QUEUE ({filteredObservations.length} OBSERVATIONS)
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            TOTAL IN ARCHIVE & SESSION: {allObservations.length}
          </span>
        </div>

        {filteredObservations.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="NO OBSERVATIONS MATCH CURRENT FILTER"
            description="Adjust your priority or human review status filter above, or process custom cutouts in Research Mode."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  <th className="p-3.5">TARGET ID</th>
                  <th className="p-3.5">PRIORITY</th>
                  <th className="p-3.5">CLASSIFICATION</th>
                  <th className="p-3.5 text-center">ANOMALY SCORE</th>
                  <th className="p-3.5">WHY PRIORITIZED</th>
                  <th className="p-3.5">REVIEW STATUS</th>
                  <th className="p-3.5 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                {filteredObservations.map((obs) => {
                  const rState = reviewStates[obs.id] || 'UNREVIEWED';
                  const isExpanded = expandedObsId === obs.id;

                  const triageInput = {
                    score: obs.anomaly_score,
                    priority: obs.priority as PriorityLevel,
                    novelty_score: obs.triage_response?.novelty_score ?? obs.ood_score,
                    uncertainty_score: obs.triage_response?.uncertainty_score ?? (obs.confidence != null ? (1.0 - obs.confidence) / 0.75 : 0.5),
                    oddity_score: obs.triage_response?.oddity_score ?? obs.p_odd ?? (obs.triage_response?.scientific_attributes?.prob_odd),
                    raw_embedding_distance: obs.triage_response?.raw_embedding_distance,
                    confidence: obs.confidence,
                    p_odd: obs.p_odd ?? obs.triage_response?.scientific_attributes?.prob_odd,
                    predicted_class: obs.gz2class,
                    nearest_reference_class: obs.triage_response?.nearest_reference_class || obs.broad_morphology,
                    model_version: obs.triage_response?.model_version,
                    scientific_attributes: obs.triage_response?.scientific_attributes
                  };

                  const expResult = generateTriageExplanation(triageInput);

                  return (
                    <React.Fragment key={obs.id}>
                      <tr className={`transition-colors ${isExpanded ? 'bg-[#15102A]/80' : 'hover:bg-[#15102A]/40'}`}>
                        {/* ID + Thumbnail */}
                        <td className="p-3.5 font-bold text-white">
                          <div className="flex items-center gap-3">
                            <img
                              src={obs.image_url}
                              alt={obs.id}
                              className="w-10 h-10 rounded object-cover border border-slate-700 bg-black shrink-0"
                            />
                            <div>
                              <span className="font-bold text-white block">{obs.id}</span>
                              <span className="text-[10px] text-slate-400 font-sans">{obs.dr7objid}</span>
                            </div>
                          </div>
                        </td>

                        {/* Priority */}
                        <td className="p-3.5">
                          <PriorityBadge priority={obs.priority as PriorityLevel} />
                        </td>

                        {/* Classification */}
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded bg-[#0D0A1C] text-[#8FD3FF] border border-[#21133B] font-semibold">
                            {obs.broad_morphology}
                          </span>
                          <span className="text-[10px] text-slate-500 block">({obs.gz2class})</span>
                        </td>

                        {/* Anomaly Score */}
                        <td className="p-3.5 text-center font-bold">
                          <span className={obs.anomaly_score >= 0.7 ? 'text-rose-400 font-extrabold' : obs.anomaly_score >= 0.5 ? 'text-amber-400' : 'text-emerald-400'}>
                            {obs.anomaly_score.toFixed(2)}
                          </span>
                        </td>

                        {/* Why Prioritized */}
                        <td className="p-3.5 max-w-xs">
                          <button
                            onClick={() => toggleExpand(obs.id)}
                            className="text-[11px] text-[#8FD3FF] hover:text-white transition-colors flex items-center gap-1 cursor-pointer text-left font-sans-ui"
                            title="Toggle triage reasoning"
                          >
                            <Sparkles className="w-3.5 h-3.5 text-[#D6A84F] shrink-0" />
                            <span className="truncate">{expResult.interpretation.primaryReason.replace(/^Primary reason:?\s*/i, '')}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5 shrink-0 text-[#8FD3FF]" /> : <ChevronDown className="w-3.5 h-3.5 shrink-0 text-[#8E8A9D]" />}
                          </button>
                        </td>

                        {/* Review Status */}
                        <td className="p-3.5">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                              rState === 'APPROVED'
                                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50'
                                : rState === 'DEEP_ANALYSIS_REQUESTED'
                                ? 'bg-indigo-950/80 text-indigo-300 border-indigo-500/50'
                                : rState === 'REVIEW_PENDING'
                                ? 'bg-amber-950/80 text-amber-300 border-amber-500/50'
                                : 'bg-slate-900 text-slate-400 border-slate-800'
                            }`}
                          >
                            {rState.replace(/_/g, ' ')}
                          </span>
                        </td>

                        {/* Actions */}
                        <td className="p-3.5 text-right space-x-2">
                          <button
                            onClick={() => setModalObs(obs)}
                            className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-[#8FAFC2] hover:text-white border border-slate-800 transition-all text-[11px] inline-flex items-center gap-1 cursor-pointer"
                          >
                            <HelpCircle className="w-3 h-3 text-amber-400" />
                            Why Flagged?
                          </button>

                          <button
                            onClick={() => onInspectObservation(obs)}
                            className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] hover:text-white font-mono text-[11px] font-semibold border border-[#4B5563]/60 transition-all inline-flex items-center gap-1 cursor-pointer"
                          >
                            DOSSIER <ExternalLink className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>

                      {/* Expanded In-Line Triage Explanation Row */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="p-4 bg-[#05080E] border-b border-slate-800">
                            <TriageExplanation signals={triageInput} />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Triage Reasoning Modal Overlay */}
      {modalObs && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl bg-[#090D14] border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-mono font-bold text-white tracking-wider">
                  TRIAGE REASONING: {modalObs.id}
                </h3>
                <PriorityBadge priority={modalObs.priority as PriorityLevel} />
              </div>

              <button
                onClick={() => setModalObs(null)}
                className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white border border-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <TriageExplanation
              signals={{
                score: modalObs.anomaly_score,
                priority: modalObs.priority as PriorityLevel,
                novelty_score: modalObs.triage_response?.novelty_score ?? modalObs.ood_score,
                uncertainty_score: modalObs.triage_response?.uncertainty_score ?? (modalObs.confidence != null ? (1.0 - modalObs.confidence) / 0.75 : 0.5),
                oddity_score: modalObs.triage_response?.oddity_score ?? modalObs.p_odd ?? modalObs.triage_response?.scientific_attributes?.prob_odd,
                raw_embedding_distance: modalObs.triage_response?.raw_embedding_distance,
                confidence: modalObs.confidence,
                p_odd: modalObs.p_odd ?? modalObs.triage_response?.scientific_attributes?.prob_odd,
                predicted_class: modalObs.gz2class,
                nearest_reference_class: modalObs.triage_response?.nearest_reference_class || modalObs.broad_morphology,
                model_version: modalObs.triage_response?.model_version
              }}
            />

            <div className="text-right">
              <button
                onClick={() => {
                  const target = modalObs;
                  setModalObs(null);
                  onInspectObservation(target);
                }}
                className="px-4 py-2 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-200 border border-rose-800 font-mono text-xs font-bold inline-flex items-center gap-1.5 cursor-pointer"
              >
                INSPECT FULL DOSSIER <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
