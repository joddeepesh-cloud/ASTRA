import React from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from './PriorityBadge';
import { ShieldAlert, ArrowRight, Database, Gauge, Sparkles } from 'lucide-react';

interface AnomalyCardProps {
  observation: Observation;
  onInvestigate: (obs: Observation) => void;
}

export const AnomalyCard: React.FC<AnomalyCardProps> = ({ observation, onInvestigate }) => {
  return (
    <div className="glass-panel p-6 rounded-xl border border-rose-500/30 bg-slate-950/80 relative overflow-hidden shadow-2xl">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-4 border-b border-rose-500/20">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-400 animate-pulse" />
          <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-widest">
            HIGH ANOMALY ALERT
          </span>
          <span className="text-[10px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30 px-1.5 py-0.5 rounded">
            DEMO
          </span>
        </div>
        <PriorityBadge priority={observation.priority} />
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-5 items-center">
        {/* Thumbnail Preview */}
        <div className="relative group rounded-lg overflow-hidden border border-cyan-500/30 bg-black aspect-square max-h-48">
          <img
            src={observation.image_url}
            alt={observation.id}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 opacity-90 group-hover:opacity-100"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent" />
          <div className="absolute bottom-2 left-2 right-2 text-xs font-mono text-cyan-300 bg-slate-900/80 px-2 py-1 rounded border border-cyan-900/40 flex justify-between">
            <span>RA: {observation.ra.toFixed(2)}°</span>
            <span>DEC: {observation.dec.toFixed(2)}°</span>
          </div>
        </div>

        {/* Observation Details */}
        <div className="md:col-span-2 space-y-4">
          <div className="flex justify-between items-baseline">
            <div>
              <span className="text-xs font-mono text-slate-400">TARGET ID</span>
              <h3 className="text-2xl font-bold font-mono text-white tracking-tight flex items-center gap-2">
                {observation.id}
                <span className="text-xs font-normal font-sans text-slate-400">({observation.dr7objid})</span>
              </h3>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono text-slate-400">ANOMALY SCORE</span>
              <div className="text-2xl font-mono font-bold text-rose-400 flex items-center justify-end gap-1">
                <Gauge className="w-5 h-5 text-rose-400" />
                {observation.anomaly_score.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div>
              <span className="text-slate-500 block">CLASSIFICATION</span>
              <span className="text-cyan-300 font-semibold">{observation.broad_morphology}</span>
            </div>
            <div>
              <span className="text-slate-500 block">CONFIDENCE</span>
              <span className="text-emerald-400 font-semibold">{(observation.confidence * 100).toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-slate-500 block">CATALOG MATCH</span>
              <span className="text-amber-400 font-semibold truncate block">
                {observation.catalog_status === 'NO_MATCH' ? 'No strong match' : 'Weak match'}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
            <Sparkles className="w-3.5 h-3.5 inline text-amber-400 mr-1" />
            {observation.explanation}
          </p>

          <div className="pt-2 flex justify-between items-center">
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-slate-400" />
              Dataset: GZ2 Sample ({observation.split?.toUpperCase()})
            </span>
            <button
              onClick={() => onInvestigate(observation)}
              className="px-5 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold tracking-wider transition-all flex items-center gap-2 shadow-lg shadow-rose-950/50 hover:shadow-rose-600/30 cursor-pointer"
            >
              INVESTIGATE <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
