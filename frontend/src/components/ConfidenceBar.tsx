import React from 'react';

interface ConfidenceBarProps {
  label: string;
  value: number; // 0.0 - 1.0
  color?: 'cyan' | 'amber' | 'emerald' | 'crimson';
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  label,
  value,
  color = 'cyan'
}) => {
  const percentage = Math.round(value * 100);

  const getColorClasses = () => {
    switch (color) {
      case 'amber':
        return 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]';
      case 'emerald':
        return 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]';
      case 'crimson':
        return 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]';
      case 'cyan':
      default:
        return 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]';
    }
  };

  return (
    <div className="w-full space-y-1.5">
      <div className="flex justify-between text-xs font-mono">
        <span className="text-slate-300">{label}</span>
        <span className="text-cyan-400 font-semibold">{percentage}%</span>
      </div>
      <div className="h-2 w-full bg-slate-900/90 rounded-full overflow-hidden border border-slate-800 p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${getColorClasses()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
