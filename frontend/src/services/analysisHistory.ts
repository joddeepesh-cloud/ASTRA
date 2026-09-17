import type { AnalysisHistoryRecord, PriorityLevel } from '../types';
import type { TriageResponse } from '../types/api';

const V2_STORAGE_KEY = 'astra_analysis_history_v2';
const V1_STORAGE_KEY = 'astra_analysis_history_v1';

export function getAnalysisHistory(): AnalysisHistoryRecord[] {
  try {
    // Try V2 storage first
    const rawV2 = localStorage.getItem(V2_STORAGE_KEY);
    if (rawV2) {
      const parsed = JSON.parse(rawV2);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    }

    // Fallback: Read V1 storage if V2 is empty
    const rawV1 = localStorage.getItem(V1_STORAGE_KEY);
    if (rawV1) {
      const parsedV1 = JSON.parse(rawV1);
      if (Array.isArray(parsedV1)) {
        return parsedV1;
      }
    }
  } catch (err) {
    console.warn('Error reading ASTRA analysis history ledger:', err);
  }
  return [];
}

export function saveAnalysisHistory(records: AnalysisHistoryRecord[]): void {
  try {
    localStorage.setItem(V2_STORAGE_KEY, JSON.stringify(records));
  } catch (err) {
    console.warn('Error saving ASTRA analysis history ledger:', err);
  }
}

export function recordAnalysis(
  result: TriageResponse,
  fileName: string,
  observationId: string,
  source: 'RESEARCH_UPLOAD' | 'LIBRARY' = 'RESEARCH_UPLOAD',
  imageKeyOrUrl?: string
): AnalysisHistoryRecord {
  const domainDecision = result.domain_validation?.decision || 'COMPATIBLE';
  const isCompatible = domainDecision === 'COMPATIBLE';
  const isUncertain = domainDecision === 'UNCERTAIN';
  const triageScore = result.experimental_triage_score ?? 0.0;

  const resolvedObjType = result.predicted_object_type || result.object_type || (domainDecision === 'INCOMPATIBLE' ? 'INCOMPATIBLE' : 'ASTRONOMICAL_SOURCE_AMBIGUOUS');

  const nowISO = new Date().toISOString();
  const runId = `RUN-${Date.now()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
  const histId = `HIST-${observationId || 'OBS'}-${runId.slice(-6)}`;

  const isUserUpload = source === 'RESEARCH_UPLOAD';
  const imageKey = isUserUpload ? imageKeyOrUrl : undefined;
  const imageUrl = !isUserUpload ? imageKeyOrUrl : undefined;

  const newRecord: AnalysisHistoryRecord = {
    id: histId,
    run_id: runId,
    timestamp: nowISO,
    source: source,
    observation_id: observationId || `OBS-${histId.slice(-6)}`,
    filename: fileName || 'Observation_Cutout.jpg',
    image_key: imageKey,
    image_url: imageUrl,
    domain_status: domainDecision as 'COMPATIBLE' | 'UNCERTAIN' | 'INCOMPATIBLE',
    object_type: resolvedObjType,
    morphology: (isCompatible || isUncertain) ? (result.predicted_class || result.morphology || 'OTHER') : 'UNVERIFIED',
    confidence: result.class_confidence ?? null,
    triage_score: triageScore,
    priority: (result.priority_level as PriorityLevel) || 'LOW',
    status: (domainDecision === 'INCOMPATIBLE') ? 'REJECTED' : triageScore > 0.8 ? 'FLAGGED_FOR_REVIEW' : 'COMPLETED',
    is_demo: false,
    triage_response: result
  };

  const current = getAnalysisHistory();
  // Filter out any exact duplicate run_id if re-called
  const updated = [newRecord, ...current.filter(r => r.run_id !== runId && r.id !== histId)];
  saveAnalysisHistory(updated);
  return newRecord;
}

// Backward-compatible wrapper alias
export function recordLiveAnalysis(
  result: TriageResponse,
  fileName: string,
  observationId: string
): AnalysisHistoryRecord {
  return recordAnalysis(result, fileName, observationId, 'RESEARCH_UPLOAD');
}
