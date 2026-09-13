import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  onReset?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Observations Found',
  description = 'No astronomical data matched your search or filter criteria.',
  onReset
}) => {
  return (
    <div className="glass-panel p-10 rounded-xl border border-slate-800 text-center space-y-4 max-w-md mx-auto my-8">
      <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 text-slate-400 flex items-center justify-center mx-auto">
        <SearchX className="w-6 h-6 text-slate-400" />
      </div>
      <div className="space-y-1 font-mono">
        <h3 className="text-base font-bold text-slate-200">{title}</h3>
        <p className="text-xs text-slate-400 font-sans">{description}</p>
      </div>
      {onReset && (
        <button
          onClick={onReset}
          className="px-4 py-2 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 font-mono text-xs border border-cyan-800/60 transition-all inline-flex items-center gap-1.5 cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          RESET FILTERS
        </button>
      )}
    </div>
  );
};
