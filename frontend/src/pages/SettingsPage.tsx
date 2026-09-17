import React, { useState, useEffect } from 'react';
import { getHealth } from '../services/api';
import type { HealthResponse } from '../types/api';
import { getAnalysisHistory } from '../services/analysisHistory';
import { getReviewEvents } from '../services/reviewEventsService';
import {
  Cpu,
  Clock,
  Activity,
  Sliders,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Monitor,
  RefreshCw,
  Sparkles
} from 'lucide-react';

interface Preferences {
  reducedMotion: boolean;
  clockFormat: '12h' | '24h';
  autoScrollChat: boolean;
  compactView: boolean;
}

const PREF_STORAGE_KEY = 'astra_user_preferences';
const SESSION_START_KEY = 'astra_session_start_time';

export const SettingsPage: React.FC = () => {
  // Health & System Status
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);

  // Mission Clock State
  const [currentTime, setCurrentTime] = useState(new Date());

  // Session Duration State
  const [sessionStartTime] = useState<number>(() => {
    try {
      const stored = sessionStorage.getItem(SESSION_START_KEY);
      if (stored) return parseInt(stored, 10);
      const now = Date.now();
      sessionStorage.setItem(SESSION_START_KEY, now.toString());
      return now;
    } catch {
      return Date.now();
    }
  });
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Preferences State
  const [prefs, setPrefs] = useState<Preferences>(() => {
    try {
      const saved = localStorage.getItem(PREF_STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch {
      // Fallback
    }
    return {
      reducedMotion: false,
      clockFormat: '24h',
      autoScrollChat: true,
      compactView: false
    };
  });

  // Fetch Health Endpoint Data
  const refreshHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await getHealth();
      setHealth(res);
    } catch (e) {
      setHealth(null);
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  // Update Clock & Session Timer every second
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setCurrentTime(now);
      setElapsedSeconds(Math.floor((now.getTime() - sessionStartTime) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [sessionStartTime]);

  // Persist Preference Changes
  const togglePreference = (key: keyof Preferences) => {
    setPrefs((prev) => {
      const updated = { ...prev, [key]: key === 'clockFormat' ? (prev.clockFormat === '24h' ? '12h' : '24h') : !prev[key] };
      try {
        localStorage.setItem(PREF_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.warn('Failed to save preference:', e);
      }
      return updated;
    });
  };

  // Compute Session Metrics from Genuine Stores
  const userHistory = getAnalysisHistory();
  const reviewEvents = getReviewEvents();
  const deepAnalysisCount = reviewEvents.filter((e) => e.action === 'DEEP_ANALYSIS').length;
  const approvedCount = reviewEvents.filter((e) => e.action === 'APPROVE').length;

  // Format Elapsed Time
  const formatSessionDuration = (totalSec: number) => {
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    if (hrs > 0) {
      return `${hrs.toString().padStart(2, '0')}h ${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
    }
    return `${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
  };

  // Clock Display Format
  const formatDateStr = (d: Date) => {
    const day = d.getDate().toString().padStart(2, '0');
    const month = d.toLocaleString('en-US', { month: 'short' }).toUpperCase();
    const year = d.getFullYear();
    return `${day} ${month} ${year}`;
  };

  const formatTimeStr = (d: Date) => {
    if (prefs.clockFormat === '12h') {
      return d.toLocaleTimeString('en-US', { hour12: true });
    }
    return d.toLocaleTimeString('en-US', { hour12: false });
  };

  const timezoneStr = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-6 font-sans-ui text-[#ECEAF2]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21133B] pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold font-serif-display text-white tracking-wider flex items-center gap-2.5">
              <Sliders className="w-6 h-6 text-[#9B7FD4]" /> SYSTEM SETTINGS & DIAGNOSTICS
            </h1>
            <span className="text-xs font-mono-tech bg-[#21133B] text-[#9B7FD4] border border-[#9B7FD4]/40 px-2.5 py-0.5 rounded font-bold">
              MISSION CONSOLE
            </span>
          </div>
          <p className="text-xs text-[#8E8A9D] font-sans-ui mt-1">
            Real-time backend system status, mission clock, active session telemetry, and user preferences.
          </p>
        </div>

        <button
          onClick={refreshHealth}
          disabled={isCheckingHealth}
          className="px-4 py-2 rounded-lg bg-[#15102A] hover:bg-[#21133B] text-[#D8D3E2] border border-[#9B7FD4]/30 text-xs font-mono-tech flex items-center gap-2 transition-all cursor-pointer self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 text-[#8FD3FF] ${isCheckingHealth ? 'animate-spin' : ''}`} />
          <span>{isCheckingHealth ? 'CHECKING API...' : 'REFRESH STATUS'}</span>
        </button>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SECTION 1: SYSTEM STATUS */}
        <div className="glass-panel p-6 rounded-2xl border border-[#9B7FD4]/20 space-y-4">
          <div className="flex items-center justify-between border-b border-[#21133B] pb-3">
            <h2 className="text-sm font-mono-tech font-bold text-white tracking-wider uppercase flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#55C7D9]" /> SYSTEM STATUS & PIPELINE HEALTH
            </h2>
            <span className="text-[10px] font-mono-tech text-[#8E8A9D]">LIVE BACKEND TELEMETRY</span>
          </div>

          <div className="space-y-3 font-mono-tech text-xs">
            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">ML API STATUS</span>
              {health?.ml_ready ? (
                <span className="text-[#58BFA7] font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#58BFA7]" /> ONLINE / READY
                </span>
              ) : (
                <span className="text-amber-400 font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" /> STANDBY / OFFLINE
                </span>
              )}
            </div>

            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">EXECUTION DEVICE</span>
              <span className="text-[#8FD3FF] font-bold uppercase">{health?.device || 'MPS / PyTorch'}</span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">MORPHOLOGY MODEL</span>
              <span className="text-white font-bold">{health?.model_version || 'galaxy-zoo-efficientnet-b0'}</span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">DOMAIN GATE V2</span>
              <span className="text-[#9B7FD4] font-bold">{health?.domain_gate_model_version || 'mobilenet_v3_small_v2'}</span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">SEMANTIC PRE-GATE</span>
              <span className="text-[#55C7D9] font-bold">{health?.semantic_gate_model_version || 'open_clip_vit_b_32'}</span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[#0D0A1C] rounded-lg border border-[#21133B]">
              <span className="text-[#8E8A9D]">STARTUP LATENCY</span>
              <span className="text-[#ECEAF2] font-bold">{health?.startup_duration_ms ? `${health.startup_duration_ms.toFixed(1)} ms` : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* SECTION 2: MISSION CLOCK & SESSION TELEMETRY */}
        <div className="space-y-6">
          {/* Mission Clock Card */}
          <div className="glass-panel p-6 rounded-2xl border border-[#9B7FD4]/20 space-y-4">
            <div className="flex items-center justify-between border-b border-[#21133B] pb-3">
              <h2 className="text-sm font-mono-tech font-bold text-white tracking-wider uppercase flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#D6A84F]" /> MISSION CHRONOMETER
              </h2>
              <span className="text-[10px] font-mono-tech text-[#8E8A9D]">DYNAMIC REAL-TIME</span>
            </div>

            <div className="grid grid-cols-2 gap-4 font-mono-tech">
              <div className="bg-[#0D0A1C] p-4 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">CURRENT DATE</span>
                <span className="text-xl font-bold text-white block">{formatDateStr(currentTime)}</span>
              </div>

              <div className="bg-[#0D0A1C] p-4 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase tracking-wider">LOCAL TIME</span>
                <span className="text-xl font-bold text-[#8FD3FF] block">{formatTimeStr(currentTime)}</span>
              </div>
            </div>

            <div className="flex justify-between items-center text-xs font-mono-tech bg-[#0D0A1C] p-3 rounded-lg border border-[#21133B] text-[#8E8A9D]">
              <span>SYSTEM TIMEZONE:</span>
              <span className="text-[#ECEAF2] font-bold">{timezoneStr}</span>
            </div>
          </div>

          {/* Session Duration & Activity Telemetry */}
          <div className="glass-panel p-6 rounded-2xl border border-[#9B7FD4]/20 space-y-4">
            <div className="flex items-center justify-between border-b border-[#21133B] pb-3">
              <h2 className="text-sm font-mono-tech font-bold text-white tracking-wider uppercase flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#7657B8]" /> ACTIVE SESSION TELEMETRY
              </h2>
              <span className="text-[10px] font-mono-tech text-[#8E8A9D]">SESSION LEDGER</span>
            </div>

            <div className="grid grid-cols-2 gap-3 font-mono-tech text-xs">
              <div className="bg-[#0D0A1C] p-3.5 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase">SESSION DURATION</span>
                <span className="text-lg font-bold text-[#55C7D9] block">{formatSessionDuration(elapsedSeconds)}</span>
              </div>

              <div className="bg-[#0D0A1C] p-3.5 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase">ANALYZED RUNS</span>
                <span className="text-lg font-bold text-white block">{userHistory.length}</span>
              </div>

              <div className="bg-[#0D0A1C] p-3.5 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase">REVIEWS SUBMITTED</span>
                <span className="text-lg font-bold text-[#58BFA7] block">{approvedCount}</span>
              </div>

              <div className="bg-[#0D0A1C] p-3.5 rounded-xl border border-[#21133B] space-y-1">
                <span className="text-[10px] text-[#8E8A9D] block uppercase">DEEP ANALYSIS</span>
                <span className="text-lg font-bold text-[#9B7FD4] block">{deepAnalysisCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 3: USER PREFERENCES (PERSISTED) */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-[#9B7FD4]/20 space-y-6">
        <div className="border-b border-[#21133B] pb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-mono-tech font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Monitor className="w-5 h-5 text-[#8FD3FF]" /> WORKSTATION PREFERENCES
            </h2>
            <p className="text-xs text-[#8E8A9D] font-sans-ui mt-0.5">
              Customize interface behavior and mission console parameters. Preferences are saved locally in your browser.
            </p>
          </div>
          <span className="text-xs font-mono-tech text-[#58BFA7] bg-[#0E241B] border border-[#58BFA7]/30 px-3 py-1 rounded-full font-bold">
            LOCAL STORAGE PERSISTED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono-tech text-xs">
          {/* Reduced Motion Toggle */}
          <div className="p-4 bg-[#0D0A1C] rounded-xl border border-[#21133B] flex items-center justify-between">
            <div>
              <span className="font-bold text-white block">Reduced Motion</span>
              <span className="text-[11px] text-[#8E8A9D] block font-sans-ui mt-0.5">
                Disable background star pulse and floating animations.
              </span>
            </div>
            <button
              onClick={() => togglePreference('reducedMotion')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                prefs.reducedMotion
                  ? 'bg-[#7657B8] text-white border border-[#9B7FD4]'
                  : 'bg-[#15102A] text-[#8E8A9D] border border-[#21133B]'
              }`}
            >
              {prefs.reducedMotion ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Clock Format Toggle */}
          <div className="p-4 bg-[#0D0A1C] rounded-xl border border-[#21133B] flex items-center justify-between">
            <div>
              <span className="font-bold text-white block">Clock Format</span>
              <span className="text-[11px] text-[#8E8A9D] block font-sans-ui mt-0.5">
                Switch between 24-hour military time and 12-hour format.
              </span>
            </div>
            <button
              onClick={() => togglePreference('clockFormat')}
              className="px-3 py-1.5 rounded-lg bg-[#21133B] text-[#8FD3FF] border border-[#9B7FD4]/40 font-bold transition-all cursor-pointer"
            >
              {prefs.clockFormat}
            </button>
          </div>

          {/* Auto-scroll Chat Toggle */}
          <div className="p-4 bg-[#0D0A1C] rounded-xl border border-[#21133B] flex items-center justify-between">
            <div>
              <span className="font-bold text-white block">Auto-scroll Space AI</span>
              <span className="text-[11px] text-[#8E8A9D] block font-sans-ui mt-0.5">
                Automatically scroll to new responses in Space Help AI.
              </span>
            </div>
            <button
              onClick={() => togglePreference('autoScrollChat')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                prefs.autoScrollChat
                  ? 'bg-[#7657B8] text-white border border-[#9B7FD4]'
                  : 'bg-[#15102A] text-[#8E8A9D] border border-[#21133B]'
              }`}
            >
              {prefs.autoScrollChat ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Compact View Toggle */}
          <div className="p-4 bg-[#0D0A1C] rounded-xl border border-[#21133B] flex items-center justify-between">
            <div>
              <span className="font-bold text-white block">Compact Interface Density</span>
              <span className="text-[11px] text-[#8E8A9D] block font-sans-ui mt-0.5">
                Increase data density across observation tables.
              </span>
            </div>
            <button
              onClick={() => togglePreference('compactView')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                prefs.compactView
                  ? 'bg-[#7657B8] text-white border border-[#9B7FD4]'
                  : 'bg-[#15102A] text-[#8E8A9D] border border-[#21133B]'
              }`}
            >
              {prefs.compactView ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 4: ABOUT ASTRA & SCIENTIFIC DISCLAIMER */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-[#9B7FD4]/20 space-y-4 bg-[#0D0A1C]/90">
        <div className="flex items-center justify-between border-b border-[#21133B] pb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#55C7D9]" />
            <h2 className="text-base font-mono-tech font-bold text-white uppercase tracking-wider">
              ABOUT ASTRA OBSERVATORY SYSTEM
            </h2>
          </div>
          <span className="text-xs font-mono-tech text-[#8E8A9D]">VERSION 1.0.0</span>
        </div>

        <div className="space-y-3 text-xs font-sans-ui text-[#D8D3E2] leading-relaxed">
          <p>
            ASTRA (Astronomical Observation Triage System) is an experimental space software framework engineered to prioritize downlinked astronomical survey data under bandwidth constraints using multi-stage domain validation and out-of-distribution manifold feature distance calculations.
          </p>

          <div className="p-4 bg-[#03040A] rounded-xl border border-[#D6A84F]/30 text-amber-200/90 font-sans-ui text-xs space-y-1">
            <span className="font-mono-tech font-bold text-[#D6A84F] block text-[11px] uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#D6A84F]" /> OFFICIAL SCIENTIFIC PRIORITIZATION DISCLAIMER
            </span>
            <p>
              ASTRA prioritizes observations for scientific review. A high triage score is not proof that an observation represents a new astronomical object or phenomenon.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
