import React from 'react';

interface StatusBadgeProps {
  status?: string;
  isDemo?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status = 'SYSTEM NOMINAL', isDemo = true }) => {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono tracking-wider shadow-sm">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <span>{status}</span>
      {isDemo && (
        <span className="ml-1 px-1.5 py-0.2 text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded font-sans uppercase">
          Demo Stream
        </span>
      )}
    </div>
  );
};
