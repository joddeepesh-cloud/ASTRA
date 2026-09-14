import React from 'react';
import { Telescope, Cpu, ShieldAlert, Zap, Database, UserCheck } from 'lucide-react';

export const ScientificPipeline: React.FC = () => {
  const steps = [
    {
      num: "01",
      title: "OBSERVATION",
      desc: "Raw photometric stream captured by spaceborne optical/infrared sensors.",
      icon: Telescope,
      color: "text-[#D5DAE0] border-[#C7CDD5]/30 bg-[#151B23]"
    },
    {
      num: "02",
      title: "ONBOARD TRIAGE",
      desc: "Lightweight neural feature extractor runs on satellite hardware.",
      icon: Cpu,
      color: "text-[#8FAFC2] border-[#8FAFC2]/30 bg-[#15232E]"
    },
    {
      num: "03",
      title: "ANOMALY / OOD ANALYSIS",
      desc: "Statistical out-of-distribution detection flags unexpected morphologies.",
      icon: ShieldAlert,
      color: "text-rose-400 border-rose-500/30 bg-[#3A1D1D]"
    },
    {
      num: "04",
      title: "PRIORITY SCORING",
      desc: "Bandwidth priority queue scores targets for immediate downlink.",
      icon: Zap,
      color: "text-[#D6A84F] border-[#D6A84F]/30 bg-[#3A2B15]"
    },
    {
      num: "05",
      title: "CATALOG CROSS-MATCH",
      desc: "Automated alignment with SDSS DR16, Simbad, and NASA archives.",
      icon: Database,
      color: "text-[#8FAFC2] border-[#8FAFC2]/30 bg-[#15232E]"
    },
    {
      num: "06",
      title: "SCIENTIFIC REVIEW",
      desc: "High-priority targets presented to domain experts & AI Copilot.",
      icon: UserCheck,
      color: "text-[#5FC7A1] border-[#5FC7A1]/30 bg-[#0E241B]"
    }
  ];

  return (
    <div className="space-y-6 font-sans-ui selection:bg-[#C7CDD5]/30">
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold font-serif-display text-[#F2F4F7] tracking-tight uppercase">
          HOW ASTRA WORKS
        </h2>
        <p className="text-sm text-[#A8B0BA] font-sans-ui">
          End-to-end autonomous satellite triage pipeline optimizing downlink bandwidth and scientific yield.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={step.num}
              className="glass-panel glass-panel-hover p-5 rounded-xl border border-[#252D37] relative overflow-hidden flex flex-col justify-between group"
            >
              <div className="flex items-start justify-between">
                <span className="text-2xl font-mono-tech font-bold text-[#717985] group-hover:text-[#D5DAE0] transition-colors">
                  {step.num}
                </span>
                <div className={`p-3 rounded-lg border ${step.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>

              <div className="mt-4 space-y-1.5 font-mono-tech">
                <h3 className="text-sm font-bold text-[#F2F4F7] tracking-wider">
                  {step.title}
                </h3>
                <p className="text-xs text-[#A8B0BA] leading-relaxed font-sans-ui">
                  {step.desc}
                </p>
              </div>

              {/* Progress Indicator */}
              <div className="mt-4 pt-2 border-t border-[#252D37] flex items-center justify-between text-[10px] font-mono-tech text-[#717985]">
                <span>STAGE {idx + 1} OF 6</span>
                <span className="text-[#8FAFC2]">LATENCY OPTIMIZED</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
