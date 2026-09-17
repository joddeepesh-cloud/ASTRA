import React, { useState, useRef, useEffect } from 'react';
import libraryData from '../data/observationLibrary.json';
import type { Observation } from '../types';
import {
  Rocket,
  ArrowRight,
  Telescope,
  Sparkles,
  ChevronDown,
  ShieldCheck,
  Cpu,
  Activity
} from 'lucide-react';
import { CosmicBackground } from '../components/CosmicBackground';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

type TargetCategory = 'galaxies' | 'planets' | 'anomalies';

interface TargetInfo {
  id: TargetCategory;
  name: string;
  badge: string;
  image: string;
  video: string;
  poster: string;
  ra: string;
  dec: string;
  gz2Class: string;
  priorityAlert?: string;
  headline: string;
  description: string;
  accentBorder: string;
  accentText: string;
}

const TARGET_DATA: Record<TargetCategory, TargetInfo> = {
  galaxies: {
    id: 'galaxies',
    name: 'GALAXIES',
    badge: 'GALAXY ZOO 2',
    image: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=600&q=80',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_3ffb4889-c520-432d-8458-038009eb40df.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_508c64b8-a31e-4290-bdfc-1187df70e0a6.png',
    ra: 'RA: 160.990°',
    dec: 'DEC: +11.703°',
    gz2Class: 'MORPHOLOGY: BARRED SPIRAL',
    headline: 'GALAXIES',
    description: 'Explore distant galaxies and examine their observed morphology, structure, and unusual patterns.',
    accentBorder: 'border-[#C7CDD5]/40 hover:border-[#D5DAE0]',
    accentText: 'text-[#D5DAE0]'
  },
  planets: {
    id: 'planets',
    name: 'PLANETS',
    badge: 'ORBITAL SURVEY',
    image: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202005_3346cc4d-ec3b-44ab-825c-b18e49f5021a.png',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_b211cd74-013b-4dd3-bfd0-64491d8696fa.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_cf55d1d8-7b59-4a64-80da-d72052ae974e.png',
    ra: 'ALT: 400km',
    dec: 'ORBITAL SCAN 01',
    gz2Class: 'SURVEY: ATMOSPHERIC DATA',
    headline: 'PLANETS',
    description: 'Explore planetary environments and the astronomical observations captured around them.',
    accentBorder: 'border-[#8FAFC2]/40 hover:border-[#8FAFC2]',
    accentText: 'text-[#8FAFC2]'
  },
  anomalies: {
    id: 'anomalies',
    name: 'ANOMALIES',
    badge: 'PRIORITY TRIAGE',
    image: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=600&q=80',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_51eae59a-2459-4c84-907c-cc5edfe5fea7.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_0ba6de7c-285d-43dc-b7ab-8c54c73707cb.png',
    ra: 'RA: 215.112°',
    dec: 'DEC: -1.042°',
    gz2Class: 'INTERACTING MERGER',
    priorityAlert: 'TRIAGE SCORE: 0.970',
    headline: 'ANOMALIES',
    description: 'Investigate observations that ASTRA considers unusual and prioritizes for scientific review.',
    accentBorder: 'border-[#D6A84F]/40 hover:border-[#D6A84F]',
    accentText: 'text-[#D6A84F]'
  }
};

const TARGET_ORDER: TargetCategory[] = ['galaxies', 'planets', 'anomalies'];

