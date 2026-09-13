import React from 'react';
import type { Observation } from '../types';
import { MOCK_TELEMETRY, MOCK_OBSERVATIONS } from '../data/mockData';
import { MetricCard } from '../components/MetricCard';
import { AnomalyCard } from '../components/AnomalyCard';
import { PriorityBadge } from '../components/PriorityBadge';
import { Telescope, Cpu, ShieldAlert, Zap, ArrowRight, ExternalLink } from 'lucide-react';

interface MissionOverviewPageProps {
  onInvestigate: (obs: Observation) => void;
  onViewLibrary: () => void;
}

export const MissionOverviewPage: React.FC<MissionOverviewPageProps> = ({ onInvestigate, onViewLibrary }) => {
  const topAnomaly = MOCK_OBSERVATIONS[0]; // OBS-004271

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header & Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold font-mono text-white tracking-wider">
              MISSION OVERVIEW
            </h1>
            <span className="text-xs font-mono bg-amber-950/40 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded">
              SIMULATED TELEMETRY
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Real-time satellite onboard observation triage and bandwidth priority queue.
          </p>
        </div>

        <button
          onClick={onViewLibrary}
          className="px-4 py-2.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 text-cyan-300 font-mono text-xs font-semibold border border-cyan-800/60 transition-all flex items-center gap-2 self-start cursor-pointer"
        >
          VIEW OBSERVATION LIBRARY <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="OBSERVATIONS RECEIVED"
          value={MOCK_TELEMETRY.observations_received}
          subtitle="Simulated satellite stream"
          icon={Telescope}
          accentColor="cyan"
          isDemo={true}
        />
        <MetricCard
          title="ONBOARD PROCESSED"
          value={MOCK_TELEMETRY.onboard_processed}
          subtitle="Triaged onboard"
          icon={Cpu}
          trend="95.5%"
          accentColor="emerald"
          isDemo={true}
        />
        <MetricCard
          title="ANOMALIES FLAGGED"
          value={MOCK_TELEMETRY.anomalies_flagged}
          subtitle="Out-of-distribution alerts"
          icon={ShieldAlert}
          trend="1.06%"
          accentColor="crimson"
          isDemo={true}
        />
        <MetricCard
          title="PRIORITY DOWNLINK"
          value={MOCK_TELEMETRY.priority_observations}
          subtitle="Bandwidth saved: 86%"
          icon={Zap}
          accentColor="amber"
          isDemo={true}
        />
      </div>

      {/* Featured Anomaly Alert Card */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-mono font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            TOP ANOMALY ALERT
          </h2>
          <span className="text-xs font-mono text-slate-400">HIGHEST DIVERGENCE TARGET</span>
        </div>
        <AnomalyCard observation={topAnomaly} onInvestigate={onInvestigate} />
      </div>

      {/* Priority Observations Table */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold font-mono text-white tracking-wider">
              PRIORITY OBSERVATIONS QUEUE
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Triaged astronomical targets ranked by anomaly score and scientific downlink priority.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded border border-slate-800">
            DEMO DATASET (6 OBJECTS)
          </span>
        </div>

        {/* Table Container */}
        <div className="glass-panel rounded-xl border border-slate-800 overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                <th className="p-3.5">TARGET ID</th>
                <th className="p-3.5">OBS TIME</th>
                <th className="p-3.5">RA / DEC</th>
                <th className="p-3.5">MORPHOLOGY</th>
                <th className="p-3.5 text-center">CONFIDENCE</th>
                <th className="p-3.5 text-center">ANOMALY SCORE</th>
                <th className="p-3.5">PRIORITY</th>
                <th className="p-3.5">CATALOG MATCH</th>
                <th className="p-3.5 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
              {MOCK_OBSERVATIONS.map((obs) => (
                <tr key={obs.id} className="hover:bg-cyan-950/20 transition-colors group">
                  <td className="p-3.5 font-bold text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    {obs.id}
                  </td>
                  <td className="p-3.5 text-slate-400">
                    {obs.observation_time.split('T')[1].replace('Z', '')} UTC
                  </td>
                  <td className="p-3.5 text-slate-300">
                    {obs.ra.toFixed(2)}°, {obs.dec.toFixed(2)}°
                  </td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-cyan-300 border border-slate-800">
                      {obs.broad_morphology}
                    </span>
                  </td>
                  <td className="p-3.5 text-center text-emerald-400 font-semibold">
                    {(obs.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="p-3.5 text-center font-bold">
                    <span className={obs.anomaly_score > 0.8 ? 'text-rose-400' : 'text-cyan-400'}>
                      {obs.anomaly_score.toFixed(2)}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <PriorityBadge priority={obs.priority} />
                  </td>
                  <td className="p-3.5 text-slate-400 max-w-[160px] truncate">
                    {obs.catalog_status === 'MATCHED' ? (
                      <span className="text-emerald-400 font-semibold">{obs.catalog_name}</span>
                    ) : obs.catalog_status === 'WEAK_MATCH' ? (
                      <span className="text-amber-400">{obs.catalog_name}</span>
                    ) : (
                      <span className="text-rose-400">No strong match</span>
                    )}
                  </td>
                  <td className="p-3.5 text-right">
                    <button
                      onClick={() => onInvestigate(obs)}
                      className="px-2.5 py-1 rounded bg-slate-900 hover:bg-cyan-950 text-cyan-300 hover:text-white border border-slate-800 hover:border-cyan-800/60 transition-all text-[11px] inline-flex items-center gap-1 cursor-pointer"
                    >
                      DETAILS <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
