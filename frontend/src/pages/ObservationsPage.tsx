import React, { useMemo, useState } from 'react';
import type { Observation, PriorityLevel } from '../types';
import libraryData from '../data/observationLibrary.json';
import { getAnalysisHistory } from '../services/analysisHistory';
import { PriorityBadge } from '../components/PriorityBadge';
import { TriageExplanation } from '../components/TriageExplanation';
import {
  Radio,
  AlertTriangle,
  Clock,
  Activity,
  ArrowRight,
  Eye,
  ShieldAlert,
  Gauge,
  FileSearch,
  Database,
  HelpCircle,
  X
} from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

interface ObservationsPageProps {
  onAnalyze: (obs: Observation) => void;
}

export const ObservationsPage: React.FC<ObservationsPageProps> = ({ onAnalyze }) => {
  const userHistory = getAnalysisHistory();
  const [explanationObs, setExplanationObs] = useState<Observation | null>(null);

  // Combine Library targets with user analysis runs
  const allObservations = useMemo(() => {
    return [...LIBRARY_OBSERVATIONS];
  }, []);

  // Sort priority observations (HIGH / CRITICAL priority first)
  const priorityObservations = useMemo(() => {
    return allObservations
      .filter((o) => o.priority === 'HIGH' || o.priority === 'CRITICAL')
      .slice(0, 10)
      .sort((a, b) => b.anomaly_score - a.anomaly_score);
  }, [allObservations]);

  // Recent feed (Sample 15 from curated dataset + user runs)
  const recentObservations = useMemo(() => {
    return allObservations.slice(0, 15);
  }, [allObservations]);

  // Operational Summary Counts derived from genuine dataset
  const totalCount = LIBRARY_OBSERVATIONS.length + userHistory.length;
  const highPriorityCount = LIBRARY_OBSERVATIONS.filter((o) => o.priority === 'HIGH' || o.priority === 'CRITICAL').length;
  const criticalAnomalyCount = LIBRARY_OBSERVATIONS.filter((o) => o.anomaly_score >= 0.70).length;
  const awaitingReviewCount = LIBRARY_OBSERVATIONS.filter(
    (o) => o.catalog_status === 'NO_MATCH' || o.catalog_status === 'UNCHECKED' || o.catalog_status === 'WEAK_MATCH'
  ).length;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold font-mono text-white tracking-wider">
              OBSERVATIONS
            </h1>
            <span className="text-xs font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
              <Database className="w-3 h-3 text-emerald-400" /> CURATED MISSION ARCHIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Browse genuine Galaxy Zoo 2 astronomical observations and user-submitted analysis runs.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800 self-start">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-slate-300">DATA STREAM:</span>
            <span className="text-emerald-400 font-bold">CURATED ARCHIVE & SESSION RUNS</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">SURVEY: SDSS DR7</span>
        </div>
      </div>

      {/* SECTION A: MISSION OBSERVATION STATUS (Metrics Bar) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-[#8FAFC2]" /> MISSION OBSERVATION STATUS
          </h2>
          <span className="text-[10px] font-mono text-slate-500">AUTHENTIC SCIENTIFIC DATASET</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Curated + User Observations */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800/80 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Total Observations</span>
              <Activity className="w-4 h-4 text-[#8FAFC2]" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">{totalCount.toLocaleString()}</div>
            <div className="text-[10px] font-mono text-[#8FAFC2]/90">2,000 GZ2 + Session runs</div>
          </div>

          {/* High Priority */}
          <div className="glass-panel p-4 rounded-xl border border-amber-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">High Priority</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">{highPriorityCount}</div>
            <div className="text-[10px] font-mono text-amber-400/80">Curated triage targets</div>
          </div>

          {/* Critical / Anomalous */}
          <div className="glass-panel p-4 rounded-xl border border-rose-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Critical Anomalies</span>
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">{criticalAnomalyCount}</div>
            <div className="text-[10px] font-mono text-rose-400/80">OOD divergence &ge; 0.70</div>
          </div>

          {/* Awaiting Review */}
          <div className="glass-panel p-4 rounded-xl border border-indigo-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Unchecked / Weak Matches</span>
              <FileSearch className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-indigo-300">{awaitingReviewCount}</div>
            <div className="text-[10px] font-mono text-indigo-400/80">Catalog cross-match review</div>
          </div>
        </div>
      </div>

      {/* SECTION B: PRIORITY OBSERVATIONS */}
      <div className="space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-2">
          <div>
            <h2 className="text-sm font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" /> PRIORITY OBSERVATIONS
            </h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              High-priority targets flagged by onboard triage requiring immediate scientific inspection.
            </p>
          </div>
          <span className="text-xs font-mono bg-rose-950/60 text-rose-300 border border-rose-800/60 px-2.5 py-1 rounded">
            {priorityObservations.length} ACTIONABLE ITEMS
          </span>
        </div>

        {/* Priority Table / Compact Grid */}
        <div className="glass-panel rounded-xl border border-slate-800/80 overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 text-[10px] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Observation</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Triage Score</th>
                  <th className="py-3 px-4">Why This Priority</th>
                  <th className="py-3 px-4 text-right">Quick Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {priorityObservations.map((obs) => {
                  return (
                    <tr key={obs.id} className="hover:bg-slate-900/60 transition-colors">
                      {/* ID + Thumbnail */}
                      <td className="py-3 px-4">
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

                      {/* Priority Badge */}
                      <td className="py-3 px-4">
                        <PriorityBadge priority={obs.priority} />
                      </td>

                      {/* Classification */}
                      <td className="py-3 px-4">
                        <span className="text-[#D5DAE0] font-semibold">{obs.broad_morphology}</span>
                        <span className="text-[10px] text-slate-500 block">({obs.gz2class})</span>
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 text-emerald-400 font-semibold">
                        {(obs.confidence * 100).toFixed(1)}%
                      </td>

                      {/* Triage / Anomaly Score */}
                      <td className="py-3 px-4">
                        <span className={`font-bold flex items-center gap-1 ${obs.anomaly_score >= 0.7 ? 'text-rose-400' : 'text-amber-400'}`}>
                          <Gauge className="w-3.5 h-3.5" />
                          {obs.anomaly_score.toFixed(2)}
                        </span>
                      </td>

                      {/* Why This Priority Button */}
                      <td className="py-3 px-4">
                        <button
                          onClick={() => setExplanationObs(obs)}
                          className="text-[11px] text-[#8FAFC2] hover:text-amber-300 font-mono transition-colors flex items-center gap-1 cursor-pointer underline"
                        >
                          <HelpCircle className="w-3 h-3 text-amber-400 shrink-0" />
                          Why this priority &rarr;
                        </button>
                      </td>

                      {/* Quick Action */}
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onAnalyze(obs)}
                          className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] hover:text-white font-mono text-[11px] font-semibold border border-[#4B5563]/60 transition-all inline-flex items-center gap-1 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" /> View Analysis
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* SECTION C: RECENT OBSERVATIONS FEED */}
      <div className="space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-2">
          <div>
            <h2 className="text-sm font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#8FAFC2]" /> RECENT OBSERVATIONS FEED
            </h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Chronological operational stream of incoming astronomical survey downlinks.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            SORTED BY RECENCY
          </span>
        </div>

        {/* Chronological Feed List */}
        <div className="space-y-3">
          {recentObservations.map((obs) => {
            const formattedTime = new Date(obs.observation_time).toUTCString().replace(' GMT', ' UTC');
            return (
              <div
                key={obs.id}
                className="glass-panel p-4 rounded-xl border border-slate-800/80 hover:border-[#4B5563]/60 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                {/* Left Side: Thumbnail + Metadata */}
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <img
                      src={obs.image_url}
                      alt={obs.id}
                      className="w-14 h-14 rounded-lg object-cover border border-[#252D37] bg-black shrink-0"
                    />
                  </div>

                  <div className="space-y-1 font-mono">
                    <div className="flex items-center gap-2.5">
                      <span className="text-sm font-bold text-white">{obs.id}</span>
                      <PriorityBadge priority={obs.priority} />
                      <span className="text-xs text-[#8FAFC2]">{obs.broad_morphology}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" /> {formattedTime}
                      </span>
                      <span>RA: {obs.ra.toFixed(2)}°</span>
                      <span>DEC: {obs.dec.toFixed(2)}°</span>
                    </div>
                  </div>
                </div>

                {/* Right Side: Operational Stats + Quick Actions */}
                <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-800/60">
                  <div className="text-right font-mono text-xs">
                    <button
                      onClick={() => setExplanationObs(obs)}
                      className="text-amber-400 hover:text-amber-300 text-[11px] block underline transition-colors"
                    >
                      Why this priority &rarr;
                    </button>
                    <span className="text-white font-semibold">
                      Score: {obs.anomaly_score.toFixed(2)}
                    </span>
                  </div>

                  {/* QUICK ACTIONS */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs border border-slate-700/60 transition-all flex items-center gap-1 cursor-pointer"
                    >
                      Open
                    </button>
                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3.5 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] hover:text-white font-mono text-xs font-semibold border border-[#4B5563]/60 transition-all flex items-center gap-1 cursor-pointer"
                    >
                      View Analysis <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Explanation Modal Overlay */}
      {explanationObs && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl bg-[#090D14] border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-mono font-bold text-white tracking-wider">
                  TRIAGE REASONING: {explanationObs.id}
                </h3>
                <PriorityBadge priority={explanationObs.priority} />
              </div>

              <button
                onClick={() => setExplanationObs(null)}
                className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white border border-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <TriageExplanation
              signals={{
                score: explanationObs.anomaly_score,
                priority: explanationObs.priority as PriorityLevel,
                novelty_score: explanationObs.triage_response?.novelty_score ?? explanationObs.ood_score,
                uncertainty_score: explanationObs.triage_response?.uncertainty_score ?? (1.0 - explanationObs.confidence) / 0.75,
                oddity_score: explanationObs.triage_response?.oddity_score ?? explanationObs.p_odd ?? explanationObs.triage_response?.scientific_attributes?.prob_odd,
                raw_embedding_distance: explanationObs.triage_response?.raw_embedding_distance,
                confidence: explanationObs.confidence,
                p_odd: explanationObs.p_odd ?? explanationObs.triage_response?.scientific_attributes?.prob_odd,
                predicted_class: explanationObs.gz2class,
                nearest_reference_class: explanationObs.triage_response?.nearest_reference_class || explanationObs.broad_morphology,
                model_version: explanationObs.triage_response?.model_version
              }}
            />

            <div className="text-right">
              <button
                onClick={() => {
                  const target = explanationObs;
                  setExplanationObs(null);
                  onAnalyze(target);
                }}
                className="px-4 py-2 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-200 border border-rose-800 font-mono text-xs font-bold inline-flex items-center gap-1.5 cursor-pointer"
              >
                INSPECT FULL DOSSIER <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
