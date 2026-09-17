import React, { useState, useRef, useEffect } from 'react';
import type { AnalysisHistoryRecord, Observation } from '../types';
import libraryData from '../data/observationLibrary.json';
import { getAnalysisHistory } from '../services/analysisHistory';
import { getImageBlob } from '../services/imageStore';
import { PriorityBadge } from '../components/PriorityBadge';
import { EmptyState } from '../components/EmptyState';
import { History, Filter, CheckCircle2, AlertTriangle, XCircle, ExternalLink, ShieldCheck, Database, Inbox } from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

interface HistoryPageProps {
  onInspectObservation?: (obs: Observation) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onInspectObservation }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const createdObjectUrlsRef = useRef<string[]>([]);

  useEffect(() => {
    return () => {
      createdObjectUrlsRef.current.forEach((url) => {
        try {
          URL.revokeObjectURL(url);
        } catch {
          // ignore
        }
      });
      createdObjectUrlsRef.current = [];
    };
  }, []);

  const allRecords = getAnalysisHistory();

  const filteredRecords = allRecords.filter((rec) => {
    if (filterStatus === 'ALL') return true;
    return rec.status === filterStatus;
  });

  const handleInspect = async (record: AnalysisHistoryRecord) => {
    const found = LIBRARY_OBSERVATIONS.find((o) => o.id === record.observation_id);
    let resolvedImageUrl = found ? found.image_url : record.image_url || '';

    if (!resolvedImageUrl && record.image_key) {
      try {
        const blob = await getImageBlob(record.image_key);
        if (blob) {
          resolvedImageUrl = URL.createObjectURL(blob);
          createdObjectUrlsRef.current.push(resolvedImageUrl);
        }
      } catch (err) {
        console.warn('Could not retrieve image Blob from IndexedDB:', err);
      }
    }

    if (onInspectObservation) {
      const syntheticObs: Observation = {
        id: record.observation_id,
        dr7objid: record.source === 'LIBRARY' ? (found?.dr7objid || 'LIBRARY-TARGET') : (record.filename || 'USER-UPLOADED-FILE'),
        asset_id: found ? found.asset_id : 999999,
        ra: record.triage_response?.ra ?? (found ? found.ra : 0.0),
        dec: record.triage_response?.dec ?? (found ? found.dec : 0.0),
        gz2class: record.morphology,
        broad_morphology: (record.morphology === 'SPIRAL' ? 'SPIRAL' : record.morphology === 'SMOOTH' ? 'SMOOTH' : record.morphology === 'FEATURED_DISK' ? 'FEATURED_DISK' : record.morphology === 'EDGE_ON' ? 'EDGE_ON' : 'OTHER') as any,
        object_type: (record.object_type || (record.filename?.startsWith('LIB-') ? 'Galaxy' : 'Unresolved astronomical source')) as any,
        confidence: record.confidence,
        anomaly_score: record.triage_score,
        ood_score: record.triage_score,
        priority: record.priority,
        catalog_status: 'UNCHECKED',
        observation_time: record.timestamp,
        image_url: resolvedImageUrl,
        explanation: record.triage_response?.explanation || `Historical analysis run ${record.id} processed under source ${record.source}. Domain status: ${record.domain_status}.`,
        morphology_probs: [
          { label: record.morphology, probability: record.confidence }
        ],
        triage_response: record.triage_response,
        is_demo: false,
        is_live: record.source === 'RESEARCH_UPLOAD'
      };
      onInspectObservation(syntheticObs);
    }
  };

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-6xl mx-auto font-sans-ui text-[#ECEAF2]" data-tour="history-page">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#21133B] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-serif-display text-white tracking-wider uppercase flex items-center gap-2.5">
              <History className="w-5 h-5 text-[#8FAFC2]" /> ANALYSIS HISTORY
            </h1>
            <span className="text-xs font-mono-tech bg-[#15102A] text-[#9B7FD4] border border-[#9B7FD4]/40 px-2 py-0.5 rounded font-bold">
              SESSION LEDGER
            </span>
          </div>
          <p className="text-xs text-[#8E8A9D] font-sans-ui mt-1">
            Historical ledger of astronomical observation analysis runs, domain verification checks, and experimental triage scores.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center gap-2 self-start md:self-auto bg-slate-900/90 p-1 rounded-lg border border-slate-800">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
          <span className="text-[11px] font-mono text-slate-400 mr-1">STATUS:</span>
          {['ALL', 'FLAGGED_FOR_REVIEW', 'COMPLETED', 'REJECTED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all cursor-pointer ${
                filterStatus === st
                  ? 'bg-[#151B23] text-[#D5DAE0] border border-[#4B5563]/60 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st === 'FLAGGED_FOR_REVIEW' ? 'FLAGGED' : st}
            </button>
          ))}
        </div>
      </div>

      {/* History Ledger Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-[#8FAFC2]" />
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              ANALYSIS RUN RECORDS ({filteredRecords.length})
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            LOCAL SESSION LEDGER
          </span>
        </div>

        {filteredRecords.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="NO ANALYSIS RUNS YET"
            description="Upload an astronomical observation cutout in Research Mode to execute domain validation and scientific triage."
          />
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                <th className="p-3.5">RUN ID / TIMESTAMP</th>
                <th className="p-3.5">SOURCE</th>
                <th className="p-3.5">OBSERVATION / FILE</th>
                <th className="p-3.5 text-center">DOMAIN CHECK</th>
                <th className="p-3.5">MORPHOLOGY</th>
                <th className="p-3.5 text-center">TRIAGE SCORE</th>
                <th className="p-3.5">PRIORITY</th>
                <th className="p-3.5">STATUS</th>
                <th className="p-3.5 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
              {filteredRecords.map((rec) => (
                <tr key={rec.id} className="hover:bg-[#151B23]/50 transition-colors group">
                  <td className="p-3.5">
                    <div className="font-bold text-white flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#8FAFC2]" />
                      {rec.id}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {new Date(rec.timestamp).toUTCString()}
                    </div>
                  </td>
                  <td className="p-3.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                      {rec.source}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <div className="font-semibold text-[#D5DAE0]">{rec.observation_id}</div>
                    <div className="text-[10px] text-slate-400 font-mono truncate max-w-[140px]">
                      {rec.filename}
                    </div>
                  </td>
                  <td className="p-3.5 text-center">
                    {rec.domain_status === 'COMPATIBLE' ? (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
                        <ShieldCheck className="w-3 h-3 text-emerald-400" /> COMPATIBLE
                      </span>
                    ) : rec.domain_status === 'UNCERTAIN' ? (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/60">
                        <AlertTriangle className="w-3 h-3 text-amber-400" /> UNCERTAIN
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/60">
                        <XCircle className="w-3 h-3 text-rose-400" /> INCOMPATIBLE
                      </span>
                    )}
                  </td>
                  <td className="p-3.5">
                    <span className="text-slate-200 font-semibold">{rec.morphology}</span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      {rec.confidence != null ? `${(rec.confidence * 100).toFixed(1)}% conf` : 'conf: N/A'}
                    </span>
                  </td>
                  <td className="p-3.5 text-center font-bold">
                    <span className={rec.triage_score > 0.8 ? 'text-rose-400' : 'text-[#8FAFC2]'}>
                      {rec.triage_score.toFixed(3)}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <PriorityBadge priority={rec.priority} />
                  </td>
                  <td className="p-3.5">
                    {rec.status === 'COMPLETED' ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                      </span>
                    ) : rec.status === 'FLAGGED_FOR_REVIEW' ? (
                      <span className="inline-flex items-center gap-1 text-amber-400 font-semibold text-[11px]">
                        <AlertTriangle className="w-3.5 h-3.5" /> Scientific Review
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-400 font-semibold text-[11px]">
                        <XCircle className="w-3.5 h-3.5" /> Rejected
                      </span>
                    )}
                  </td>
                  <td className="p-3.5 text-right">
                    <button
                      onClick={() => handleInspect(rec)}
                      className="px-2.5 py-1 rounded bg-[#0D1219] hover:bg-[#151B23] text-[#D5DAE0] hover:text-white border border-[#252D37] hover:border-[#4B5563] transition-all text-[11px] inline-flex items-center gap-1 cursor-pointer"
                    >
                      DOSSIER <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </div>
    </div>
  );
};
