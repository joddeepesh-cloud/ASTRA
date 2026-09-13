import React, { useState, useRef } from 'react';
import {
  UploadCloud, AlertTriangle, CheckCircle2, RefreshCw,
  Sparkles, Cpu, AlertCircle, ArrowRight
} from 'lucide-react';
import { triageImage } from '../services/api';
import type { TriageResponse, DomainValidationGate } from '../types/api';
import { ConfidenceBar } from './ConfidenceBar';
import { PriorityBadge } from './PriorityBadge';

type UploadState = 'idle' | 'validating' | 'analyzing' | 'success' | 'error';

interface UploadDropzoneProps {
  onInspectResult?: (result: TriageResponse, imageFile: File, previewUrl: string) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onInspectResult }) => {
  const [state, setState] = useState<UploadState>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);

  // Architecture placeholder for future domain validation model gate
  const domainGate: DomainValidationGate = {
    compatible: true,
    status: 'not_implemented',
    message: 'Imagery must represent astronomical observation cutouts (FITS, SDSS/HST JPEGs).'
  };

  const abortControllerRef = useRef<AbortController | null>(null);

  const resetUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState('idle');
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setErrorMessage('');
    setTriageResult(null);
  };

  const processFile = async (file: File) => {
    // Reset previous state
    setErrorMessage('');
    setTriageResult(null);

    // 1. Basic Client-Side Validation
    const fname = file.name.toLowerCase();
    const validExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    const hasValidExt = validExtensions.some((ext) => fname.endsWith(ext));
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    const hasValidType = validTypes.includes(file.type);

    if (!hasValidExt && !hasValidType) {
      setErrorMessage('Unsupported file format. Upload a valid JPEG, PNG, or WEBP image.');
      setState('error');
      return;
    }

    const maxBytes = 10 * 1024 * 1024; // 10 MB
    if (file.size > maxBytes) {
      setErrorMessage('File size exceeds the maximum upload limit of 10 MB.');
      setState('error');
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // 2. Transition State: VALIDATING
    setState('validating');
    await new Promise((resolve) => setTimeout(resolve, 300)); // Smooth UI transition

    // 3. Transition State: ANALYZING (Call Real FastAPI Backend)
    setState('analyzing');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const result = await triageImage(file, controller.signal);
      setTriageResult(result);
      setState('success');
    } catch (err: any) {
      setErrorMessage(err.message || "ASTRA's analysis service is currently unavailable. Live analysis cannot be performed.");
      setState('error');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="glass-panel p-6 md:p-8 rounded-xl border border-cyan-900/40 space-y-6 max-w-4xl mx-auto">
      {/* Title Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold font-mono text-white tracking-tight">
          ANALYZE AN OBSERVATION
        </h2>
        <p className="text-xs md:text-sm text-slate-400 font-sans max-w-xl mx-auto">
          Upload astronomical observation imagery (FITS cutouts, SDSS/HST JPEGs) for real-time morphology classification and scientific triage scoring.
        </p>
      </div>

      {/* Domain Input Warning Box */}
      <div className="bg-amber-950/40 border border-amber-500/30 p-3.5 rounded-lg flex items-start gap-3 text-xs text-amber-200">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1 font-sans">
          <span className="font-mono font-bold text-amber-300 uppercase block">
            ASTRONOMY DOMAIN INPUT REQUIREMENTS
          </span>
          <p className="text-amber-200/90 leading-relaxed">
            {domainGate.message} Non-astronomical imagery should not be submitted for morphological analysis.
          </p>
        </div>
      </div>

      {/* Main Dropzone & Analysis Container */}
      {state === 'idle' && (
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="border-2 border-dashed border-slate-800 bg-slate-950/60 hover:border-cyan-500/50 hover:bg-slate-900/40 rounded-xl p-8 text-center transition-all duration-300 flex flex-col items-center justify-center min-h-[260px]"
        >
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-full bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center mx-auto text-cyan-400 shadow-lg">
              <UploadCloud className="w-8 h-8 animate-pulse" />
            </div>
            <div className="space-y-1 font-sans">
              <p className="text-sm font-semibold text-slate-200">
                Drag and drop your astronomical image file here
              </p>
              <p className="text-xs text-slate-400">
                Supports JPEG, PNG, WEBP format up to 10 MB
              </p>
            </div>
            <div>
              <label className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold cursor-pointer transition-all inline-block shadow-md shadow-cyan-950/50">
                BROWSE FILES
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Validating State */}
      {state === 'validating' && (
        <div className="border border-slate-800 bg-slate-950/80 rounded-xl p-10 text-center space-y-4 min-h-[260px] flex flex-col items-center justify-center">
          <Sparkles className="w-10 h-10 text-amber-400 animate-bounce mx-auto" />
          <div className="space-y-1 font-mono">
            <p className="text-sm font-bold text-amber-300">STAGE 1: UNIVERSAL SEMANTIC CHECK...</p>
            <p className="text-xs text-slate-400">{selectedFile?.name}</p>
          </div>
        </div>
      )}

      {/* Analyzing State */}
      {state === 'analyzing' && (
        <div className="border border-cyan-900/60 bg-slate-950/90 rounded-xl p-10 text-center space-y-4 min-h-[260px] flex flex-col items-center justify-center">
          <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin mx-auto" />
          <div className="space-y-2 font-mono">
            <p className="text-sm font-bold text-cyan-300">STAGE 2: ASTRONOMICAL DOMAIN CHECK & TRIAGE...</p>
            <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>Semantic Gate $\rightarrow$ Domain Gate V2 $\rightarrow$ Galaxy Zoo Morphology</span>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {state === 'error' && (
        <div className="border border-rose-500/50 bg-rose-950/30 rounded-xl p-8 text-center space-y-4 min-h-[240px] flex flex-col items-center justify-center">
          <div className="w-14 h-14 rounded-full bg-rose-950/80 border border-rose-500/40 flex items-center justify-center mx-auto text-rose-400">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div className="space-y-2 font-mono max-w-md mx-auto">
            <span className="px-2.5 py-1 rounded bg-rose-900/60 text-rose-300 border border-rose-500/40 text-xs font-bold uppercase inline-block">
              ANALYSIS FAILED
            </span>
            <p className="text-xs text-rose-200/90 font-sans leading-relaxed">
              {errorMessage}
            </p>
          </div>
          <button
            onClick={resetUpload}
            className="px-4 py-2 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700 transition-all cursor-pointer"
          >
            TRY ANOTHER FILE
          </button>
        </div>
      )}

      {/* Success State: Display Domain Validation & Scientific Analysis Result */}
      {state === 'success' && triageResult && (
        <div className="space-y-6">
          {/* Domain COMPATIBLE View */}
          {triageResult.domain_validation?.decision === 'COMPATIBLE' && (
            <>
              <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/40 flex items-center justify-between">
                <div className="flex items-center gap-3 font-mono">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  <div>
                    <span className="text-xs text-emerald-400 font-bold uppercase block">
                      ASTRONOMICAL DOMAIN VERIFIED (TWO-STAGE CHECK PASSED)
                    </span>
                    <span className="text-xs text-slate-400">
                      Semantic Gate + Domain Gate V2 | Total Triage: {triageResult.total_triage_ms} ms
                    </span>
                  </div>
                </div>
                {triageResult.priority_level && <PriorityBadge priority={triageResult.priority_level} />}
              </div>

              {/* Result Main Display Grid */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                {/* Left: Image & Morphology Classification */}
                <div className="md:col-span-6 space-y-4">
                  {previewUrl && (
                    <div className="aspect-square w-full rounded-lg overflow-hidden bg-black border border-slate-800 relative">
                      <img src={previewUrl} alt="Uploaded observation" className="w-full h-full object-cover" />
                      <div className="absolute top-3 left-3 bg-slate-950/80 px-2.5 py-1 rounded text-xs font-mono text-cyan-300 border border-cyan-900/50 backdrop-blur-md">
                        LIVE UPLOAD ANALYSIS
                      </div>
                    </div>
                  )}

                  {triageResult.predicted_class && triageResult.class_confidence != null && triageResult.class_probabilities && (
                    <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-3">
                      <div className="flex justify-between items-center font-mono">
                        <span className="text-xs text-slate-400">PREDICTED MORPHOLOGY</span>
                        <span className="text-sm font-bold text-cyan-300 uppercase">{triageResult.predicted_class}</span>
                      </div>
                      <div className="flex justify-between items-center font-mono text-xs">
                        <span className="text-slate-400">CLASSIFICATION CONFIDENCE</span>
                        <span className="text-emerald-400 font-bold">{(triageResult.class_confidence * 100).toFixed(1)}%</span>
                      </div>

                      <div className="space-y-2 pt-2 border-t border-slate-800">
                        {Object.entries(triageResult.class_probabilities).map(([cls, prob]) => (
                          <ConfidenceBar
                            key={cls}
                            label={cls}
                            value={prob}
                            color={prob > 0.7 ? 'cyan' : prob > 0.2 ? 'emerald' : 'amber'}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right: Scientific Triage Scores & Attributes */}
                <div className="md:col-span-6 space-y-4">
                  {/* Triage Score Summary Box */}
                  {triageResult.experimental_triage_score != null && (
                    <div className="bg-slate-900/60 p-4 rounded-lg border border-cyan-900/40 space-y-3">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                        <span className="text-xs font-mono text-slate-400 uppercase">EXPERIMENTAL TRIAGE SCORE</span>
                        <span className="text-2xl font-mono font-bold text-cyan-300">{triageResult.experimental_triage_score.toFixed(2)}</span>
                      </div>

                      <div className="space-y-2.5 pt-1">
                        {triageResult.novelty_score != null && (
                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1">
                              <span className="text-slate-400">Novelty Score (Nearest Centroid)</span>
                              <span className="text-amber-400">{triageResult.novelty_score.toFixed(2)}</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                              <div className="bg-amber-400 h-2 rounded-full" style={{ width: `${triageResult.novelty_score * 100}%` }} />
                            </div>
                          </div>
                        )}

                        {triageResult.uncertainty_score != null && (
                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1">
                              <span className="text-slate-400">Classification Uncertainty</span>
                              <span className="text-rose-400">{triageResult.uncertainty_score.toFixed(2)}</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                              <div className="bg-rose-400 h-2 rounded-full" style={{ width: `${triageResult.uncertainty_score * 100}%` }} />
                            </div>
                          </div>
                        )}

                        {triageResult.oddity_score != null && (
                          <div>
                            <div className="flex justify-between text-xs font-mono mb-1">
                              <span className="text-slate-400">Scientific Oddity Attribute (p_odd)</span>
                              <span className="text-indigo-400">{triageResult.oddity_score.toFixed(2)}</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                              <div className="bg-indigo-400 h-2 rounded-full" style={{ width: `${triageResult.oddity_score * 100}%` }} />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Deterministic Scientific Explanation */}
                  <div className="bg-slate-950/80 p-4 rounded-lg border border-slate-800 space-y-2">
                    <span className="text-xs font-mono text-cyan-400 font-bold block">DETERMINISTIC TRIAGE EXPLANATION</span>
                    <p className="text-xs text-slate-300 font-sans leading-relaxed">
                      {triageResult.explanation}
                    </p>
                  </div>

                  {/* Scientific Disclaimer */}
                  <div className="p-3 bg-amber-950/30 rounded border border-amber-500/20 text-[11px] font-sans text-amber-200/90 leading-relaxed">
                    {triageResult.score_interpretation}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={resetUpload}
                      className="flex-1 py-2.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700 transition-all cursor-pointer"
                    >
                      UPLOAD ANOTHER IMAGE
                    </button>

                    {onInspectResult && selectedFile && previewUrl && (
                      <button
                        onClick={() => onInspectResult(triageResult, selectedFile, previewUrl)}
                        className="flex-1 py-2.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-md"
                      >
                        INSPECT DETAILED VIEW <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Domain INCOMPATIBLE View */}
          {triageResult.domain_validation?.decision === 'INCOMPATIBLE' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/50 flex items-center gap-3 font-mono">
                <AlertCircle className="w-6 h-6 text-rose-400 shrink-0" />
                <div>
                  <span className="text-xs text-rose-300 font-bold uppercase block">
                    DOMAIN REJECTED — INCOMPATIBLE
                  </span>
                  <span className="text-xs text-slate-400">
                    ASTRA could not validate this image as astronomical observation data. No astronomical classification was performed.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                <div className="md:col-span-5">
                  {previewUrl && (
                    <div className="aspect-square w-full rounded-lg overflow-hidden bg-black border border-rose-900/40 relative">
                      <img src={previewUrl} alt="Rejected observation" className="w-full h-full object-cover opacity-80" />
                      <div className="absolute top-3 left-3 bg-rose-950/90 px-2.5 py-1 rounded text-xs font-mono text-rose-300 border border-rose-500/40 backdrop-blur-md">
                        REJECTED UPLOAD
                      </div>
                    </div>
                  )}
                </div>

                <div className="md:col-span-7 space-y-4 flex flex-col justify-between">
                  <div className="bg-slate-950/90 p-5 rounded-xl border border-rose-900/40 space-y-3 font-sans">
                    <h3 className="text-sm font-mono font-bold text-rose-300 uppercase tracking-wide flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                      DOMAIN REJECTION NOTICE
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      ASTRA could not validate this image as astronomical observation data. No astronomical classification was performed.
                    </p>
                    {triageResult.domain_validation.semantic_reason && (
                      <div className="p-3 bg-rose-950/30 rounded border border-rose-500/20 text-xs font-mono text-rose-200">
                        Reason: {triageResult.domain_validation.semantic_reason}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={resetUpload}
                    className="w-full py-3 rounded bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs font-bold border border-slate-700 transition-all cursor-pointer"
                  >
                    TRY ANOTHER IMAGE
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Domain UNCERTAIN View */}
          {triageResult.domain_validation?.decision === 'UNCERTAIN' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-amber-950/60 border border-amber-500/50 flex items-center gap-3 font-mono">
                <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
                <div>
                  <span className="text-xs text-amber-300 font-bold uppercase block">
                    DOMAIN VALIDATION UNCERTAIN
                  </span>
                  <span className="text-xs text-slate-400">
                    ASTRA could not confidently validate this image as astronomical observation data. Analysis was stopped to avoid an unsupported classification.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                <div className="md:col-span-5">
                  {previewUrl && (
                    <div className="aspect-square w-full rounded-lg overflow-hidden bg-black border border-amber-900/40 relative">
                      <img src={previewUrl} alt="Uncertain observation" className="w-full h-full object-cover opacity-90" />
                      <div className="absolute top-3 left-3 bg-amber-950/90 px-2.5 py-1 rounded text-xs font-mono text-amber-300 border border-amber-500/40 backdrop-blur-md">
                        UNCERTAIN DOMAIN
                      </div>
                    </div>
                  )}
                </div>

                <div className="md:col-span-7 space-y-4 flex flex-col justify-between">
                  <div className="bg-slate-950/90 p-5 rounded-xl border border-amber-900/40 space-y-3 font-sans">
                    <h3 className="text-sm font-mono font-bold text-amber-300 uppercase tracking-wide flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      SAFE UNCERTAINTY NOTICE
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">
                      ASTRA could not confidently validate this image as astronomical observation data. Analysis was stopped to avoid an unsupported classification.
                    </p>
                    <div className="p-3 bg-amber-950/30 rounded border border-amber-500/20 text-xs font-mono text-amber-200">
                      Safety Rule Enforced: No confident Galaxy Zoo morphology classification was performed for ambiguous inputs.
                    </div>
                  </div>

                  <button
                    onClick={resetUpload}
                    className="w-full py-3 rounded bg-slate-900 hover:bg-slate-800 text-slate-200 font-mono text-xs font-bold border border-slate-700 transition-all cursor-pointer"
                  >
                    TRY ANOTHER IMAGE
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
