import React from 'react';
import { Telescope, Cpu, ShieldAlert, Zap, Database, UserCheck } from 'lucide-react';

export const ScientificPipeline: React.FC = () => {
  const steps = [
    {
      num: "01",
      title: "OBSERVATION",
      desc: "Raw photometric stream captured by spaceborne optical/infrared sensors.",
      icon: Telescope,
      color: "text-cyan-400 border-cyan-500/30 bg-cyan-950/40"
    },
    {
      num: "02",
      title: "ONBOARD TRIAGE",
      desc: "Lightweight neural feature extractor runs on satellite hardware.",
      icon: Cpu,
      color: "text-indigo-400 border-indigo-500/30 bg-indigo-950/40"
    },
    {
      num: "03",
      title: "ANOMALY / OOD ANALYSIS",
      desc: "Statistical out-of-distribution detection flags unexpected morphologies.",
      icon: ShieldAlert,
      color: "text-rose-400 border-rose-500/30 bg-rose-950/40"
    },
    {
      num: "04",
      title: "PRIORITY SCORING",
      desc: "Bandwidth priority queue scores targets for immediate downlink.",
      icon: Zap,
      color: "text-amber-400 border-amber-500/30 bg-amber-950/40"
    },
    {
      num: "05",
      title: "CATALOG CROSS-MATCH",
      desc: "Automated alignment with SDSS DR16, Simbad, and NASA archives.",
      icon: Database,
      color: "text-teal-400 border-teal-500/30 bg-teal-950/40"
    },
    {
      num: "06",
      title: "SCIENTIFIC REVIEW",
      desc: "High-priority targets presented to domain experts & AI Copilot.",
      icon: UserCheck,
      color: "text-emerald-400 border-emerald-500/30 bg-emerald-950/40"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold font-mono text-white tracking-tight">
          HOW ASTRA WORKS
        </h2>
        <p className="text-sm text-slate-400 font-sans">
          End-to-end autonomous satellite triage pipeline optimizing downlink bandwidth and scientific yield.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={step.num}
              className="glass-panel glass-panel-hover p-5 rounded-xl border relative overflow-hidden flex flex-col justify-between group"
            >
              {/* Connector line for desktop */}
              <div className="flex items-start justify-between">
                <span className="text-2xl font-mono font-bold text-slate-600 group-hover:text-cyan-400 transition-colors">
                  {step.num}
                </span>
                <div className={`p-3 rounded-lg border ${step.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>

              <div className="mt-4 space-y-1.5">
                <h3 className="text-sm font-mono font-bold text-slate-100 tracking-wider">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed font-sans">
                  {step.desc}
                </p>
              </div>

              {/* Progress Indicator */}
              <div className="mt-4 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>STAGE {idx + 1} OF 6</span>
                <span className="text-cyan-400">LATENCY OPTIMIZED</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
