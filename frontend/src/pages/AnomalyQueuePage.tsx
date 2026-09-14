import React, { useState, useMemo, useEffect } from 'react';
import type { Observation, PriorityLevel } from '../types';
import libraryData from '../data/observationLibrary.json';
import { getAnalysisHistory } from '../services/analysisHistory';
import {
  getAllObservationReviewStates,
  REVIEW_EVENT_CUSTOM_TYPE
} from '../services/reviewEventsService';
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
  Sparkles
} from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

interface AnomalyQueuePageProps {
  onInspectObservation: (obs: Observation) => void;
}

export const AnomalyQueuePage: React.FC<AnomalyQueuePageProps> = ({ onInspectObservation }) => {
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'anomaly_score' | 'confidence' | 'time'>('anomaly_score');
  const [reviewStates, setReviewStates] = useState<Record<string, string>>(() => getAllObservationReviewStates());
  const [expandedObsId, setExpandedObsId] = useState<string | null>(null);

  useEffect(() => {
    const syncStates = () => {
      setReviewStates(getAllObservationReviewStates());
    };
    window.addEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncStates);
    return () => {
      window.removeEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncStates);
    };
  }, []);

  // Genuine queue dataset: High & Critical priority targets (Canonical Thresholds)
  const queueObservations = useMemo(() => {
    const userHistory = getAnalysisHistory();
    const userRunsHighPriority: Observation[] = userHistory
      .filter((rec) => rec.priority === 'HIGH' || rec.priority === 'CRITICAL')
      .map((rec) => ({
        id: rec.observation_id,
        dr7objid: 'USER-UPLOAD',
        asset_id: 999999,
        ra: 0.0,
        dec: 0.0,
        gz2class: rec.morphology,
        broad_morphology: rec.morphology === 'SPIRAL' ? 'SPIRAL' : rec.morphology === 'SMOOTH' ? 'SMOOTH' : 'DISK_FEATURE',
        object_type: 'Galaxy',
        confidence: rec.confidence,
        anomaly_score: rec.triage_score,
        ood_score: rec.triage_score,
        priority: rec.priority,
        catalog_status: 'UNCHECKED',
        catalog_name: rec.filename,
        observation_time: rec.timestamp,
        image_url: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23070B11"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%238FAFC2" font-size="10" font-family="monospace">USER FILE</text></svg>',
        explanation: `User observation cutout ${rec.filename} analyzed in Research Mode.`,
        morphology_probs: [{ label: rec.morphology, probability: rec.confidence }],
        is_demo: false
      }));

    const curatedHighPriority = LIBRARY_OBSERVATIONS.filter(
      (o) => o.priority === 'HIGH' || o.priority === 'CRITICAL'
    );
    return [...userRunsHighPriority, ...curatedHighPriority];
  }, []);

  // Count priorities
  const counts = useMemo(() => {
    return {
      CRITICAL: queueObservations.filter((o) => o.priority === 'CRITICAL').length,
      HIGH: queueObservations.filter((o) => o.priority === 'HIGH').length,
      MEDIUM: queueObservations.filter((o) => o.priority === 'MEDIUM').length,
      LOW: queueObservations.filter((o) => o.priority === 'LOW').length,
    };
  }, [queueObservations]);

  const filteredObservations = useMemo(() => {
    return queueObservations
      .filter((obs) => {
        if (priorityFilter === 'ALL') return true;
        return obs.priority === priorityFilter;
      })
      .sort((a, b) => {
        if (sortBy === 'anomaly_score') return b.anomaly_score - a.anomaly_score;
        if (sortBy === 'confidence') return b.confidence - a.confidence;
        return new Date(b.observation_time).getTime() - new Date(a.observation_time).getTime();
      });
  }, [queueObservations, priorityFilter, sortBy]);

  const toggleExpand = (obsId: string) => {
    setExpandedObsId(expandedObsId === obsId ? null : obsId);
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto font-sans" data-tour="anomaly-queue-page">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold font-mono text-white tracking-wider flex items-center gap-2.5">
              <ShieldAlert className="w-6 h-6 text-rose-400" /> ANOMALY & PRIORITY QUEUE
            </h1>
            <span className="text-xs font-mono bg-rose-950/60 text-rose-400 border border-rose-800/60 px-2 py-0.5 rounded font-bold">
              TRIAGE CONSOLE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Astronomical observations prioritized for scientific review by ASTRA's experimental out-of-distribution triage heuristic.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 self-start md:self-auto">
          <Cpu className="w-4 h-4 text-[#8FAFC2]" />
          <span>STATISTICAL OOD DISTANCE METRIC</span>
        </div>
      </div>

      {/* Priority Summary Metric Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div
          onClick={() => setPriorityFilter(priorityFilter === 'CRITICAL' ? 'ALL' : 'CRITICAL')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'CRITICAL'
              ? 'border-purple-500 bg-purple-950/40'
              : 'border-slate-800 hover:border-purple-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-purple-400">CRITICAL PRIORITY</span>
            <AlertTriangle className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{counts.CRITICAL}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Top OOD Divergence Target</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'HIGH' ? 'ALL' : 'HIGH')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'HIGH'
              ? 'border-rose-500 bg-rose-950/40'
              : 'border-slate-800 hover:border-rose-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-rose-400">HIGH PRIORITY</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{counts.HIGH}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Scientific Review Required</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'MEDIUM' ? 'ALL' : 'MEDIUM')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'MEDIUM'
              ? 'border-amber-500 bg-amber-950/40'
              : 'border-slate-800 hover:border-amber-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-amber-400">MEDIUM PRIORITY</span>
            <Layers className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{counts.MEDIUM}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Secondary Review Queue</div>
        </div>

        <div
          onClick={() => setPriorityFilter(priorityFilter === 'LOW' ? 'ALL' : 'LOW')}
          className={`glass-panel p-4 rounded-xl border transition-all cursor-pointer ${
            priorityFilter === 'LOW'
              ? 'border-emerald-500 bg-emerald-950/40'
              : 'border-slate-800 hover:border-emerald-500/50 bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-emerald-400">LOW PRIORITY</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{counts.LOW}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">Standard Reference Baseline</div>
        </div>
      </div>

      {/* Filter and Sort Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/90 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400 ml-1" />
          <span className="text-xs font-mono text-slate-400">FILTER PRIORITY:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-all cursor-pointer ${
                priorityFilter === p
                  ? 'bg-rose-950 text-rose-300 border border-rose-500/50 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <ArrowUpDown className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-mono text-slate-400">SORT BY:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 font-mono text-xs text-slate-200 focus:outline-none focus:border-rose-500/50"
          >
            <option value="anomaly_score">Triage Anomaly Score (High → Low)</option>
            <option value="confidence">Model Confidence (High → Low)</option>
            <option value="time">Observation Time (Recent First)</option>
          </select>
        </div>
      </div>

      {/* Queue Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/50 flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            PRIORITIZED OBSERVATION QUEUE ({filteredObservations.length} OBJECTS)
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            CANONICAL HIGH/CRITICAL QUEUE
          </span>
        </div>

        {filteredObservations.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="NO OBSERVATIONS CURRENTLY PRIORITIZED"
            description="Run an astronomical observation cutout through Research Mode to execute live triage and populate the priority queue."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  <th className="p-3.5">TARGET ID</th>
                  <th className="p-3.5">RA / DEC</th>
                  <th className="p-3.5">MORPHOLOGY</th>
                  <th className="p-3.5 text-center">ANOMALY SCORE</th>
                  <th className="p-3.5">PRIORITY</th>
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
                    uncertainty_score: obs.triage_response?.uncertainty_score ?? (1.0 - obs.confidence) / 0.75,
                    oddity_score: obs.triage_response?.oddity_score ?? obs.p_odd ?? (obs.triage_response?.scientific_attributes?.prob_odd),
                    raw_embedding_distance: obs.triage_response?.raw_embedding_distance,
                    confidence: obs.confidence,
                    p_odd: obs.p_odd ?? obs.triage_response?.scientific_attributes?.prob_odd,
                    predicted_class: obs.gz2class,
                    nearest_reference_class: obs.triage_response?.nearest_reference_class || obs.broad_morphology,
                    model_version: obs.triage_response?.model_version
                  };

                  return (
                    <React.Fragment key={obs.id}>
                      <tr className={`transition-colors ${isExpanded ? 'bg-slate-900/90' : 'hover:bg-rose-950/20'}`}>
                        <td className="p-3.5 font-bold text-white flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${obs.priority === 'CRITICAL' ? 'bg-purple-400' : 'bg-rose-400'}`} />
                          {obs.id}
                        </td>
                        <td className="p-3.5 text-slate-300">
                          {obs.ra.toFixed(2)}°, {obs.dec.toFixed(2)}°
                        </td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded bg-[#0D1219] text-[#8FAFC2] border border-[#252D37]">
                            {obs.broad_morphology}
                          </span>
                        </td>
                        <td className="p-3.5 text-center font-bold">
                          <span className={obs.anomaly_score >= 0.7 ? 'text-purple-400 font-extrabold' : 'text-rose-400'}>
                            {obs.anomaly_score.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3.5">
                          <PriorityBadge priority={obs.priority as PriorityLevel} />
                        </td>
                        <td className="p-3.5 max-w-xs">
                          <button
                            onClick={() => toggleExpand(obs.id)}
                            className="text-[11px] text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1 cursor-pointer underline text-left"
                          >
                            <Sparkles className="w-3 h-3 text-amber-400 shrink-0" />
                            <span className="truncate">Why prioritized?</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        </td>
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
                        <td className="p-3.5 text-right space-x-2">
                          <button
                            onClick={() => toggleExpand(obs.id)}
                            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-[#8FAFC2] hover:text-white border border-slate-800 transition-all text-[11px] inline-flex items-center gap-1 cursor-pointer"
                          >
                            <HelpCircle className="w-3 h-3 text-amber-400" />
                            {isExpanded ? 'Hide Reason' : 'Why Flagged?'}
                          </button>

                          <button
                            onClick={() => onInspectObservation(obs)}
                            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-rose-950 text-rose-300 hover:text-white border border-slate-800 hover:border-rose-800/60 transition-all text-[11px] inline-flex items-center gap-1 cursor-pointer"
                          >
                            DOSSIER <ExternalLink className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>

                      {/* Expanded In-Line Explanation Row */}
                      {isExpanded && (
                        <tr>
                          <td colSpan={8} className="p-4 bg-[#05080E] border-b border-slate-800">
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
    </div>
  );
};
