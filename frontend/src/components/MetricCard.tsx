import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  isDemo?: boolean;
  accentColor?: 'silver' | 'amber' | 'crimson' | 'emerald';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  isDemo = true,
  accentColor = 'silver'
}) => {
  const getIconBg = () => {
    switch (accentColor) {
      case 'amber':
        return 'bg-[#3A2B15] text-[#D6A84F] border-[#D6A84F]/30';
      case 'crimson':
        return 'bg-[#3A1D1D] text-rose-400 border-rose-500/30';
      case 'emerald':
        return 'bg-[#0E241B] text-[#5FC7A1] border-[#5FC7A1]/30';
      case 'silver':
      default:
        return 'bg-[#151B23] text-[#D5DAE0] border-[#C7CDD5]/30';
    }
  };

  return (
    <div className="glass-panel glass-panel-hover p-5 rounded-xl border border-[#252D37] relative overflow-hidden group font-sans-ui">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono-tech font-medium text-[#717985] uppercase tracking-wider">{title}</span>
            {isDemo && (
              <span className="text-[10px] font-mono-tech text-[#D6A84F] bg-[#3A2B15]/60 px-1.5 py-0.5 rounded border border-[#D6A84F]/30">
                DEMO
              </span>
            )}
          </div>
          <div className="mt-2 text-2xl md:text-3xl font-bold font-mono-tech text-[#F2F4F7] tracking-tight">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
        </div>
        <div className={`p-2.5 rounded-lg border ${getIconBg()}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs text-[#A8B0BA] font-mono-tech pt-3 border-t border-[#252D37]">
          <span>{subtitle}</span>
          {trend && <span className="text-[#D5DAE0] font-semibold">{trend}</span>}
        </div>
      )}
    </div>
  );
};
