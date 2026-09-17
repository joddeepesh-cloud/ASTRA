import React from 'react';
import type { ActiveTab } from '../types';
import { Compass, Radio, ShieldAlert, Library, Search, Bot, History, Settings, Rocket, ExternalLink } from 'lucide-react';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  onGoToLanding: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onGoToLanding }) => {
  const menuItems: { id: ActiveTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'briefing', label: 'Mission Briefing', icon: Compass },
    { id: 'research', label: 'Research & Upload', icon: Search },
    { id: 'observations', label: 'Observations', icon: Radio },
    { id: 'anomalies', label: 'Anomaly Queue', icon: ShieldAlert },
    { id: 'library', label: 'Observation Library', icon: Library },
    { id: 'history', label: 'Analysis History', icon: History },
    { id: 'copilot', label: 'Space Help AI', icon: Bot, badge: 'ACTIVE' },
  ];

  return (
    <aside className="w-64 bg-[#070912] border-r border-[#21133B] flex flex-col justify-between h-full shrink-0 z-40 relative select-none overflow-y-auto">
      {/* Brand Header & Navigation */}
      <div className="p-4 space-y-5 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 cursor-pointer" onClick={onGoToLanding}>
            <div className="w-9 h-9 rounded-xl bg-[#15102A] border border-[#9B7FD4]/40 flex items-center justify-center text-[#ECEAF2] shadow-md shadow-black/60">
              <Rocket className="w-5 h-5 text-[#8FD3FF]" />
            </div>
            <div>
              <span className="text-lg font-bold font-mono-tech text-white tracking-widest block leading-none">
                ASTRA
              </span>
              <span className="text-[9px] font-mono-tech text-[#55C7D9] tracking-wider uppercase mt-0.5 block font-semibold">
                OBSERVATORY SYSTEM
              </span>
            </div>
          </div>

          <button
            onClick={onGoToLanding}
            title="Return to Landing Page"
            className="p-1.5 rounded text-[#8E8A9D] hover:text-white hover:bg-[#15102A] border border-transparent hover:border-[#21133B] transition-all cursor-pointer"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1 overflow-y-auto flex-1 pr-0.5">
          <span className="text-[10px] font-mono-tech font-bold text-[#8E8A9D] uppercase tracking-widest px-3 block mb-2">
            NAVIGATION CONSOLE
          </span>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-mono-tech transition-all cursor-pointer relative ${
                  isActive
                    ? 'bg-[#15102A] text-white border border-[#9B7FD4]/50 font-bold shadow-lg shadow-black/60'
                    : 'text-[#8E8A9D] hover:text-[#ECEAF2] hover:bg-[#15102A]/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#8FD3FF]' : 'text-[#8E8A9D]'}`} />
                  <span>{item.label}</span>
                </div>

                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#8FD3FF] shadow-sm shadow-[#8FD3FF]" />
                )}

                {item.badge && !isActive && (
                  <span
                    className="text-[9px] px-1.5 py-0.5 rounded font-mono-tech font-bold bg-[#15102A] text-[#8FD3FF] border border-[#8FD3FF]/30"
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Settings & Bottom Status (Anchored Footer) */}
      <div className="p-4 border-t border-[#21133B] space-y-3 shrink-0 bg-[#070912]">
        <button
          onClick={() => setActiveTab('settings')}
          className={`w-full flex items-center justify-between px-3.5 py-2 text-xs font-mono-tech rounded-xl transition-all cursor-pointer ${
            activeTab === 'settings'
              ? 'bg-[#15102A] text-[#9B7FD4] border border-[#9B7FD4]/50 font-bold'
              : 'text-[#8E8A9D] hover:text-[#ECEAF2] hover:bg-[#15102A]/60 border border-transparent'
          }`}
        >
          <div className="flex items-center gap-3">
            <Settings className={`w-4 h-4 ${activeTab === 'settings' ? 'text-[#9B7FD4]' : 'text-[#8E8A9D]'}`} />
            <span>System Settings</span>
          </div>
          {activeTab === 'settings' && (
            <span className="w-1.5 h-1.5 rounded-full bg-[#9B7FD4] shadow-sm shadow-[#9B7FD4]" />
          )}
        </button>

        <div className="p-3 bg-[#0D0A1C] rounded-xl border border-[#21133B] space-y-1.5 font-mono-tech">
          <div className="flex justify-between items-center text-[10px] text-[#8E8A9D]">
            <span>SYSTEM</span>
            <span className="text-[#58BFA7] font-bold">NOMINAL</span>
          </div>
          <div className="w-full bg-[#03040A] h-1.5 rounded-full overflow-hidden border border-[#21133B]">
            <div className="bg-[#58BFA7] h-full w-[94%]" />
          </div>
          <div className="text-[9px] text-[#8E8A9D] text-right">
            DOWNLINK BANDWIDTH: 86% SAVED
          </div>
        </div>
      </div>
    </aside>
  );
};
