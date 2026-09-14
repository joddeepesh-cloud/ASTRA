import React from 'react';

interface ConfidenceBarProps {
  label: string;
  value: number; // 0.0 - 1.0
  color?: 'silver' | 'cyan' | 'amber' | 'emerald' | 'crimson';
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  label,
  value,
  color = 'silver'
}) => {
  const percentage = Math.round(value * 100);

  const getColorClasses = () => {
    switch (color) {
      case 'amber':
        return 'bg-[#D6A84F] shadow-[0_0_10px_rgba(214,168,79,0.3)]';
      case 'emerald':
        return 'bg-[#5FC7A1] shadow-[0_0_10px_rgba(95,199,161,0.3)]';
      case 'crimson':
        return 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.3)]';
      case 'cyan':
        return 'bg-[#8FAFC2] shadow-[0_0_10px_rgba(143,175,194,0.3)]';
      case 'silver':
      default:
        return 'bg-[#D5DAE0] shadow-[0_0_10px_rgba(213,218,224,0.3)]';
    }
  };

  return (
    <div className="w-full space-y-1.5 font-mono-tech">
      <div className="flex justify-between text-xs font-mono-tech">
        <span className="text-[#A8B0BA]">{label}</span>
        <span className="text-[#D5DAE0] font-semibold">{percentage}%</span>
      </div>
      <div className="h-2 w-full bg-[#030508] rounded-full overflow-hidden border border-[#252D37] p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${getColorClasses()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
