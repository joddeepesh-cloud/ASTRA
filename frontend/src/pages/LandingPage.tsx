import React, { useState, useRef, useEffect } from 'react';
import { MOCK_TELEMETRY } from '../data/mockData';
import { ScientificPipeline } from '../components/ScientificPipeline';
import { Rocket, ArrowRight, Telescope, Sparkles, ChevronDown } from 'lucide-react';

type PlanetKey = 'earth' | 'venus' | 'mars';

interface PlanetInfo {
  id: PlanetKey;
  name: string;
  video: string;
  poster: string;
  cutout: string;
  eyebrow: string;
  headline: string;
  lede: string;
}

const PLANETS: Record<PlanetKey, PlanetInfo> = {
  earth: {
    id: 'earth',
    name: 'EARTH',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_3ffb4889-c520-432d-8458-038009eb40df.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_508c64b8-a31e-4290-bdfc-1187df70e0a6.png',
    cutout: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202005_3346cc4d-ec3b-44ab-825c-b18e49f5021a.png',
    eyebrow: 'ASTRONOMICAL OBSERVATION TRIAGE',
    headline: 'EARTH',
    lede: 'ASTRA monitors orbital telemetries and Earth observations, prioritizing high-value anomalies for scientific review under bandwidth constraints.'
  },
  venus: {
    id: 'venus',
    name: 'VENUS',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_b211cd74-013b-4dd3-bfd0-64491d8696fa.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_cf55d1d8-7b59-4a64-80da-d72052ae974e.png',
    cutout: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202012_640b239a-d08a-4200-adb2-741bbe129ac8.png',
    eyebrow: 'ATMOSPHERIC OBSERVATION TRIAGE',
    headline: 'VENUS',
    lede: 'ASTRA triages extreme cloud-covered planetary observations, identifying statistically unusual atmospheric data under tight downlink budgets.'
  },
  mars: {
    id: 'mars',
    name: 'MARS',
    video: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202422_51eae59a-2459-4c84-907c-cc5edfe5fea7.mp4',
    poster: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202133_0ba6de7c-285d-43dc-b7ab-8c54c73707cb.png',
    cutout: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260827_202018_3d559490-f613-4ed7-a3bb-3b7e9fc90fb8.png',
    eyebrow: 'SURFACE & ORBITAL ANOMALY TRIAGE',
    headline: 'MARS',
    lede: 'ASTRA analyzes surface and orbital data across Martian geology, filtering high-confidence priority observations for deep scientific investigation.'
  }
};

const PLANET_ORDER: PlanetKey[] = ['earth', 'venus', 'mars'];

