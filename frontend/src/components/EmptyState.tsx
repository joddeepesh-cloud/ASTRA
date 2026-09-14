import React from 'react';
import { SearchX, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  onReset?: () => void;
  icon?: React.ComponentType<{ className?: string }>;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Observations Found',
  description = 'No astronomical data matched your search or filter criteria.',
  onReset,
  icon: CustomIcon
}) => {
  const IconToRender = CustomIcon || SearchX;
  return (
    <div className="glass-panel p-10 rounded-xl border border-[#252D37] text-center space-y-4 max-w-md mx-auto my-8 font-sans-ui selection:bg-[#C7CDD5]/30">
      <div className="w-12 h-12 rounded-full bg-[#151B23] border border-[#252D37] text-[#A8B0BA] flex items-center justify-center mx-auto">
        <IconToRender className="w-6 h-6 text-[#A8B0BA]" />
      </div>
      <div className="space-y-1 font-mono-tech">
        <h3 className="text-base font-bold text-[#F2F4F7]">{title}</h3>
        <p className="text-xs text-[#A8B0BA] font-sans-ui">{description}</p>
      </div>
      {onReset && (
        <button
          onClick={onReset}
          className="px-4 py-2 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] font-mono-tech text-xs border border-[#C7CDD5]/30 transition-all inline-flex items-center gap-1.5 cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          RESET FILTERS
        </button>
      )}
    </div>
  );
};
