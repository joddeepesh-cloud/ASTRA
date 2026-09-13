import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  isDemo?: boolean;
  accentColor?: 'cyan' | 'amber' | 'crimson' | 'emerald';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  isDemo = true,
  accentColor = 'cyan'
}) => {
  const getIconBg = () => {
    switch (accentColor) {
      case 'amber':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'crimson':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'emerald':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'cyan':
      default:
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
    }
  };

  return (
    <div className="glass-panel glass-panel-hover p-5 rounded-xl border relative overflow-hidden group">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider">{title}</span>
            {isDemo && (
              <span className="text-[10px] font-mono text-amber-400/80 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-500/20">
                DEMO
              </span>
            )}
          </div>
          <div className="mt-2 text-2xl md:text-3xl font-bold font-mono text-slate-100 tracking-tight">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
        </div>
        <div className={`p-2.5 rounded-lg border ${getIconBg()}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs text-slate-400 font-mono pt-3 border-t border-slate-800/80">
          <span>{subtitle}</span>
          {trend && <span className="text-cyan-400 font-semibold">{trend}</span>}
        </div>
      )}
    </div>
  );
};
