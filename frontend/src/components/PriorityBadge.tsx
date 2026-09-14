import React from 'react';
import type { PriorityLevel } from '../types';

interface PriorityBadgeProps {
  priority: PriorityLevel;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority }) => {
  const getBadgeStyle = () => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-purple-950/80 text-purple-300 border-purple-500/50 glow-crimson animate-pulse';
      case 'HIGH':
        return 'bg-rose-950/70 text-rose-400 border-rose-500/40 glow-crimson';
      case 'MEDIUM':
        return 'bg-amber-950/70 text-amber-400 border-amber-500/40';
      case 'LOW':
      default:
        return 'bg-[#151B23] text-[#D5DAE0] border-[#4B5563]/50';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-mono font-semibold border ${getBadgeStyle()}`}>
      {(priority === 'CRITICAL' || priority === 'HIGH') && (
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5 animate-pulse" />
      )}
      {priority} PRIORITY
    </span>
  );
};
