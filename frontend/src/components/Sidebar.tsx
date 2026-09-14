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
    { id: 'anomalies', label: 'Anomaly Queue', icon: ShieldAlert, badge: '127' },
    { id: 'library', label: 'Observation Library', icon: Library },
    { id: 'history', label: 'Analysis History', icon: History },
    { id: 'copilot', label: 'Space Help AI', icon: Bot, badge: 'ACTIVE' },
  ];

  return (
    <aside className="w-64 bg-[#070B11]/95 border-r border-[#252D37]/80 flex flex-col justify-between h-screen sticky top-0 z-40 backdrop-blur-xl selection:bg-[#C7CDD5]/30">
      {/* Brand Header */}
      <div className="p-5 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={onGoToLanding}>
            <div className="w-9 h-9 rounded-lg bg-[#151B23] border border-[#C7CDD5]/40 flex items-center justify-center text-[#D5DAE0] shadow-md shadow-black/50">
              <Rocket className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold font-mono-tech text-[#F2F4F7] tracking-widest block leading-none">
                ASTRA
              </span>
              <span className="text-[9px] font-mono-tech text-[#A8B0BA] tracking-wider uppercase mt-0.5 block">
                OBSERVATORY SYSTEM
              </span>
            </div>
          </div>

          <button
            onClick={onGoToLanding}
            title="Return to Landing Page"
            className="p-1.5 rounded text-[#717985] hover:text-[#D5DAE0] hover:bg-[#151B23] border border-transparent hover:border-[#252D37] transition-all cursor-pointer"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          <span className="text-[10px] font-mono-tech font-semibold text-[#717985] uppercase tracking-widest px-3 block mb-2">
            NAVIGATION
          </span>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-mono-tech transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#252D37] text-[#F2F4F7] border border-[#C7CDD5]/50 font-bold shadow-md shadow-black/40'
                    : 'text-[#A8B0BA] hover:text-[#F2F4F7] hover:bg-[#151B23]/70 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#8FAFC2]' : 'text-[#717985]'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded font-mono-tech font-bold ${
                      item.id === 'anomalies'
                        ? 'bg-[#3A1D1D] text-[#D6A84F] border border-[#D6A84F]/40'
                        : 'bg-[#15232E] text-[#8FAFC2] border border-[#8FAFC2]/40'
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
      <div className="p-4 border-t border-[#151B23] space-y-3">
        <button
          onClick={() => setActiveTab('research')}
          className="w-full flex items-center gap-3 px-3 py-2 text-xs font-mono-tech text-[#717985] hover:text-[#D5DAE0] hover:bg-[#151B23]/60 rounded-lg transition-all cursor-pointer"
        >
          <Settings className="w-4 h-4 text-[#717985]" />
          <span>System Settings</span>
        </button>

        <div className="p-3 bg-[#0D1219] rounded-lg border border-[#252D37] space-y-1.5 font-mono-tech">
          <div className="flex justify-between items-center text-[10px] text-[#A8B0BA]">
            <span>SYSTEM</span>
            <span className="text-[#5FC7A1] font-bold">NOMINAL</span>
          </div>
          <div className="w-full bg-[#030508] h-1.5 rounded-full overflow-hidden">
            <div className="bg-[#5FC7A1] h-full w-[94%]" />
          </div>
          <div className="text-[9px] text-[#717985] text-right">
            DOWNLINK BANDWIDTH: 86% SAVED
          </div>
        </div>
      </div>
    </aside>
  );
};
