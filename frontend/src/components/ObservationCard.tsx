import React from 'react';
import type { Observation } from '../types';
import { PriorityBadge } from './PriorityBadge';
import { ArrowRight, Eye, Gauge } from 'lucide-react';

interface ObservationCardProps {
  observation: Observation;
  onAnalyze: (obs: Observation) => void;
}

export const ObservationCard: React.FC<ObservationCardProps> = ({ observation, onAnalyze }) => {
  return (
    <div className="glass-panel glass-panel-hover rounded-xl border border-[#252D37] overflow-hidden flex flex-col justify-between group font-sans-ui selection:bg-[#C7CDD5]/30">
      {/* Top Image Preview */}
      <div className="relative aspect-video bg-[#030508] overflow-hidden">
        <img
          src={observation.image_url}
          alt={observation.id}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-85 group-hover:opacity-100"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#030508] via-transparent to-transparent opacity-80" />
        
        <div className="absolute top-3 left-3">
          <PriorityBadge priority={observation.priority} />
        </div>
        
        <div className="absolute top-3 right-3 text-[10px] font-mono-tech bg-[#030508]/90 text-[#D5DAE0] px-2 py-0.5 rounded border border-[#252D37] backdrop-blur-sm">
          {observation.broad_morphology}
        </div>

        <div className="absolute bottom-2 left-3 text-xs font-mono-tech text-[#F2F4F7] font-bold tracking-tight">
          {observation.id}
        </div>
      </div>

      {/* Details Body */}
      <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs font-mono-tech text-[#717985]">
            <span>RA: {observation.ra.toFixed(2)}°</span>
            <span>DEC: {observation.dec.toFixed(2)}°</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono-tech bg-[#0D1219]/70 p-2.5 rounded border border-[#252D37]">
            <div>
              <span className="text-[#717985] block text-[10px]">CONFIDENCE</span>
              <span className="text-[#5FC7A1] font-semibold">{(observation.confidence * 100).toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-[#717985] block text-[10px]">ANOMALY SCORE</span>
              <span className={`font-semibold flex items-center gap-1 ${observation.anomaly_score > 0.8 ? 'text-[#D6A84F]' : 'text-[#D5DAE0]'}`}>
                <Gauge className="w-3 h-3" />
                {observation.anomaly_score.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-[#252D37] flex items-center justify-between font-mono-tech">
          <span className="text-[10px] text-[#717985] truncate max-w-[140px]">
            {observation.catalog_name || 'No catalog entry'}
          </span>
          <button
            onClick={() => onAnalyze(observation)}
            className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] hover:text-white font-mono-tech text-xs font-semibold border border-[#C7CDD5]/30 transition-all flex items-center gap-1 cursor-pointer"
          >
            <Eye className="w-3.5 h-3.5" />
            ANALYZE <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};
