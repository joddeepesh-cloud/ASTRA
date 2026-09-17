import React, { useState, useRef } from 'react';
import {
  UploadCloud, AlertTriangle, CheckCircle2, RefreshCw,
  AlertCircle, ArrowRight, ShieldCheck, Telescope, Rocket
} from 'lucide-react';
import { triageImage } from '../services/api';
import type { TriageResponse, DomainValidationGate } from '../types/api';
import type { Observation } from '../types';
import { ConfidenceBar } from './ConfidenceBar';
import { PriorityBadge } from './PriorityBadge';
import { TriageExplanation } from './TriageExplanation';
import { ObservationLibraryPicker } from './ObservationLibraryPicker';
import { recordAnalysis } from '../services/analysisHistory';
import { saveImageBlob } from '../services/imageStore';

type UploadState = 'idle' | 'validating' | 'analyzing' | 'success' | 'error';
type InputSource = 'upload' | 'library';

interface UploadDropzoneProps {
  onInspectResult?: (result: TriageResponse, imageFile: File, previewUrl: string) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onInspectResult }) => {
  const [state, setState] = useState<UploadState>('idle');
  const [inputSource, setInputSource] = useState<InputSource>('upload');
  const [selectedLibraryObs, setSelectedLibraryObs] = useState<Observation | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);

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
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setErrorMessage('');
    setTriageResult(null);
    setSelectedLibraryObs(null);
  };

  const handleSwitchInputSource = (source: InputSource) => {
    if (state !== 'idle') {
      resetUpload();
    }
    setInputSource(source);
  };

  const processFile = async (file: File) => {
    setErrorMessage('');
    setTriageResult(null);

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

    setState('validating');
    await new Promise((resolve) => setTimeout(resolve, 300));

    setState('analyzing');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const result = await triageImage(file, controller.signal);
      setTriageResult(result);
      setState('success');

      // Save original uploaded image Blob to IndexedDB for persistent history reconstruction
      const obsId = result.observation_id || `OBS-${Date.now().toString(36).toUpperCase()}`;
      const imageKey = `IMG-${obsId}`;
      await saveImageBlob(imageKey, file);

      // Record in Session Analysis History
      await recordAnalysis(result, file.name, obsId, 'RESEARCH_UPLOAD', imageKey);
    } catch (err: any) {
      setErrorMessage(err.message || "ASTRA's analysis service is currently unavailable. Live analysis cannot be performed.");
      setState('error');
    }
  };

  const runLibraryAnalysis = async (obs: Observation) => {
    setErrorMessage('');
    setTriageResult(null);
    setState('validating');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // Fetch genuine library asset image as Blob
      const imgRes = await fetch(obs.image_url);
      if (!imgRes.ok) {
        throw new Error(`Unable to load library observation image asset (${imgRes.statusText}).`);
      }

      const blob = await imgRes.blob();
      const filename = `${obs.id}.jpg`;
      const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });

      setSelectedFile(file);
      setPreviewUrl(obs.image_url);

      setState('analyzing');

      // Submit to real ASTRA FastAPI /triage backend
      const result = await triageImage(file, controller.signal, obs.object_type || 'GALAXY');
      setTriageResult(result);
      setState('success');

      // Record in Session Analysis History
      await recordAnalysis(result, filename, obs.id, 'LIBRARY', obs.image_url);
    } catch (err: any) {
      setErrorMessage(err.message || "ASTRA analysis could not be completed for the selected library observation.");
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
    <div className="glass-panel p-6 md:p-8 rounded-xl border border-[#C7CDD5]/30 space-y-6 max-w-4xl mx-auto selection:bg-[#C7CDD5]/30 font-sans-ui">
      {/* Title Header & Input Source Switcher */}
      <div className="text-center space-y-4">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold font-serif-display text-[#F2F4F7] tracking-tight uppercase">
            Analyze An Observation
          </h2>
          <p className="text-xs md:text-sm text-[#A8B0BA] font-sans-ui max-w-xl mx-auto">
            Choose an input source below to submit an astronomical observation cutout through ASTRA's real ML triage pipeline.
          </p>
        </div>

        {/* Input Source Toggle */}
        <div className="flex items-center justify-center gap-2 p-1.5 bg-[#0D1219] rounded-xl border border-[#252D37] max-w-md mx-auto">
          <button
            onClick={() => handleSwitchInputSource('upload')}
            className={`flex-1 py-2 px-4 rounded-lg font-mono-tech text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              inputSource === 'upload'
                ? 'bg-[#D5DAE0] text-[#070B11] shadow-md'
                : 'text-[#A8B0BA] hover:text-[#F2F4F7]'
            }`}
          >
            <UploadCloud className="w-4 h-4" /> UPLOAD IMAGE
          </button>
          <button
            onClick={() => handleSwitchInputSource('library')}
            className={`flex-1 py-2 px-4 rounded-lg font-mono-tech text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
              inputSource === 'library'
                ? 'bg-[#D5DAE0] text-[#070B11] shadow-md'
                : 'text-[#A8B0BA] hover:text-[#F2F4F7]'
            }`}
          >
            <Telescope className="w-4 h-4" /> OBSERVATION LIBRARY
          </button>
        </div>
      </div>

      {/* Domain Input Warning Box */}
      <div className="bg-[#3A2B15]/40 border border-[#D6A84F]/30 p-3.5 rounded-lg flex items-start gap-3 text-xs text-[#D6A84F]">
        <AlertTriangle className="w-5 h-5 text-[#D6A84F] shrink-0 mt-0.5" />
        <div className="space-y-1 font-sans-ui">
          <span className="font-mono-tech font-bold text-[#D6A84F] uppercase block">
            ASTRONOMY DOMAIN INPUT REQUIREMENTS
          </span>
          <p className="text-[#D6A84F]/90 leading-relaxed">
            {domainGate.message} Non-astronomical imagery should not be submitted for morphological analysis.
          </p>
        </div>
      </div>

      {/* Main Container State: IDLE */}
      {state === 'idle' && (
        <>
          {inputSource === 'upload' ? (
            /* Upload File Dropzone */
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-[#252D37] bg-[#070B11]/60 hover:border-[#C7CDD5]/50 hover:bg-[#0D1219]/40 rounded-xl p-8 text-center transition-all duration-300 flex flex-col items-center justify-center min-h-[260px]"
            >
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-full bg-[#151B23] border border-[#C7CDD5]/30 flex items-center justify-center mx-auto text-[#D5DAE0] shadow-lg">
                  <UploadCloud className="w-8 h-8 text-[#8FAFC2]" />
                </div>
                <div className="space-y-1 font-sans-ui">
                  <p className="text-sm font-semibold text-[#F2F4F7]">
                    Drag and drop your astronomical image file here
                  </p>
                  <p className="text-xs text-[#717985]">
                    Supports JPEG, PNG, WEBP format up to 10 MB
                  </p>
                </div>
                <div>
                  <label className="px-5 py-2.5 rounded-lg bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold cursor-pointer transition-all inline-block shadow-md shadow-black/40">
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
          ) : (
            /* Observation Library Picker or Loaded Target View */
            <div>
              {!selectedLibraryObs ? (
                <ObservationLibraryPicker
                  onSelectObservation={(obs) => setSelectedLibraryObs(obs)}
                  selectedObservationId={selectedLibraryObs ? (selectedLibraryObs as Observation).id : null}
                />
              ) : (
                /* Selected Curated Observation Pre-Analysis Card */
                <div className="glass-panel p-6 rounded-xl border border-[#8FAFC2]/40 bg-[#070B11]/90 space-y-6">
                  <div className="flex items-center justify-between border-b border-[#252D37] pb-3">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 rounded bg-[#15232E] text-[#8FAFC2] border border-[#8FAFC2]/40 font-mono-tech text-xs font-bold">
                        CURATED LIBRARY OBSERVATION
                      </span>
                      <span className="text-xs text-[#717985] font-mono-tech">
                        Galaxy Zoo 2 / SDSS DR7
                      </span>
                    </div>

                    <button
                      onClick={() => setSelectedLibraryObs(null)}
                      className="text-xs font-mono-tech text-[#8FAFC2] hover:text-white underline cursor-pointer"
                    >
                      Change Target
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                    {/* Left: Image Preview */}
                    <div className="md:col-span-5">
                      <div className="aspect-square w-full rounded-lg overflow-hidden bg-black border border-[#252D37] relative">
                        <img
                          src={selectedLibraryObs.image_url}
                          alt={selectedLibraryObs.id}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-[#030508]/90 font-mono-tech text-[10px] text-[#D5DAE0] border border-[#252D37]">
                          {selectedLibraryObs.id}
                        </div>
                      </div>
                    </div>

                    {/* Right: Genuine Source Metadata */}
                    <div className="md:col-span-7 space-y-4 flex flex-col justify-between font-mono-tech text-xs">
                      <div className="space-y-2.5 bg-[#0D1219] p-4 rounded-lg border border-[#252D37]">
                        <span className="text-xs font-bold text-[#D5DAE0] block uppercase border-b border-[#252D37] pb-1">
                          SOURCE CATALOG METADATA
                        </span>

                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                          <div>
                            <span className="text-[#717985] block">Target ID:</span>
                            <span className="text-white font-bold">{selectedLibraryObs.id}</span>
                          </div>
                          <div>
                            <span className="text-[#717985] block">SDSS DR7 ObjID:</span>
                            <span className="text-[#D5DAE0]">{selectedLibraryObs.dr7objid}</span>
                          </div>
                          <div>
                            <span className="text-[#717985] block">Right Ascension (RA):</span>
                            <span className="text-[#8FAFC2]">{selectedLibraryObs.ra.toFixed(4)}°</span>
                          </div>
                          <div>
                            <span className="text-[#717985] block">Declination (DEC):</span>
                            <span className="text-[#8FAFC2]">{selectedLibraryObs.dec.toFixed(4)}°</span>
                          </div>
                          <div>
                            <span className="text-[#717985] block">GZ2 Taxonomy:</span>
                            <span className="text-[#D6A84F] font-bold">{selectedLibraryObs.gz2class}</span>
                          </div>
                          <div>
                            <span className="text-[#717985] block">Broad Category:</span>
                            <span className="text-[#5FC7A1]">{selectedLibraryObs.broad_morphology}</span>
                          </div>
                        </div>
                      </div>

                      {/* Source Metadata Notice */}
                      <div className="p-3 bg-[#15232E]/60 rounded border border-[#8FAFC2]/30 text-[11px] text-[#8FAFC2] font-sans-ui leading-relaxed">
                        Notice: Source catalog information displayed above. This observation cutout has not yet been processed by ASTRA's real ML inference pipeline.
                      </div>

                      {/* Actions */}
                      <div className="flex gap-3 pt-1">
                        <button
                          onClick={() => setSelectedLibraryObs(null)}
                          className="py-3 px-4 rounded bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] font-mono-tech text-xs border border-[#252D37] transition-all cursor-pointer"
                        >
                          SELECT DIFFERENT TARGET
                        </button>

                        <button
                          onClick={() => runLibraryAnalysis(selectedLibraryObs)}
                          className="flex-1 py-3 px-4 rounded bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer"
                        >
                          <Rocket className="w-4 h-4 text-[#070B11]" />
                          RUN ASTRA ANALYSIS
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Loading States: VALIDATING or ANALYZING */}
      {(state === 'validating' || state === 'analyzing') && (
        <div className="border border-[#252D37] bg-[#070B11]/90 rounded-xl p-10 text-center space-y-4 min-h-[260px] flex flex-col items-center justify-center font-mono-tech">
          <RefreshCw className="w-10 h-10 text-[#8FAFC2] animate-spin mx-auto" />
          <div className="space-y-1">
            <p className="text-sm font-bold text-[#F2F4F7]">
              {state === 'validating' ? 'VALIDATING ASTRONOMICAL FORMAT...' : 'ANALYZING MORPHOLOGY & TRIAGE...'}
            </p>
            <p className="text-xs text-[#717985]">
              Evaluating open-world semantic gate & learned Galaxy Zoo manifold...
            </p>
          </div>
        </div>
      )}

      {/* ERROR State */}
      {state === 'error' && (
        <div className="border border-[#3A1D1D] bg-[#1F0E0E]/90 rounded-xl p-8 text-center space-y-4 font-mono-tech">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <div className="space-y-1">
            <p className="text-sm font-bold text-rose-300">ANALYSIS COULD NOT BE COMPLETED</p>
            <p className="text-xs text-[#A8B0BA] font-sans-ui max-w-md mx-auto">{errorMessage}</p>
          </div>
          <button
            onClick={resetUpload}
            className="px-4 py-2 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] font-mono-tech text-xs border border-[#252D37] cursor-pointer transition-all"
          >
            TRY ANOTHER FILE
          </button>
        </div>
      )}

      {/* SUCCESS State with Real Backend Triage Result */}
      {state === 'success' && triageResult && (
        <div className="space-y-6">
          {/* Domain COMPATIBLE or UNCERTAIN View */}
          {(triageResult.domain_validation?.decision === 'COMPATIBLE' || triageResult.domain_validation?.decision === 'UNCERTAIN') && (
            <div className="space-y-6">
              {triageResult.domain_validation?.decision === 'COMPATIBLE' ? (
                <div className="p-4 rounded-xl bg-[#0E241B] border border-[#5FC7A1]/40 flex items-center justify-between font-mono-tech text-xs">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#5FC7A1] shrink-0" />
                    <div>
                      <span className="font-bold text-[#5FC7A1] uppercase block">ASTRONOMICAL DOMAIN COMPATIBLE</span>
                      <span className="text-[#A8B0BA] font-sans-ui text-[11px]">{triageResult.domain_validation.semantic_reason || 'Verified as astronomical imagery by onboard domain gate.'}</span>
                    </div>
                  </div>
                  {triageResult.priority_level && (
                    <PriorityBadge priority={triageResult.priority_level} />
                  )}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-[#3A2B15]/80 border border-[#D6A84F]/50 flex items-center justify-between font-mono-tech text-xs">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-[#D6A84F] shrink-0" />
                    <div>
                      <span className="font-bold text-[#D6A84F] uppercase block">ASTRONOMY IMAGE ACCEPTED — UNCERTAIN DOMAIN</span>
                      <span className="text-[#A8B0BA] font-sans-ui text-[11px]">
                        {triageResult.domain_validation?.semantic_reason || 'Recognized as astronomy-related imagery. Visual evidence preserved for multi-modal catalog enrichment.'}
                      </span>
                    </div>
                  </div>
                  {triageResult.priority_level && (
                    <PriorityBadge priority={triageResult.priority_level} />
                  )}
                </div>
              )}

              {/* Result Main Display Grid */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                {/* Left: Image & Morphology Classification */}
                <div className="md:col-span-6 space-y-4">
                  {previewUrl && (
                    <div className="aspect-square w-full rounded-lg overflow-hidden bg-[#030508] border border-[#252D37] relative">
                      <img src={previewUrl} alt="Uploaded observation" className="w-full h-full object-cover" />
                      <div className="absolute top-3 left-3 bg-[#030508]/90 px-2.5 py-1 rounded text-xs font-mono-tech text-[#D5DAE0] border border-[#C7CDD5]/30 backdrop-blur-md">
                        {selectedLibraryObs ? 'CURATED LIBRARY TARGET ANALYSIS' : 'LIVE UPLOAD ANALYSIS'}
                      </div>
                    </div>
                  )}

                  {selectedLibraryObs && (
                    <div className="bg-[#15232E]/70 p-3.5 rounded-lg border border-[#8FAFC2]/40 font-mono-tech text-xs space-y-1">
                      <div className="flex justify-between items-center text-[#8FAFC2] font-bold">
                        <span>SOURCE DATA: GALAXY ZOO 2 / SDSS DR7</span>
                        <span className="text-[10px] text-[#A8B0BA] font-normal">{selectedLibraryObs.id}</span>
                      </div>
                      <div className="text-[11px] text-[#A8B0BA] font-sans-ui">
                        Catalog Taxonomy: <strong className="text-white">{selectedLibraryObs.broad_morphology}</strong> ({selectedLibraryObs.gz2class})
                      </div>
                    </div>
                  )}

                  {triageResult.predicted_class && triageResult.class_confidence != null && triageResult.class_probabilities ? (
                    <div className="bg-[#0D1219]/80 p-4 rounded-lg border border-[#252D37] space-y-3 font-mono-tech">
                      <div className="flex justify-between items-center font-mono-tech">
                        <span className="text-xs text-[#717985]">PREDICTED MORPHOLOGY</span>
                        <span className="text-sm font-bold text-[#F2F4F7] uppercase">{triageResult.predicted_class}</span>
                      </div>
                      <div className="flex justify-between items-center font-mono-tech text-xs">
                        <span className="text-[#717985]">MORPHOLOGY CONFIDENCE</span>
                        <span className="text-[#5FC7A1] font-bold">{(triageResult.class_confidence * 100).toFixed(1)}%</span>
                      </div>

                      <div className="space-y-2 pt-2 border-t border-[#252D37]">
                        {Object.entries(triageResult.class_probabilities).map(([cls, prob]) => (
                          <ConfidenceBar
                            key={cls}
                            label={cls}
                            value={prob}
                            color={prob > 0.7 ? 'silver' : prob > 0.2 ? 'emerald' : 'amber'}
                          />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-[#0D1219]/80 p-4 rounded-lg border border-[#252D37] space-y-3 font-mono-tech text-xs">
                      <div className="flex justify-between items-center border-b border-[#252D37] pb-2">
                        <span className="text-[11px] text-[#D5DAE0] font-bold uppercase">OBJECT ROUTER EVIDENCE</span>
                        <span className="text-[10px] text-amber-300 bg-amber-950/60 border border-amber-500/40 px-2 py-0.5 rounded font-bold">
                          {triageResult.object_type_status || 'EXPERIMENTAL_ZERO_SHOT'}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div className="bg-[#070B11] p-2.5 rounded border border-[#252D37]">
                          <span className="text-[10px] text-[#717985] block uppercase">Visual Similarity</span>
                          <span className="text-cyan-300 font-bold text-sm">
                            {triageResult.visual_similarity_score !== undefined && triageResult.visual_similarity_score !== null
                              ? triageResult.visual_similarity_score.toFixed(2)
                              : 'N/A'}
                          </span>
                        </div>
                        <div className="bg-[#070B11] p-2.5 rounded border border-[#252D37]">
                          <span className="text-[10px] text-[#717985] block uppercase">Decision Margin</span>
                          <span className="text-emerald-300 font-bold text-sm">
                            {triageResult.object_margin !== undefined && triageResult.object_margin !== null
                              ? `+${triageResult.object_margin.toFixed(2)}`
                              : 'N/A'}
                          </span>
                        </div>
                      </div>

                      <div className="p-3 bg-[#15232E]/60 rounded border border-[#8FAFC2]/30 text-[11px] text-[#A8B0BA] font-sans-ui leading-relaxed">
                        Galaxy Zoo morphology specialist was not executed because this target was resolved as a non-galaxy observation ({triageResult.predicted_object_type || 'Unresolved point source'}).
                      </div>
                    </div>
                  )}
                </div>

                {/* Right: Scientific ANOMALY Interpretation & Triage Explanation */}
                <div className="md:col-span-6 space-y-4">
                  <TriageExplanation
                    signals={{
                      score: triageResult.experimental_triage_score,
                      priority: triageResult.priority_level,
                      novelty_score: triageResult.novelty_score,
                      uncertainty_score: triageResult.uncertainty_score,
                      oddity_score: triageResult.oddity_score,
                      raw_embedding_distance: triageResult.raw_embedding_distance,
                      confidence: triageResult.class_confidence,
                      p_odd: triageResult.scientific_attributes?.prob_odd,
                      predicted_class: triageResult.predicted_class,
                      nearest_reference_class: triageResult.nearest_reference_class,
                      model_version: triageResult.model_version,
                      domain_status: triageResult.domain_validation?.decision,
                      domain_reason: triageResult.domain_validation?.semantic_reason,
                      object_type_info: triageResult.object_type_info,
                      morphology_info: triageResult.morphology_info,
                      object_type: triageResult.object_type || selectedLibraryObs?.object_type,
                      morphology: triageResult.morphology,
                      scientific_attributes: triageResult.scientific_attributes
                    }}
                  />

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-2 font-mono-tech">
                    <button
                      onClick={resetUpload}
                      className="flex-1 py-2.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#A8B0BA] font-mono-tech text-xs border border-[#252D37] transition-all cursor-pointer"
                    >
                      UPLOAD ANOTHER IMAGE
                    </button>

                    {onInspectResult && selectedFile && previewUrl && (
                      <button
                        onClick={() => onInspectResult(triageResult, selectedFile, previewUrl)}
                        className="flex-1 py-2.5 rounded bg-[#D5DAE0] hover:bg-white text-[#070B11] font-mono-tech text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-md"
                      >
                        INSPECT DETAILED VIEW <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Domain INCOMPATIBLE View */}
          {triageResult.domain_validation?.decision === 'INCOMPATIBLE' && (
            <div className="space-y-6 font-mono-tech">
              <div className="p-4 rounded-xl bg-[#3A1D1D]/80 border border-rose-500/50 flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-rose-400 shrink-0" />
                <div>
                  <span className="text-xs text-rose-300 font-bold uppercase block">
                    REJECTED: NON-ASTRONOMICAL IMAGE
                  </span>
                  <span className="text-xs text-[#A8B0BA] font-sans-ui">
                    The uploaded image was flagged as non-astronomical imagery and was rejected prior to ML inference.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                <div className="md:col-span-5">
                  {previewUrl && (
                    <div className="aspect-square w-full rounded-lg overflow-hidden bg-black border border-rose-900/40 relative">
                      <img src={previewUrl} alt="Incompatible input" className="w-full h-full object-cover opacity-60 grayscale" />
                      <div className="absolute top-3 left-3 bg-rose-950/90 px-2.5 py-1 rounded text-xs font-mono-tech text-rose-300 border border-rose-500/40 backdrop-blur-md">
                        REJECTED BY PRE-GATE
                      </div>
                    </div>
                  )}
                </div>

                <div className="md:col-span-7 space-y-4 flex flex-col justify-between">
                  <div className="bg-[#030508]/90 p-5 rounded-xl border border-[#252D37] space-y-3 font-sans-ui">
                    <h3 className="text-sm font-mono-tech font-bold text-rose-300 uppercase tracking-wide flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-rose-400" />
                      SAFETY SYSTEM PRE-GATE REJECTION
                    </h3>
                    <p className="text-xs text-[#A8B0BA] leading-relaxed font-sans-ui">
                      {triageResult.domain_validation.semantic_reason || 'Image fell outside astronomical survey requirements.'}
                    </p>
                    {triageResult.domain_validation.semantic_reason && (
                      <div className="p-3 bg-[#3A1D1D]/30 rounded border border-rose-500/20 text-xs font-mono-tech text-rose-200">
                        Reason: {triageResult.domain_validation.semantic_reason}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={resetUpload}
                    className="w-full py-3 rounded bg-[#151B23] hover:bg-[#252D37] text-[#F2F4F7] font-mono-tech text-xs font-bold border border-[#252D37] transition-all cursor-pointer"
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
