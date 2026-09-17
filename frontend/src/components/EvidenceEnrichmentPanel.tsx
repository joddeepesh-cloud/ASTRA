import React, { useState, useEffect, useCallback } from 'react';
import type { EvidenceResponse } from '../types/api';
import { getObservationEvidence, triggerObservationEnrichment } from '../services/api';
import { Database, CheckCircle2, AlertTriangle, Clock, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';

interface EvidenceEnrichmentPanelProps {
  observationId: string;
  initialObjectType?: string | null;
  ra?: number | null;
  dec?: number | null;
}

export const EvidenceEnrichmentPanel: React.FC<EvidenceEnrichmentPanelProps> = ({
  observationId,
  initialObjectType,
  ra,
  dec,
}) => {
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);


  const fetchEvidence = useCallback(async () => {
    try {
      const data = await getObservationEvidence(observationId);
      setEvidence(data);
      return data;
    } catch {
      // Fallback
      setEvidence({
        observation_id: observationId,
        evidence_status: 'UNAVAILABLE',
        catalog_sources_queried: ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
        contributing_catalogs: [],
        explanation: ra && dec ? 'Connecting to catalog service...' : 'Catalog enrichment unavailable — no trusted celestial coordinates were supplied.',
        provenance: [],
        conflicts: [],
      });
      return null;
    } finally {
      setRefreshing(false);
    }

  }, [observationId, ra, dec]);

  useEffect(() => {
    fetchEvidence();

    // If ra and dec are present and status is PENDING, poll every 3s
    const timer = setInterval(async () => {
      const current = await getObservationEvidence(observationId);
      if (current) {
        setEvidence(current);
        if (current.evidence_status === 'COMPLETE' || current.evidence_status === 'UNAVAILABLE') {
          clearInterval(timer);
        }
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [observationId, fetchEvidence]);

  const handleTriggerEnrichment = async () => {
    setRefreshing(true);
    if (ra !== undefined && ra !== null && dec !== undefined && dec !== null) {
      await triggerObservationEnrichment(observationId, ra, dec);
    }
    await fetchEvidence();
  };

  const status = evidence?.evidence_status || (ra && dec ? 'PENDING' : 'UNAVAILABLE');
  const fusedType = evidence?.fused_object_type;
  const level = evidence?.evidence_level || 'NONE';
  const quality = evidence?.match_quality || 'UNAVAILABLE';
  const contributing = evidence?.contributing_catalogs || [];
  const queried = evidence?.catalog_sources_queried || ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"];
  const conflicts = evidence?.conflicts || [];
  const provenance = evidence?.provenance || [];
  const explanation = evidence?.explanation || (ra && dec ? 'Retrieving multi-modal catalog evidence...' : 'Catalog enrichment unavailable — no trusted celestial coordinates were supplied.');

  return (
    <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4 font-mono text-xs">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="text-sm font-bold text-white tracking-wider flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          MULTI-MODAL EVIDENCE ENRICHMENT & FUSION
        </h3>

        <div className="flex items-center gap-2">
          {status === 'COMPLETE' && (
            <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" /> FUSION COMPLETE
            </span>
          )}
          {status === 'PENDING' && (
            <span className="bg-amber-950/80 text-amber-300 border border-amber-500/50 px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1 animate-pulse">
              <Clock className="w-3 h-3 text-amber-400" /> ENRICHMENT PENDING
            </span>
          )}
          {status === 'UNAVAILABLE' && (
            <span className="bg-slate-900 text-slate-400 border border-slate-800 px-2.5 py-1 rounded text-[10px]">
              ENRICHMENT UNAVAILABLE
            </span>
          )}
          {status === 'ERROR' && (
            <span className="bg-rose-950/80 text-rose-300 border border-rose-500/50 px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-400" /> ENRICHMENT ERROR
            </span>
          )}

          {ra !== undefined && ra !== null && (
            <button
              onClick={handleTriggerEnrichment}
              disabled={refreshing}
              className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
              title="Refresh Evidence"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Primary Comparison: Initial ASTRA vs Fused Interpretation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Initial ASTRA Classification */}
        <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800 space-y-1.5">
          <span className="text-slate-400 text-[10px] block uppercase tracking-wider">Initial ASTRA Classification</span>
          <span className="text-white font-bold text-sm block">
            {initialObjectType || 'AMBIGUOUS_POINT_SOURCE'}
          </span>
          <span className="text-[10px] text-slate-400 block">
            Source: Local Image Structural Analysis & OpenCLIP Zero-Shot
          </span>
        </div>

        {/* Final Fused Evidence-Based Interpretation */}
        <div className="p-3.5 bg-[#0D1520] rounded-lg border border-[#1E2E42] space-y-1.5">
          <span className="text-cyan-400 text-[10px] block uppercase tracking-wider font-bold flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Final Evidence-Based Interpretation
          </span>
          {status === 'COMPLETE' && fusedType ? (
            <span className="text-emerald-300 font-bold text-sm block">
              {fusedType.replace(/_/g, ' ')}
            </span>
          ) : status === 'PENDING' ? (
            <span className="text-amber-300 text-xs block italic">
              Initial ASTRA classification — external evidence enrichment pending.
            </span>
          ) : (
            <span className="text-slate-400 text-xs block italic">
              Catalog enrichment unavailable — no trusted celestial coordinates were supplied.
            </span>
          )}
          <div className="flex items-center gap-2 pt-1">
            <span className="text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
              Level: <strong className="text-cyan-300">{level}</strong>
            </span>
            <span className="text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
              Quality: <strong className="text-emerald-300">{quality.replace(/_/g, ' ')}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Catalog Sources & Evidence Breakdown */}
      <div className="space-y-2 pt-1">
        <div className="flex justify-between items-center text-[11px]">
          <span className="text-slate-400">Queried Catalogs:</span>
          <span className="text-slate-300 font-bold">{queried.join(', ')}</span>
        </div>

        <div className="flex justify-between items-center text-[11px]">
          <span className="text-slate-400">Contributing Catalogs:</span>
          <span className="text-emerald-400 font-bold">
            {contributing.length > 0 ? contributing.join(', ') : 'None (No catalog match within search radius)'}
          </span>
        </div>
      </div>

      {/* Conflicts Banner if Any */}
      {conflicts.length > 0 && (
        <div className="p-3 bg-rose-950/60 border border-rose-500/50 rounded-lg text-rose-200 text-[11px] space-y-1">
          <div className="font-bold flex items-center gap-1.5 text-rose-300">
            <ShieldAlert className="w-4 h-4" /> SCIENTIFIC CONFLICT DETECTED
          </div>
          {conflicts.map((c, i) => (
            <div key={i}>• {c}</div>
          ))}
        </div>
      )}

      {/* Scientific Justification Explanation */}
      <div className="p-3 bg-slate-900/90 rounded border border-slate-800 text-slate-300 text-[11px] leading-relaxed">
        <span className="text-slate-400 font-bold block mb-1">SCIENTIFIC JUSTIFICATION:</span>
        {explanation}
      </div>

      {/* Provenance Trace */}
      {provenance.length > 0 && (
        <div className="text-[10px] text-slate-400 border-t border-slate-800/80 pt-2 space-y-0.5">
          <span className="font-bold text-slate-400">Provenance:</span> {provenance.join(' → ')}
        </div>
      )}
    </div>
  );
};
