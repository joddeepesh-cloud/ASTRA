import React, { useMemo } from 'react';
import type { Observation } from '../types';
import { MOCK_OBSERVATIONS, MOCK_TELEMETRY } from '../data/mockData';
import { PriorityBadge } from '../components/PriorityBadge';
import {
  Radio,
  AlertTriangle,
  Clock,
  Activity,
  ArrowRight,
  Eye,
  ShieldAlert,
  Gauge,
  FileSearch
} from 'lucide-react';

interface ObservationsPageProps {
  onAnalyze: (obs: Observation) => void;
}

export const ObservationsPage: React.FC<ObservationsPageProps> = ({ onAnalyze }) => {
  // Sort priority observations (HIGH priority first, then high anomaly score)
  const priorityObservations = useMemo(() => {
    return [...MOCK_OBSERVATIONS]
      .filter((o) => o.priority === 'HIGH' || o.anomaly_score >= 0.8)
      .sort((a, b) => b.anomaly_score - a.anomaly_score);
  }, []);

  // Sort recent feed chronologically (Newest first)
  const recentObservations = useMemo(() => {
    return [...MOCK_OBSERVATIONS].sort(
      (a, b) => new Date(b.observation_time).getTime() - new Date(a.observation_time).getTime()
    );
  }, []);

  // Operational Summary Counts
  const totalCount = MOCK_TELEMETRY.observations_received || MOCK_OBSERVATIONS.length;
  const highPriorityCount = MOCK_OBSERVATIONS.filter((o) => o.priority === 'HIGH').length;
  const criticalAnomalyCount = MOCK_OBSERVATIONS.filter((o) => o.anomaly_score >= 0.8).length;
  const awaitingReviewCount = MOCK_OBSERVATIONS.filter(
    (o) => o.catalog_status === 'NO_MATCH' || o.catalog_status === 'UNCHECKED'
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
              <Activity className="w-3 h-3 animate-pulse text-emerald-400" /> MISSION CONTROL FEED
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Monitor recent astronomical observations and mission priorities.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800 self-start">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-slate-300">TELEMETRY STREAM:</span>
            <span className="text-emerald-400 font-bold">ACTIVE</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">LATENCY: 12ms</span>
        </div>
      </div>

      {/* SECTION A: MISSION OBSERVATION STATUS (Metrics Bar) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-cyan-400" /> MISSION OBSERVATION STATUS
          </h2>
          <span className="text-[10px] font-mono text-slate-500">SIMULATED DEMO TELEMETRY</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Recent Observations */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800/80 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Recent Observations</span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">{totalCount.toLocaleString()}</div>
            <div className="text-[10px] font-mono text-cyan-400/90">Downlink active stream</div>
          </div>

          {/* High Priority */}
          <div className="glass-panel p-4 rounded-xl border border-amber-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">High Priority</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">{highPriorityCount}</div>
            <div className="text-[10px] font-mono text-amber-400/80">Immediate review queue</div>
          </div>

          {/* Critical / Anomalous */}
          <div className="glass-panel p-4 rounded-xl border border-rose-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Critical Anomalies</span>
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">{criticalAnomalyCount}</div>
            <div className="text-[10px] font-mono text-rose-400/80">OOD divergence &ge; 0.80</div>
          </div>

          {/* Awaiting Review */}
          <div className="glass-panel p-4 rounded-xl border border-indigo-900/40 space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[11px] font-mono uppercase tracking-wider">Awaiting Review</span>
              <FileSearch className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-indigo-300">{awaitingReviewCount}</div>
            <div className="text-[10px] font-mono text-indigo-400/80">Catalog cross-match pending</div>
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
                  <th className="py-3 px-4">Catalog Status</th>
                  <th className="py-3 px-4 text-right">Quick Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {priorityObservations.map((obs) => (
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
                      <span className="text-cyan-300 font-semibold">{obs.broad_morphology}</span>
                      <span className="text-[10px] text-slate-500 block">({obs.gz2class})</span>
                    </td>

                    {/* Confidence */}
                    <td className="py-3 px-4 text-emerald-400 font-semibold">
                      {(obs.confidence * 100).toFixed(1)}%
                    </td>

                    {/* Triage / Anomaly Score */}
                    <td className="py-3 px-4">
                      <span className={`font-bold flex items-center gap-1 ${obs.anomaly_score >= 0.8 ? 'text-rose-400' : 'text-amber-400'}`}>
                        <Gauge className="w-3.5 h-3.5" />
                        {obs.anomaly_score.toFixed(2)}
                      </span>
                    </td>

                    {/* Catalog Status */}
                    <td className="py-3 px-4">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded border ${
                          obs.catalog_status === 'NO_MATCH'
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                            : obs.catalog_status === 'WEAK_MATCH'
                            ? 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                            : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                        }`}
                      >
                        {obs.catalog_status}
                      </span>
                    </td>

                    {/* Quick Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onAnalyze(obs)}
                        className="px-3 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 hover:text-white font-mono text-[11px] font-semibold border border-cyan-800/60 transition-all inline-flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Analysis
                      </button>
                    </td>
                  </tr>
                ))}
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
              <Clock className="w-4 h-4 text-cyan-400" /> RECENT OBSERVATIONS FEED
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
                className="glass-panel p-4 rounded-xl border border-slate-800/80 hover:border-cyan-900/60 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                {/* Left Side: Thumbnail + Metadata */}
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <img
                      src={obs.image_url}
                      alt={obs.id}
                      className="w-14 h-14 rounded-lg object-cover border border-cyan-900/40 bg-black shrink-0"
                    />
                    <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
                    </span>
                  </div>

                  <div className="space-y-1 font-mono">
                    <div className="flex items-center gap-2.5">
                      <span className="text-sm font-bold text-white">{obs.id}</span>
                      <PriorityBadge priority={obs.priority} />
                      <span className="text-xs text-cyan-400">{obs.broad_morphology}</span>
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
                    <span className="text-slate-500 block text-[10px]">ANOMALY / CONF</span>
                    <span className="text-white font-semibold">
                      {obs.anomaly_score.toFixed(2)} / {(obs.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* SECTION D: QUICK ACTIONS */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs border border-slate-700/60 transition-all flex items-center gap-1 cursor-pointer"
                    >
                      Open
                    </button>
                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3.5 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 hover:text-white font-mono text-xs font-semibold border border-cyan-800/60 transition-all flex items-center gap-1 cursor-pointer"
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
    </div>
  );
};
