import React, { useState } from 'react';
import type { ActiveTab } from '../types';
import { getRandomSpaceFact, type SpaceFact } from '../data/spaceFacts';
import {
  Compass,
  Sparkles,
  Search,
  Library,
  ShieldAlert,
  Bot,
  History,
  ArrowRight,
  RotateCcw,
  Rocket,
  ChevronRight,
  Telescope
} from 'lucide-react';

interface MissionBriefingPageProps {
  onNavigateTab: (tab: ActiveTab) => void;
}

export const MissionBriefingPage: React.FC<MissionBriefingPageProps> = ({ onNavigateTab }) => {
  const [currentFact, setCurrentFact] = useState<SpaceFact>(() => getRandomSpaceFact());

  const handleRefreshFact = () => {
    setCurrentFact(getRandomSpaceFact());
  };

  const modules = [
    {
      num: '01',
      title: 'RESEARCH',
      subtitle: 'Upload & Staged AI Triage Pipeline',
      description: 'Upload custom astronomical observation cutouts and run them through ASTRA’s Open-World Semantic Pre-Gate, Domain Gate V2, and Galaxy Zoo morphology triage engine.',
      icon: Search,
      tab: 'research' as ActiveTab,
      badge: 'ML PIPELINE',
      actionText: 'OPEN RESEARCH →',
      accent: 'border-[#C7CDD5]/30 hover:border-[#D5DAE0] bg-[#151B23]/40 text-[#D5DAE0]',
    },
    {
      num: '02',
      title: 'OBSERVATION LIBRARY',
      subtitle: '2,000 Galaxy Zoo 2 Scientific Archive',
      description: 'Explore 2,000 genuine Galaxy Zoo 2 astronomical observations with real DR7 IDs, celestial coordinates (RA/DEC), debiased vote distributions, and interactive Science Dossiers.',
      icon: Library,
      tab: 'library' as ActiveTab,
      badge: '2,000 OBJECTS',
      actionText: 'EXPLORE ARCHIVE →',
      accent: 'border-[#8FAFC2]/30 hover:border-[#8FAFC2] bg-[#15232E]/40 text-[#8FAFC2]',
    },
    {
      num: '03',
      title: 'ANOMALY QUEUE',
      subtitle: 'Operational Attention Workspace',
      description: 'Review observations prioritized by ASTRA for immediate scientific attention using our experimental out-of-distribution triage heuristic.',
      icon: ShieldAlert,
      tab: 'anomalies' as ActiveTab,
      badge: 'PRIORITY QUEUE',
      actionText: 'OPEN QUEUE →',
      accent: 'border-[#D6A84F]/30 hover:border-[#D6A84F] bg-[#3A2B15]/30 text-[#D6A84F]',
    },
    {
      num: '04',
      title: 'SPACE HELP AI',
      subtitle: 'Grounded Astronomy Assistant',
      description: 'Consult ASTRA Space Help AI for general astronomy concept explanations, galaxy morphology taxonomy, and observation-grounded QA.',
      icon: Bot,
      tab: 'copilot' as ActiveTab,
      badge: 'SPECIALIZED AI',
      actionText: 'TALK TO ASTRA →',
      accent: 'border-[#C7CDD5]/30 hover:border-[#D5DAE0] bg-[#151B23]/40 text-[#D5DAE0]',
    },
    {
      num: '05',
      title: 'HISTORY',
      subtitle: 'Session Analysis Ledger',
      description: 'Review historical record of previous triage runs, domain verification decisions, timestamps, and priority status flags from your active session.',
      icon: History,
      tab: 'history' as ActiveTab,
      badge: 'SESSION LEDGER',
      actionText: 'VIEW HISTORY →',
      accent: 'border-[#5FC7A1]/30 hover:border-[#5FC7A1] bg-[#0E241B]/30 text-[#5FC7A1]',
    },
  ];

  return (
    <div className="p-4 md:p-8 space-y-6 md:space-y-8 max-w-6xl mx-auto font-sans-ui text-[#F2F4F7] selection:bg-[#C7CDD5]/30">
      
      {/* ========================================================= */}
      {/* 1. OBSERVATORY HUD HERO HEADER                             */}
      {/* ========================================================= */}
      <div className="relative glass-panel p-6 md:p-8 rounded-2xl border border-[#C7CDD5]/30 bg-gradient-to-r from-[#030508] via-[#0D1219] to-[#030508] shadow-2xl overflow-hidden space-y-4">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#C7CDD5] to-transparent opacity-80" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#8FAFC2]/05 blur-3xl rounded-full pointer-events-none" />

        <div className="flex items-center justify-between border-b border-[#252D37] pb-3 font-mono-tech text-xs">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded bg-[#151B23] border border-[#C7CDD5]/30 text-[#D5DAE0] font-bold tracking-widest uppercase flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5" /> MISSION BRIEFING
            </span>
            <span className="text-[#A8B0BA]">ASTRA // OBSERVATORY SYSTEM</span>
          </div>
          <span className="text-[#5FC7A1] flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-[#5FC7A1]" />
            ASTRA SYSTEM READY
          </span>
        </div>

        <div className="space-y-3 max-w-3xl">
          <h1 className="text-3xl md:text-5xl font-serif-display font-bold text-[#F2F4F7] tracking-tight leading-tight uppercase">
            Your Window Into Astronomical Observations
          </h1>

          <p className="text-base md:text-lg font-serif-display text-[#D5DAE0]">
            "Find what deserves humanity's attention."
          </p>

          <p className="text-xs md:text-sm text-[#A8B0BA] font-sans-ui leading-relaxed max-w-2xl">
            ASTRA analyzes astronomical observations downlinked from survey streams, identifies statistically unusual patterns, and prioritizes observations for scientific review under tight downlink limits.
          </p>
        </div>

        <div className="pt-1 flex flex-wrap items-center gap-3">
          <button
            onClick={() => onNavigateTab('research')}
            className="px-5 py-3 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold tracking-widest transition-all shadow-xl shadow-black/40 flex items-center gap-2 cursor-pointer"
          >
            <Rocket className="w-4 h-4 text-[#070B11]" />
            START RESEARCH MODE
          </button>

          <button
            onClick={() => onNavigateTab('library')}
            className="px-5 py-3 rounded-lg glass-panel hover:bg-[#151B23] text-[#F2F4F7] font-mono-tech text-xs font-semibold tracking-widest border border-[#C7CDD5]/30 transition-all flex items-center gap-2 cursor-pointer"
          >
            EXPLORE ARCHIVE <Telescope className="w-4 h-4 text-[#8FAFC2]" />
          </button>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 2. TODAY'S SPACE FACT (EDITORIAL PANEL)                   */}
      {/* ========================================================= */}
      <div className="glass-panel p-5 md:p-6 rounded-2xl border border-[#D6A84F]/30 bg-gradient-to-r from-[#030508] via-[#3A2B15]/20 to-[#030508] shadow-xl space-y-3 relative">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D6A84F]/20 pb-3">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-[#D6A84F]" />
            <span className="text-xs font-mono-tech font-bold text-[#D6A84F] uppercase tracking-widest">
              ✦ TODAY'S SPACE FACT
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono-tech bg-[#3A2B15] text-[#D6A84F] border border-[#D6A84F]/40 px-3 py-1 rounded font-bold uppercase tracking-wider">
              {currentFact.category}
            </span>
            <button
              onClick={handleRefreshFact}
              title="Select another astronomy fact"
              className="p-1.5 rounded-md text-[#A8B0BA] hover:text-[#D5DAE0] hover:bg-[#151B23] transition-colors cursor-pointer flex items-center gap-1.5 text-[10px] font-mono-tech"
            >
              <RotateCcw className="w-3.5 h-3.5" /> NEW FACT
            </button>
          </div>
        </div>

        <p className="text-base md:text-lg text-[#F2F4F7] font-serif-display font-medium leading-relaxed max-w-4xl">
          "{currentFact.text}"
        </p>
      </div>

      {/* ========================================================= */}
      {/* 3. EDITORIAL EXPLORATION LAUNCHPAD SEQUENCE               */}
      {/* ========================================================= */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-[#252D37] pb-3 font-mono-tech">
          <div>
            <h2 className="text-lg font-serif-display font-bold text-[#F2F4F7] tracking-wider uppercase">
              What You Can Explore
            </h2>
            <p className="text-xs text-[#A8B0BA] font-sans-ui mt-0.5">
              Select an ASTRA module below to begin your mission session.
            </p>
          </div>
          <span className="text-xs text-[#717985]">05 MODULES ACTIVE</span>
        </div>

        <div className="space-y-3">
          {modules.map((mod) => {
            const Icon = mod.icon;
            return (
              <div
                key={mod.num}
                onClick={() => onNavigateTab(mod.tab)}
                className={`glass-panel p-5 md:p-6 rounded-xl border transition-all duration-300 cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4 hover:shadow-2xl ${mod.accent}`}
              >
                <div className="flex items-start md:items-center gap-5">
                  <span className="text-2xl md:text-3xl font-mono-tech font-bold text-[#717985] group-hover:text-current transition-colors">
                    {mod.num}
                  </span>
                  <div className="w-10 h-10 rounded-lg bg-[#030508] border border-[#252D37] flex items-center justify-center text-[#A8B0BA] group-hover:border-current group-hover:text-[#F2F4F7] transition-all shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-base md:text-lg font-serif-display font-semibold text-[#F2F4F7] group-hover:text-current transition-colors">
                        {mod.title}
                      </h3>
                      <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded bg-[#030508] border border-[#252D37] text-[#A8B0BA]">
                        {mod.badge}
                      </span>
                    </div>
                    <p className="text-xs font-mono-tech text-[#717985]">{mod.subtitle}</p>
                    <p className="text-xs text-[#A8B0BA] font-sans-ui max-w-2xl pt-0.5 leading-relaxed">
                      {mod.description}
                    </p>
                  </div>
                </div>

                <div className="shrink-0 flex items-center gap-2 font-mono-tech text-xs font-bold tracking-wider text-[#C7CDD5] group-hover:text-[#F2F4F7]">
                  <span>{mod.actionText}</span>
                  <ChevronRight className="w-4 h-4 text-[#717985] group-hover:text-current group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. READY TO EXPLORE CTA                                    */}
      {/* ========================================================= */}
      <div className="glass-panel p-8 md:p-10 rounded-2xl border border-[#C7CDD5]/30 bg-gradient-to-b from-[#0D1219] via-[#070B11] to-[#030508] text-center space-y-4 relative overflow-hidden">
        <div className="space-y-2 max-w-2xl mx-auto">
          <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block">
            READY TO EXPLORE?
          </span>
          <h2 className="text-2xl md:text-4xl font-serif-display font-bold text-[#F2F4F7] tracking-tight uppercase">
            Begin Observation Analysis
          </h2>
          <p className="text-xs md:text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
            Start by uploading an astronomical observation or explore prioritized anomalies in the scientific archive.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
          <button
            onClick={() => onNavigateTab('research')}
            className="px-6 py-3 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold tracking-widest transition-all shadow-xl shadow-black/40 flex items-center gap-2 cursor-pointer"
          >
            START RESEARCH <ArrowRight className="w-4 h-4 text-[#070B11]" />
          </button>

          <button
            onClick={() => onNavigateTab('library')}
            className="px-6 py-3 rounded-lg glass-panel hover:bg-[#151B23] text-[#F2F4F7] font-mono-tech text-xs font-semibold tracking-widest border border-[#C7CDD5]/30 hover:border-[#D5DAE0] transition-all flex items-center gap-2 cursor-pointer"
          >
            EXPLORE LIBRARY <Telescope className="w-4 h-4 text-[#8FAFC2]" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default MissionBriefingPage;
