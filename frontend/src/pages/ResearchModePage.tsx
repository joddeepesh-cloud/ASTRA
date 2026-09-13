import React from 'react';
import { UploadDropzone } from '../components/UploadDropzone';
import { ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import type { TriageResponse } from '../types/api';

interface ResearchModePageProps {
  onInspectResult?: (result: TriageResponse, imageFile: File, previewUrl: string) => void;
}

export const ResearchModePage: React.FC<ResearchModePageProps> = ({ onInspectResult }) => {
  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="border-b border-slate-800 pb-6">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold font-mono text-white tracking-wider">
            RESEARCH & EXPERIMENTAL UPLOAD MODE
          </h1>
          <span className="text-xs font-mono bg-cyan-950/40 text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded">
            ASTRA LABS
          </span>
        </div>
        <p className="text-xs text-slate-400 font-sans mt-1 max-w-2xl">
          Test custom observation cutouts against ASTRA's onboard domain validator, morphology feature extractor, and statistical OOD anomaly pipeline.
        </p>
      </div>

      {/* Main Upload Dropzone Area */}
      <UploadDropzone onInspectResult={onInspectResult} />

      {/* Technical Specifications */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold">
            <Cpu className="w-4 h-4" /> ONBOARD FEATURE MANIFOLD
          </div>
          <p className="text-xs text-slate-400 font-sans leading-relaxed">
            Extracts deep embedding vectors using a lightweight TIMM vision backbone trained on Galaxy Zoo 2 morphology.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-mono text-xs font-bold">
            <ShieldAlert className="w-4 h-4" /> DOMAIN VALIDATOR FILTER
          </div>
          <p className="text-xs text-slate-400 font-sans leading-relaxed">
            Non-astronomical imagery (people, cars, memes, landscapes) is explicitly identified and rejected before inference.
          </p>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold">
            <Sparkles className="w-4 h-4" /> ANOMALY SCORING ENGINE
          </div>
          <p className="text-xs text-slate-400 font-sans leading-relaxed">
            Calculates Mahalanobis and Isolation Forest distance metrics against learned astronomical distributions.
          </p>
        </div>
      </div>
    </div>
  );
};