interface LandingPageProps {
  onExplore: () => void;
  onViewObservations?: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onExplore, onViewObservations }) => {
  const [featured, setFeatured] = useState<PlanetKey>('earth');
  const [loadedVideos, setLoadedVideos] = useState<Record<PlanetKey, boolean>>({
    earth: true,
    venus: false,
    mars: false
  });

  const pipelineRef = useRef<HTMLDivElement>(null);

  // Compute side slot planet keys
  const rest = PLANET_ORDER.filter(p => p !== featured);
  const leftKey = rest[0];
  const rightKey = rest[1];

  const warmVideo = (key: PlanetKey) => {
    if (!loadedVideos[key]) {
      setLoadedVideos(prev => ({ ...prev, [key]: true }));
    }
  };

  const showPlanet = (nextKey: PlanetKey) => {
    warmVideo(nextKey);
    setFeatured(nextKey);
  };

  useEffect(() => {
    // Warm remaining videos on idle after initial paint
    const timer = setTimeout(() => {
      setLoadedVideos({ earth: true, venus: true, mars: true });
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const scrollToPipeline = () => {
    pipelineRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleViewObs = () => {
    if (onViewObservations) {
      onViewObservations();
    } else {
      onExplore();
    }
  };

  return (
    <div className="min-h-screen bg-[#03060f] text-slate-100 flex flex-col relative overflow-x-hidden font-sans-ui selection:bg-[#79DCE8]/30">
      {/* ========================================================= */}
      {/* 1. CINEMATIC FULL VIEWPORT PLANETARY BACKGROUND SYSTEM   */}
      {/* ========================================================= */}
      <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none z-0">
        {/* Background Poster Image Fallbacks for each planet */}
        {PLANET_ORDER.map(key => (
          <img
            key={`poster-${key}`}
            src={PLANETS[key].poster}
            alt={`${PLANETS[key].name} Poster Background`}
            className={`absolute inset-0 w-full h-full object-cover object-center pointer-events-none transition-opacity duration-700 ${
              featured === key ? 'opacity-80 z-10' : 'opacity-0 z-0'
            }`}
          />
        ))}

        {/* 3 x Full Viewport Background Videos with Opacity Crossfade */}
        {PLANET_ORDER.map(key => (
          <video
            key={`video-${key}`}
            autoPlay
            muted
            loop
            playsInline
            preload={key === 'earth' ? 'auto' : 'none'}
            poster={PLANETS[key].poster}
            src={loadedVideos[key] ? PLANETS[key].video : undefined}
            className={`absolute inset-0 w-full h-full object-cover object-center pointer-events-none transition-opacity duration-700 ${
              featured === key ? 'opacity-85 z-20' : 'opacity-0 z-0'
            }`}
          />
        ))}

        {/* Atmospheric Dark Overlay for Contrast & Text Readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#03060f]/40 via-[#03060f]/60 to-[#03060f] pointer-events-none z-30" />

        {/* Star Grid & Grid Scanline Overlays */}
        <div className="absolute inset-0 star-grid opacity-30 pointer-events-none z-30" />
        <div className="absolute inset-0 scanline-overlay opacity-20 pointer-events-none z-30" />
      </div>

      {/* Hero Ambient Radial Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-[#79DCE8]/10 blur-[140px] pointer-events-none rounded-full z-0 animate-hero-fade" />

      {/* ========================================================= */}
      {/* 2. FIRST VIEWPORT HERO SECTION (Full 100vh / 100svh)       */}
      {/* ========================================================= */}
      <section className="relative min-h-screen h-[100svh] w-full flex flex-col justify-between z-20 overflow-hidden">
        
        {/* TOP NAVIGATION BAR */}
        <header className="px-6 md:px-12 py-6 max-w-7xl mx-auto w-full flex items-center justify-between z-30 relative animate-hero-fade">
          {/* Brand Wordmark */}
          <div className="flex items-center gap-3.5 cursor-pointer" onClick={onExplore}>
            <div className="w-10 h-10 rounded-xl bg-slate-900/90 border border-[#79DCE8]/40 flex items-center justify-center text-[#79DCE8] shadow-lg shadow-[#79DCE8]/10">
              <Rocket className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-bold font-mono-tech text-white tracking-widest block leading-none">
                ASTRA
              </span>
              <span className="text-[9px] font-mono-tech text-slate-400 tracking-wider uppercase mt-0.5 block">
                ASTRONOMICAL TRIAGE & SCIENTIFIC REVIEW ASSISTANT
              </span>
            </div>
          </div>

          {/* Center Nav Links (Desktop) */}
          <nav className="hidden md:flex items-center gap-6 font-mono-tech text-xs tracking-wider text-slate-300">
            <button onClick={onExplore} className="hover:text-[#79DCE8] transition-colors cursor-pointer">
              MISSION
            </button>
            <button onClick={handleViewObs} className="hover:text-[#79DCE8] transition-colors cursor-pointer">
              OBSERVATIONS
            </button>
            <button onClick={onExplore} className="hover:text-[#79DCE8] transition-colors cursor-pointer flex items-center gap-1">
              ANOMALIES <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
            </button>
            <button onClick={handleViewObs} className="hover:text-[#79DCE8] transition-colors cursor-pointer">
              LIBRARY
            </button>
            <button onClick={onExplore} className="hover:text-[#79DCE8] transition-colors cursor-pointer">
              COPILOT
            </button>
          </nav>

          {/* Right Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={onExplore}
              className="px-5 py-2.5 rounded-lg bg-[#79DCE8] hover:bg-cyan-300 text-slate-950 font-mono-tech text-xs font-bold tracking-wider transition-all shadow-lg shadow-[#79DCE8]/20 hover:shadow-[#79DCE8]/40 flex items-center gap-2 cursor-pointer"
            >
              ENTER MISSION CONTROL <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* HERO CONTENT & INTERACTIVE PLANET SWITCHER SLOTS */}
        <div className="flex-1 max-w-6xl mx-auto px-6 w-full flex items-center justify-between relative z-20 my-auto">

          {/* ========================================================= */}
          {/* LEFT PLANET SWITCHER SLOT BUTTON                          */}
          {/* ========================================================= */}
          <button
            type="button"
            onClick={() => showPlanet(leftKey)}
            onMouseEnter={() => warmVideo(leftKey)}
            onFocus={() => warmVideo(leftKey)}
            aria-label={`Show ${PLANETS[leftKey].name}`}
            className="group relative flex flex-col items-center cursor-pointer pointer-events-auto transition-transform duration-300 hover:scale-105 select-none"
          >
            <div className="w-24 sm:w-36 md:w-48 lg:w-60 aspect-square rounded-full relative overflow-hidden shadow-[0_0_60px_rgba(121,220,232,0.2)] border border-[#79DCE8]/30 glass-panel">
              {PLANET_ORDER.map(key => (
                <img
                  key={`left-cutout-${key}`}
                  src={PLANETS[key].cutout}
                  alt={`${PLANETS[key].name} Cutout`}
                  className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
                    leftKey === key ? 'opacity-100 block' : 'opacity-0 hidden'
                  }`}
                />
              ))}
              <div className="absolute inset-0 border-r-2 border-[#79DCE8]/40 rounded-full pointer-events-none" />
              {/* HUD Target Overlay */}
              <div className="absolute bottom-2 right-2 hidden md:block font-mono-tech text-[9px] text-[#79DCE8] bg-[#03060f]/80 px-2 py-1 rounded border border-[#79DCE8]/30">
                {PLANETS[leftKey].name}
              </div>
            </div>
            <span className="mt-3 font-serif-display text-xs sm:text-sm font-semibold tracking-widest text-slate-300 group-hover:text-[#79DCE8] transition-colors uppercase">
              {PLANETS[leftKey].name}
            </span>
          </button>

          {/* ========================================================= */}
          {/* CENTER HERO FOREGROUND CONTENT                            */}
          {/* ========================================================= */}
          <div className="space-y-6 max-w-2xl text-center flex flex-col items-center mx-4">
            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#081226]/80 border border-[#79DCE8]/30 text-[#79DCE8] text-xs font-mono-tech tracking-widest uppercase animate-reveal-up delay-100">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              <span>ASTRONOMICAL OBSERVATION TRIAGE</span>
            </div>

            {/* Main Large Title */}
            <div className="space-y-2 animate-reveal-up delay-200">
              <h1 className="text-5xl sm:text-7xl md:text-8xl lg:text-9xl font-serif-display font-bold text-white tracking-tight leading-none uppercase">
                <span className="bg-gradient-to-b from-white via-slate-100 to-[#79DCE8] bg-clip-text text-transparent">
                  ASTRA
                </span>
              </h1>
              {/* Cyan Accent Rule */}
              <div className="h-[3px] bg-[#79DCE8] w-24 sm:w-36 md:w-48 mx-auto mt-4 rounded-full shadow-[0_0_12px_#79DCE8] animate-rule-expand" />
            </div>

            {/* Supporting Lede Copy */}
            <p className="text-sm sm:text-base md:text-lg text-slate-200 font-sans-ui font-normal leading-relaxed max-w-xl pt-1 animate-reveal-up delay-300">
              ASTRA is an AI-powered astronomical observation triage system that identifies unusual observations and prioritizes them for scientific review.
            </p>

            {/* Primary & Secondary Call to Actions */}
            <div className="pt-4 flex flex-wrap items-center justify-center gap-4 animate-reveal-up delay-400">
              <button
                onClick={onExplore}
                className="px-8 py-4 rounded-xl bg-white hover:bg-cyan-50 text-slate-950 font-mono-tech text-xs sm:text-sm font-bold tracking-wider transition-all shadow-2xl shadow-white/10 hover:shadow-cyan-400/30 flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5"
              >
                EXPLORE THE MISSION <ArrowRight className="w-4 h-4 text-slate-950" />
              </button>

              <button
                onClick={scrollToPipeline}
                className="px-8 py-4 rounded-xl glass-panel hover:bg-slate-900/90 text-slate-200 font-mono-tech text-xs sm:text-sm font-semibold tracking-wider transition-all flex items-center gap-2 border border-[#79DCE8]/30 hover:border-[#79DCE8]/60 cursor-pointer transform hover:-translate-y-0.5"
              >
                EXPLAIN THE MISSION <Telescope className="w-4 h-4 text-[#79DCE8]" />
              </button>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT PLANET SWITCHER SLOT BUTTON                         */}
          {/* ========================================================= */}
          <button
            type="button"
            onClick={() => showPlanet(rightKey)}
            onMouseEnter={() => warmVideo(rightKey)}
            onFocus={() => warmVideo(rightKey)}
            aria-label={`Show ${PLANETS[rightKey].name}`}
            className="group relative flex flex-col items-center cursor-pointer pointer-events-auto transition-transform duration-300 hover:scale-105 select-none"
          >
            <div className="w-24 sm:w-36 md:w-48 lg:w-60 aspect-square rounded-full relative overflow-hidden shadow-[0_0_60px_rgba(121,220,232,0.2)] border border-[#79DCE8]/30 glass-panel">
              {PLANET_ORDER.map(key => (
                <img
                  key={`right-cutout-${key}`}
                  src={PLANETS[key].cutout}
                  alt={`${PLANETS[key].name} Cutout`}
                  className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
                    rightKey === key ? 'opacity-100 block' : 'opacity-0 hidden'
                  }`}
                />
              ))}
              <div className="absolute inset-0 border-l-2 border-[#79DCE8]/40 rounded-full pointer-events-none" />
              {/* HUD Target Overlay */}
              <div className="absolute top-2 left-2 hidden md:block font-mono-tech text-[9px] text-[#79DCE8] bg-[#03060f]/80 px-2 py-1 rounded border border-[#79DCE8]/30">
                {PLANETS[rightKey].name}
              </div>
            </div>
            <span className="mt-3 font-serif-display text-xs sm:text-sm font-semibold tracking-widest text-slate-300 group-hover:text-[#79DCE8] transition-colors uppercase">
              {PLANETS[rightKey].name}
            </span>
          </button>
        </div>

        {/* BOTTOM TELEMETRY PREVIEW & SCROLL INDICATOR */}
        <div className="w-full px-6 pb-6 max-w-6xl mx-auto flex flex-col items-center gap-4 z-20 relative animate-reveal-up delay-500">
          {/* Mission Telemetry HUD Bar */}
          <div className="w-full grid grid-cols-2 md:grid-cols-4 gap-2 font-mono-tech">
            <div className="glass-panel p-2.5 rounded-lg text-left border border-slate-800">
              <span className="text-[9px] text-slate-400 block uppercase">OBSERVATIONS RECEIVED</span>
              <span className="text-base font-bold text-white">{MOCK_TELEMETRY.observations_received.toLocaleString()}</span>
            </div>
            <div className="glass-panel p-2.5 rounded-lg text-left border border-slate-800">
              <span className="text-[9px] text-slate-400 block uppercase">ONBOARD PROCESSED</span>
              <span className="text-base font-bold text-emerald-400">{MOCK_TELEMETRY.onboard_processed.toLocaleString()}</span>
            </div>
            <div className="glass-panel p-2.5 rounded-lg text-left border border-slate-800">
              <span className="text-[9px] text-slate-400 block uppercase">ANOMALIES FLAGGED</span>
              <span className="text-base font-bold text-rose-400">{MOCK_TELEMETRY.anomalies_flagged}</span>
            </div>
            <div className="glass-panel p-2.5 rounded-lg text-left border border-slate-800">
              <span className="text-[9px] text-slate-400 block uppercase">DOWNLINK SAVED</span>
              <span className="text-base font-bold text-[#79DCE8]">{MOCK_TELEMETRY.downlink_saved_percent}%</span>
            </div>
          </div>

          {/* Smooth Scroll Button */}
          <button
            type="button"
            onClick={scrollToPipeline}
            aria-label="Scroll to how ASTRA works"
            className="flex items-center gap-2 cursor-pointer opacity-75 hover:opacity-100 transition-opacity font-mono-tech text-[10px] text-slate-400 uppercase tracking-widest"
          >
            <span>HOW ASTRA WORKS</span>
            <ChevronDown className="w-4 h-4 text-[#79DCE8] animate-bounce" />
          </button>
        </div>
      </section>

      {/* ========================================================= */}
      {/* 3. HOW ASTRA WORKS PIPELINE SECTION                       */}
      {/* ========================================================= */}
      <section ref={pipelineRef} className="max-w-6xl mx-auto px-6 py-20 z-20 relative border-t border-slate-900">
        <ScientificPipeline />
      </section>

      {/* FOOTER */}
      <footer className="px-6 py-6 border-t border-slate-900 bg-[#02040a] text-center text-xs font-mono-tech text-slate-500 z-20 relative">
        <p>ASTRA — AI-Based Astronomical Observation Triage System | SIH 2026 Space-Tech Project</p>
      </footer>
    </div>
  );
};

