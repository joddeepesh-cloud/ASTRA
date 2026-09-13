import React from 'react';
import type { ActiveTab } from '../types';
import { LayoutDashboard, Radio, ShieldAlert, Library, Search, Bot, Settings, Rocket, ExternalLink } from 'lucide-react';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  onGoToLanding: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onGoToLanding }) => {
  const menuItems: { id: ActiveTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'overview', label: 'Mission Overview', icon: LayoutDashboard },
    { id: 'observations', label: 'Observations', icon: Radio },
    { id: 'anomalies', label: 'Anomaly Queue', icon: ShieldAlert, badge: '127' },
    { id: 'library', label: 'Observation Library', icon: Library },
    { id: 'research', label: 'Research & Upload', icon: Search },
    { id: 'copilot', label: 'AI Mission Copilot', icon: Bot, badge: 'READY' },
  ];

  return (
    <aside className="w-64 bg-slate-950/90 border-r border-slate-800/80 flex flex-col justify-between h-screen sticky top-0 z-40 backdrop-blur-xl">
      {/* Brand Header */}
      <div className="p-5 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={onGoToLanding}>
            <div className="w-9 h-9 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-md shadow-cyan-950/50">
              <Rocket className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold font-mono text-white tracking-wider block leading-none">
                ASTRA
              </span>
              <span className="text-[10px] font-mono text-slate-400 tracking-widest uppercase">
                MISSION CONTROL
              </span>
            </div>
          </div>

          <button
            onClick={onGoToLanding}
            title="Return to Landing Page"
            className="p-1.5 rounded text-slate-400 hover:text-cyan-400 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all cursor-pointer"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-widest px-3 block mb-2">
            NAVIGATION
          </span>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                  isActive
                    ? 'bg-cyan-950/70 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-950'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      item.id === 'anomalies'
                        ? 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                        : 'bg-indigo-950/80 text-indigo-300 border border-indigo-800/60'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Settings & Bottom Status */}
      <div className="p-4 border-t border-slate-900 space-y-3">
        <button
          onClick={() => setActiveTab('research')}
          className="w-full flex items-center gap-3 px-3 py-2 text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 rounded-lg transition-all cursor-pointer"
        >
          <Settings className="w-4 h-4 text-slate-400" />
          <span>System Settings</span>
        </button>

        <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800/80 space-y-1.5">
          <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
            <span>MISSION 01</span>
            <span className="text-emerald-400 font-bold">NOMINAL</span>
          </div>
          <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full w-[94%]" />
          </div>
          <div className="text-[9px] font-mono text-slate-500 text-right">
            DOWNLINK BANDWIDTH: 86% SAVED
          </div>
        </div>
      </div>
    </aside>
  );
};
