import React, { useEffect, useState } from 'react';
import { Search, Bell, Satellite, Cpu, WifiOff } from 'lucide-react';
import { getHealth } from '../services/api';
import type { HealthResponse } from '../types/api';

interface TopBarProps {
  title: string;
  subtitle?: string;
  onSearchClick?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ title, subtitle, onSearchClick }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let isMounted = true;
    getHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setHealthStatus(data.ml_ready ? 'online' : 'offline');
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealthStatus('offline');
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <header className="h-16 bg-slate-950/80 border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-base md:text-lg font-bold font-mono text-white tracking-wider uppercase flex items-center gap-2">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-slate-400 font-sans">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {healthStatus === 'online' ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono tracking-wider shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>ML API ONLINE ({health?.device?.toUpperCase() || 'GPU'})</span>
          </div>
        ) : healthStatus === 'offline' ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/40 border border-amber-500/30 text-amber-300 text-xs font-mono tracking-wider shadow-sm">
            <WifiOff className="w-3.5 h-3.5 text-amber-400" />
            <span>LIVE ANALYSIS OFFLINE</span>
          </div>
        ) : (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400 text-xs font-mono">
            <Cpu className="w-3.5 h-3.5 animate-spin text-cyan-400" />
            <span>CONNECTING...</span>
          </div>
        )}

        <div className="h-5 w-px bg-slate-800 hidden md:block" />

        <div className="flex items-center gap-2">
          <button
            onClick={onSearchClick}
            className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded-lg border border-transparent hover:border-slate-800 transition-all cursor-pointer"
            title="Search Observations"
          >
            <Search className="w-4 h-4" />
          </button>

          <button
            className="p-2 text-slate-400 hover:text-amber-400 hover:bg-slate-900 rounded-lg border border-transparent hover:border-slate-800 transition-all relative cursor-pointer"
            title="Mission Alerts"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500" />
          </button>

          <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-slate-900/80 rounded border border-slate-800 text-xs font-mono text-slate-300">
            <Satellite className="w-3.5 h-3.5 text-cyan-400" />
            <span>SAT-ORBIT 01</span>
          </div>
        </div>
      </div>
    </header>
  );
};