interface LandingPageProps {
  onExplore: () => void;
  onViewObservations?: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onExplore, onViewObservations }) => {
  const [activeTarget, setActiveTarget] = useState<TargetCategory>('galaxies');
  const [loadedVideos, setLoadedVideos] = useState<Record<TargetCategory, boolean>>({
    galaxies: true,
    planets: false,
    anomalies: false
  });

  const pipelineRef = useRef<HTMLDivElement>(null);
  const missionRef = useRef<HTMLDivElement>(null);
  const archiveRef = useRef<HTMLDivElement>(null);

  const warmVideo = (key: TargetCategory) => {
    if (!loadedVideos[key]) {
      setLoadedVideos(prev => ({ ...prev, [key]: true }));
    }
  };

  const showTarget = (nextKey: TargetCategory) => {
    warmVideo(nextKey);
    setActiveTarget(nextKey);
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoadedVideos({ galaxies: true, planets: true, anomalies: true });
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const scrollToRef = (ref: React.RefObject<HTMLDivElement | null>) => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleViewObs = () => {
    if (onViewObservations) {
      onViewObservations();
    } else {
      onExplore();
    }
  };

  return (
    <div className="min-h-screen bg-[#050811] text-[#E9EEF4] flex flex-col relative overflow-x-hidden font-sans-ui selection:bg-[#8FD3FF]/30">
      <CosmicBackground variant="landing" />
      
      {/* ========================================================= */}
      {/* 1. CINEMATIC FULL VIEWPORT ATMOSPHERIC BACKGROUND SYSTEM  */}
      {/* ========================================================= */}
      <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none z-0">
        {TARGET_ORDER.map(key => (
          <img
            key={`poster-${key}`}
            src={TARGET_DATA[key].poster}
            alt={`${TARGET_DATA[key].name} Poster Background`}
            className={`absolute inset-0 w-full h-full object-cover object-center pointer-events-none transition-opacity duration-700 ${
              activeTarget === key ? 'opacity-40 z-10' : 'opacity-0 z-0'
            }`}
          />
        ))}

        {TARGET_ORDER.map(key => (
          <video
            key={`video-${key}`}
            autoPlay
            muted
            loop
            playsInline
            preload={key === 'galaxies' ? 'auto' : 'none'}
            poster={TARGET_DATA[key].poster}
            src={loadedVideos[key] ? TARGET_DATA[key].video : undefined}
            className={`absolute inset-0 w-full h-full object-cover object-center pointer-events-none transition-opacity duration-700 ${
              activeTarget === key ? 'opacity-50 z-20' : 'opacity-0 z-0'
            }`}
          />
        ))}

        {/* Dynamic Deep Cosmos Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#030508]/90 via-[#070B11]/80 to-[#030508] pointer-events-none z-30" />
        <div className="absolute inset-0 star-grid opacity-25 pointer-events-none z-30" />
        <div className="absolute inset-0 scanline-overlay opacity-15 pointer-events-none z-30" />
      </div>

      {/* Atmospheric Ambient Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-[#8FAFC2]/06 blur-[160px] pointer-events-none rounded-full z-0" />

      {/* ========================================================= */}
      {/* 2. SPACE-AGENCY TOP METADATA & NAVIGATION BAR            */}
      {/* ========================================================= */}
      <header className="px-6 md:px-12 py-5 max-w-7xl mx-auto w-full flex items-center justify-between z-40 relative border-b border-[#252D37]/70 bg-[#070B11]/70 backdrop-blur-md">
        
        {/* Brand Wordmark & Agency Tag */}
        <div className="flex items-center gap-4 cursor-pointer" onClick={onExplore}>
          <div className="w-10 h-10 rounded-lg bg-[#151B23] border border-[#C7CDD5]/40 flex items-center justify-center text-[#D5DAE0] shadow-lg shadow-black/50">
            <Rocket className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold font-mono-tech text-[#F2F4F7] tracking-widest leading-none">
                ASTRA
              </span>
              <span className="px-2 py-0.5 rounded bg-[#151B23] border border-[#C7CDD5]/30 text-[9px] font-mono-tech text-[#C7CDD5] tracking-wider uppercase">
                MISSION // ASTRA-01
              </span>
            </div>
            <span className="text-[9px] font-mono-tech text-[#A8B0BA] tracking-wider uppercase mt-1 block">
              ASTRONOMICAL OBSERVATION TRIAGE SYSTEM
            </span>
          </div>
        </div>

        {/* Center Nav Links */}
        <nav className="hidden lg:flex items-center gap-8 font-mono-tech text-xs tracking-wider text-[#C7CDD5]">
          <button onClick={() => scrollToRef(missionRef)} className="hover:text-[#F2F4F7] transition-colors cursor-pointer flex items-center gap-1.5">
            <span className="text-[#8FAFC2]">01</span> MISSION
          </button>
          <button onClick={() => scrollToRef(pipelineRef)} className="hover:text-[#F2F4F7] transition-colors cursor-pointer flex items-center gap-1.5">
            <span className="text-[#8FAFC2]">02</span> PIPELINE
          </button>
          <button onClick={() => scrollToRef(archiveRef)} className="hover:text-[#F2F4F7] transition-colors cursor-pointer flex items-center gap-1.5">
            <span className="text-[#8FAFC2]">03</span> ARCHIVE
          </button>
        </nav>

        {/* Action Button */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono-tech text-[#5FC7A1] bg-[#0E241B] border border-[#5FC7A1]/30 px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-[#5FC7A1] animate-pulse" />
            <span>SYSTEM NOMINAL</span>
          </div>

          <button
            onClick={onExplore}
            className="px-5 py-2.5 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold tracking-wider transition-all shadow-lg shadow-black/40 flex items-center gap-2 cursor-pointer"
          >
            EXPLORE THE MISSION <ArrowRight className="w-4 h-4 text-[#070B11]" />
          </button>
        </div>
      </header>

      {/* ========================================================= */}
      {/* 3. EDITORIAL HERO SECTION                                 */}
      {/* ========================================================= */}
      <section className="relative min-h-[calc(100vh-80px)] w-full flex flex-col justify-between z-20 overflow-hidden px-6 md:px-12 max-w-7xl mx-auto py-8">
        
        {/* Top Space-Agency Metadata Bar */}
        <div className="w-full grid grid-cols-2 md:grid-cols-4 gap-3 font-mono-tech text-xs pt-4 border-t border-[#252D37]/70">
          <div className="p-2.5 rounded-lg glass-panel border border-[#252D37]">
            <span className="text-[9px] text-[#717985] block uppercase tracking-wider">MISSION DESIGNATION</span>
            <span className="text-xs font-bold text-[#F2F4F7] tracking-widest mt-0.5 block">ASTRA-01 // SIH-2026</span>
          </div>
          <div className="p-2.5 rounded-lg glass-panel border border-[#252D37]">
            <span className="text-[9px] text-[#717985] block uppercase tracking-wider">CURATED ARCHIVE</span>
            <span className="text-xs font-bold text-[#D5DAE0] tracking-widest mt-0.5 block">2,000 GZ2 OBSERVATIONS</span>
          </div>
          <div className="p-2.5 rounded-lg glass-panel border border-[#252D37]">
            <span className="text-[9px] text-[#717985] block uppercase tracking-wider">PRE-GATE SECURITY</span>
            <span className="text-xs font-bold text-[#5FC7A1] tracking-widest mt-0.5 block">OPEN-WORLD SEMANTIC</span>
          </div>
          <div className="p-2.5 rounded-lg glass-panel border border-[#252D37]">
            <span className="text-[9px] text-[#717985] block uppercase tracking-wider">TRIAGE ENGINE</span>
            <span className="text-xs font-bold text-[#D6A84F] tracking-widest mt-0.5 block">GALAXY ZOO 2 ACTIVE</span>
          </div>
        </div>

        {/* MAIN HERO EDITORIAL LAYOUT */}
        <div className="my-auto py-12 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Typography & CTAs */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#0D1219] border border-[#C7CDD5]/30 text-[#D5DAE0] text-xs font-mono-tech tracking-widest uppercase">
              <Sparkles className="w-3.5 h-3.5 text-[#D6A84F] animate-pulse" />
              <span>ASTRONOMICAL OBSERVATION TRIAGE</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-6xl sm:text-7xl md:text-8xl font-serif-display font-bold text-[#F2F4F7] tracking-tight leading-none uppercase">
                <span className="bg-gradient-to-b from-[#F2F4F7] via-[#D5DAE0] to-[#8FAFC2] bg-clip-text text-transparent">
                  ASTRA
                </span>
              </h1>
              <div className="h-[2px] bg-gradient-to-r from-[#D5DAE0] via-[#8FAFC2] to-transparent w-48 rounded-full" />
            </div>

            <p className="text-xl sm:text-2xl font-serif-display font-medium text-[#F2F4F7] leading-snug">
              "Find what deserves humanity's attention."
            </p>

            <p className="text-base text-[#A8B0BA] font-sans-ui font-normal leading-relaxed max-w-xl">
              ASTRA analyzes astronomical observations, identifies statistically unusual patterns, and prioritizes observations for scientific review under tight bandwidth limits.
            </p>

            <div className="pt-4 flex flex-wrap items-center gap-4">
              <button
                onClick={onExplore}
                className="px-8 py-4 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs sm:text-sm font-bold tracking-widest transition-all shadow-xl shadow-black/40 flex items-center gap-3 cursor-pointer"
              >
                EXPLORE THE MISSION <ArrowRight className="w-4 h-4 text-[#070B11]" />
              </button>

              <button
                onClick={handleViewObs}
                className="px-8 py-4 rounded-lg glass-panel hover:bg-[#151B23] text-[#F2F4F7] font-mono-tech text-xs sm:text-sm font-semibold tracking-widest transition-all flex items-center gap-3 border border-[#C7CDD5]/30 hover:border-[#D5DAE0] cursor-pointer"
              >
                VIEW OBSERVATIONS <Telescope className="w-4 h-4 text-[#8FAFC2]" />
              </button>
            </div>
          </div>

          {/* Right Column: Redesigned Interactive Observation Target Panel */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center relative">
            <div className="w-full max-w-sm glass-panel p-6 rounded-2xl border border-[#C7CDD5]/30 space-y-5 relative overflow-hidden bg-[#0D1219]/90 backdrop-blur-xl shadow-2xl">
              
              {/* Target HUD Header */}
              <div className="flex items-center justify-between font-mono-tech text-xs text-[#A8B0BA] border-b border-[#252D37] pb-3">
                <span className="text-[#D5DAE0] font-semibold tracking-wider">OBSERVATION TARGET</span>
                <span className="uppercase text-[10px] px-2 py-0.5 rounded bg-[#151B23] border border-[#252D37] text-[#C7CDD5] font-bold">
                  {TARGET_DATA[activeTarget].badge}
                </span>
              </div>

              {/* Main Preview Orb Container */}
              <div className="relative aspect-square w-full rounded-full overflow-hidden border border-[#C7CDD5]/40 shadow-[0_0_40px_rgba(213,218,224,0.10)] flex items-center justify-center bg-[#030508]">
                {TARGET_ORDER.map(key => (
                  <img
                    key={`target-img-${key}`}
                    src={TARGET_DATA[key].image}
                    alt={`${TARGET_DATA[key].name} Target`}
                    className={`absolute inset-0 w-full h-full object-cover transition-all duration-500 ${
                      activeTarget === key ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'
                    }`}
                  />
                ))}
                
                {/* Scientific HUD Overlay Lines */}
                <div className="absolute inset-0 border border-[#C7CDD5]/20 rounded-full pointer-events-none" />
                <div className="absolute inset-4 border border-dashed border-[#C7CDD5]/15 rounded-full pointer-events-none" />
                
                {/* Target Reticle Overlay for Anomalies */}
                {activeTarget === 'anomalies' && (
                  <div className="absolute inset-0 bg-gradient-to-b from-[#D6A84F]/15 via-transparent to-transparent pointer-events-none animate-pulse" />
                )}

                {/* RA/DEC HUD Overlays */}
                <div className="absolute top-4 left-4 font-mono-tech text-[9px] text-[#D5DAE0] bg-[#030508]/90 px-2 py-0.5 rounded border border-[#C7CDD5]/30 shadow-md">
                  {TARGET_DATA[activeTarget].ra}
                </div>
                <div className="absolute bottom-4 right-4 font-mono-tech text-[9px] text-[#D5DAE0] bg-[#030508]/90 px-2 py-0.5 rounded border border-[#C7CDD5]/30 shadow-md">
                  {TARGET_DATA[activeTarget].dec}
                </div>

                {/* Priority Alert Badge for Anomalies */}
                {TARGET_DATA[activeTarget].priorityAlert && (
                  <div className="absolute top-4 right-4 font-mono-tech text-[9px] font-bold text-[#D6A84F] bg-[#3A2B15]/90 px-2 py-0.5 rounded border border-[#D6A84F]/50 shadow-md">
                    {TARGET_DATA[activeTarget].priorityAlert}
                  </div>
                )}
              </div>

              {/* Target Switcher Selector Buttons: GALAXIES | PLANETS | ANOMALIES */}
              <div className="grid grid-cols-3 gap-2 font-mono-tech text-xs">
                {TARGET_ORDER.map(key => (
                  <button
                    key={`tab-btn-${key}`}
                    onClick={() => showTarget(key)}
                    className={`py-2 px-1 rounded-md border text-center transition-all duration-300 cursor-pointer ${
                      activeTarget === key
                        ? key === 'anomalies'
                          ? 'bg-[#3A2B15] border-[#D6A84F] text-[#D6A84F] font-bold shadow-md'
                          : key === 'planets'
                          ? 'bg-[#15232E] border-[#8FAFC2] text-[#8FAFC2] font-bold shadow-md'
                          : 'bg-[#252D37] border-[#C7CDD5] text-[#F2F4F7] font-bold shadow-md'
                        : 'bg-[#151B23]/70 border-[#252D37] text-[#717985] hover:text-[#C7CDD5]'
                    }`}
                  >
                    {key.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Category Description */}
              <div className="space-y-1.5 pt-1 text-left border-t border-[#252D37]">
                <div className="flex items-center justify-between font-mono-tech text-xs">
                  <span className={`font-bold tracking-wider ${TARGET_DATA[activeTarget].accentText}`}>
                    {TARGET_DATA[activeTarget].headline}
                  </span>
                  <span className="text-[9px] text-[#717985]">
                    {TARGET_DATA[activeTarget].gz2Class}
                  </span>
                </div>
                <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                  "{TARGET_DATA[activeTarget].description}"
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Scroll Indicator */}
        <div className="w-full flex justify-center pb-4 pt-2">
          <button
            onClick={() => scrollToRef(missionRef)}
            className="flex items-center gap-2 cursor-pointer opacity-75 hover:opacity-100 transition-opacity font-mono-tech text-[10px] text-[#717985] uppercase tracking-widest"
          >
            <span>SCROLL TO EXPLORE THE MISSION</span>
            <ChevronDown className="w-4 h-4 text-[#8FAFC2] animate-bounce" />
          </button>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 4. SECTION 01 — THE MISSION                               */}
      {/* ========================================================= */}
      <section ref={missionRef} className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full z-20 border-t border-[#252D37]">
        <div className="space-y-16">
          
          {/* Section Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[#252D37] pb-6">
            <div>
              <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block mb-2">
                01 — THE MISSION
              </span>
              <h2 className="text-3xl md:text-5xl font-serif-display font-bold text-[#F2F4F7] tracking-tight">
                Solving the Astronomical Downlink Bottleneck
              </h2>
            </div>
            <p className="text-sm font-mono-tech text-[#717985] max-w-md">
              Modern observatories generate terabytes of survey data per day. Human expert verification cannot scale without AI-driven triage.
            </p>
          </div>

          {/* 3 Core Pillars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all">
              <div className="w-12 h-12 rounded-lg bg-[#151B23] border border-[#C7CDD5]/30 flex items-center justify-center text-[#D5DAE0]">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">Downlink Bandwidth Limits</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Deep space transmissions and ground survey networks operate under severe bandwidth constraints. ASTRA ensures highest-value observations transmit first.
              </p>
            </div>

            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all">
              <div className="w-12 h-12 rounded-lg bg-[#0E241B] border border-[#5FC7A1]/30 flex items-center justify-center text-[#5FC7A1]">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">Open-World Pre-Gate</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Before running specialized astronomical classification models, CLIP-powered semantic pre-screening rejects non-astronomy images cleanly.
              </p>
            </div>

            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all">
              <div className="w-12 h-12 rounded-lg bg-[#3A2B15] border border-[#D6A84F]/30 flex items-center justify-center text-[#D6A84F]">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">Scientific Triage Score</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Calculates a calibrated triage score combining Galaxy Zoo 2 morphology confidence, out-of-distribution entropy, and catalog novelty.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 5. SECTION 02 — HOW ASTRA THINKS (PIPELINE)               */}
      {/* ========================================================= */}
      <section ref={pipelineRef} className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full z-20 border-t border-[#252D37]">
        <div className="space-y-16">
          
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block">
              02 — HOW ASTRA THINKS
            </span>
            <h2 className="text-3xl md:text-5xl font-serif-display font-bold text-[#F2F4F7] tracking-tight">
              The Autonomous Scientific Triage Pipeline
            </h2>
            <p className="text-sm text-[#A8B0BA] font-sans-ui max-w-xl mx-auto">
              Every incoming observation passes through a strict 6-stage pipeline before reaching the priority queue.
            </p>
          </div>

          {/* 6-Stage Pipeline Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#D5DAE0] font-bold">STAGE 01</span>
                <span>INGEST</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Observation Ingest</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                Receives FITS or high-resolution optical survey cutouts with RA/DEC celestial coordinates and exposure metadata.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#5FC7A1] font-bold">STAGE 02</span>
                <span>PRE-GATE</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Semantic Screening</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                Evaluates open-world visual concepts (animals, vehicles, text) to block out-of-domain submissions before model inference.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#8FAFC2] font-bold">STAGE 03</span>
                <span>DOMAIN V2</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Domain Validation</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                Verifies celestial spectral characteristics against learned astronomical image distributions.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#C7CDD5] font-bold">STAGE 04</span>
                <span>GALAXY ZOO 2</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Morphology Prediction</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                Classifies galaxy morphology into Smooth, Featured/Disk, Edge-on, or Spiral categories with class probabilities.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#D6A84F] font-bold">STAGE 05</span>
                <span>HEURISTIC</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Triage Scoring</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                Calculates the experimental triage priority score using entropy, out-of-distribution distance, and catalog cross-matches.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/40 transition-all space-y-3">
              <div className="flex items-center justify-between text-xs font-mono-tech text-[#717985]">
                <span className="text-[#D5DAE0] font-bold">STAGE 06</span>
                <span>HUMAN-IN-LOOP</span>
              </div>
              <h3 className="text-lg font-serif-display font-semibold text-[#F2F4F7]">Scientific Review</h3>
              <p className="text-xs text-[#A8B0BA] font-sans-ui leading-relaxed">
                High-priority targets are queued in the Anomaly Queue for expert astrophysicist review and deep inspection.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 6. SECTION 03 — WHAT ASTRA LOOKS FOR (TRIAGE SIGNALS)     */}
      {/* ========================================================= */}
      <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full z-20 border-t border-[#252D37]">
        <div className="space-y-16">
          
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[#252D37] pb-6">
            <div>
              <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block mb-2">
                03 — WHAT ASTRA LOOKS FOR
              </span>
              <h2 className="text-3xl md:text-5xl font-serif-display font-bold text-[#F2F4F7] tracking-tight">
                Key Scientific Triage Signals
              </h2>
            </div>
            <p className="text-sm font-mono-tech text-[#717985] max-w-md">
              Observations are prioritized based on three explicit mathematical criteria.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37]">
              <span className="text-3xl font-mono-tech font-bold text-[#D5DAE0]">01</span>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">NOVELTY</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Identifies non-symmetric tidal disruptions, unexpected arm structures, ring features, or tidal tails that deviate from standard galaxy catalogs.
              </p>
            </div>

            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37]">
              <span className="text-3xl font-mono-tech font-bold text-[#8FAFC2]">02</span>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">UNCERTAINTY</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Measures model classification entropy. High-entropy predictions highlight borderline, complex, or overlapping objects requiring human verification.
              </p>
            </div>

            <div className="glass-panel p-8 rounded-xl space-y-4 border border-[#252D37]">
              <span className="text-3xl font-mono-tech font-bold text-[#D6A84F]">03</span>
              <h3 className="text-xl font-serif-display font-semibold text-[#F2F4F7]">ODDITY</h3>
              <p className="text-sm text-[#A8B0BA] font-sans-ui leading-relaxed">
                Surfaces statistical confidence outliers in feature space relative to the Galaxy Zoo 2 dataset baseline manifold.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 7. SECTION 04 — EXPLORE THE ARCHIVE                       */}
      {/* ========================================================= */}
      <section ref={archiveRef} className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full z-20 border-t border-[#252D37]">
        <div className="space-y-12">
          
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[#252D37] pb-6">
            <div>
              <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block mb-2">
                04 — EXPLORE THE ARCHIVE
              </span>
              <h2 className="text-3xl md:text-5xl font-serif-display font-bold text-[#F2F4F7] tracking-tight">
                Curated Galaxy Zoo 2 Archive
              </h2>
            </div>
            <button
              onClick={handleViewObs}
              className="px-5 py-2.5 rounded-lg border border-[#C7CDD5]/40 hover:bg-[#151B23] text-[#D5DAE0] font-mono-tech text-xs font-bold tracking-wider transition-all flex items-center gap-2 cursor-pointer"
            >
              EXPLORE FULL OBSERVATION LIBRARY <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Genuine Observation Cards Preview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {LIBRARY_OBSERVATIONS.slice(0, 3).map(obs => (
              <div key={obs.id} className="glass-panel p-5 rounded-xl border border-[#252D37] hover:border-[#C7CDD5]/50 transition-all space-y-4 group">
                <div className="relative aspect-video w-full rounded-lg overflow-hidden border border-[#252D37] bg-[#030508]">
                  <img src={obs.image_url} alt={obs.id} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-[#030508]/90 border border-[#252D37] font-mono-tech text-[10px] text-[#D5DAE0]">
                    {obs.id}
                  </div>
                  <div className={`absolute top-2 right-2 px-2 py-0.5 rounded font-mono-tech text-[10px] font-bold ${
                    obs.priority === 'HIGH' ? 'bg-[#3A2B15]/90 text-[#D6A84F] border border-[#D6A84F]/40' : 'bg-[#151B23]/90 text-[#717985]'
                  }`}>
                    {obs.priority} PRIORITY
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between font-mono-tech text-xs text-[#717985]">
                    <span>RA: {obs.ra.toFixed(3)}°</span>
                    <span>DEC: {obs.dec.toFixed(3)}°</span>
                  </div>
                  <h4 className="text-base font-serif-display font-semibold text-[#F2F4F7]">
                    {obs.broad_morphology} Galaxy
                  </h4>
                  <p className="text-xs text-[#A8B0BA] font-sans-ui line-clamp-2">
                    {obs.explanation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 8. SECTION 05 — READY TO EXPLORE (LAUNCHPAD CTA)         */}
      {/* ========================================================= */}
      <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full z-20 border-t border-[#252D37]">
        <div className="glass-panel p-12 md:p-16 rounded-2xl border border-[#C7CDD5]/30 text-center space-y-8 relative overflow-hidden bg-gradient-to-b from-[#0D1219] via-[#070B11] to-[#030508]">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-[#8FAFC2]/08 blur-3xl rounded-full pointer-events-none" />
          
          <div className="space-y-4 max-w-2xl mx-auto relative z-10">
            <span className="font-mono-tech text-xs text-[#8FAFC2] tracking-widest uppercase block">
              READY TO EXPLORE?
            </span>
            <h2 className="text-4xl md:text-6xl font-serif-display font-bold text-[#F2F4F7] tracking-tight uppercase">
              Launch Into Mission Briefing
            </h2>
            <p className="text-base text-[#A8B0BA] font-sans-ui">
              Start with an astronomical observation, explore the archive, or see what ASTRA has prioritized for scientific review.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 relative z-10 pt-4">
            <button
              onClick={onExplore}
              className="px-8 py-4 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs sm:text-sm font-bold tracking-widest transition-all shadow-xl shadow-black/40 flex items-center gap-3 cursor-pointer"
            >
              START MISSION BRIEFING <ArrowRight className="w-4 h-4 text-[#070B11]" />
            </button>

            <button
              onClick={handleViewObs}
              className="px-8 py-4 rounded-lg glass-panel hover:bg-[#151B23] text-[#F2F4F7] font-mono-tech text-xs sm:text-sm font-semibold tracking-widest border border-[#C7CDD5]/30 hover:border-[#D5DAE0] transition-all flex items-center gap-3 cursor-pointer"
            >
              EXPLORE LIBRARY <Telescope className="w-4 h-4 text-[#8FAFC2]" />
            </button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="px-6 py-8 border-t border-[#252D37] bg-[#030508] text-center text-xs font-mono-tech text-[#717985] z-20 relative">
        <p>ASTRA — AI-Based Astronomical Observation Triage System | SIH 2026 Space-Tech Project</p>
      </footer>
    </div>
  );
};

export default LandingPage;
