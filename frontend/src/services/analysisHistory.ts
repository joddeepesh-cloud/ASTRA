import type { AnalysisHistoryRecord, PriorityLevel } from '../types';
import type { TriageResponse } from '../types/api';

const HISTORY_STORAGE_KEY = 'astra_analysis_history_v1';

export function getAnalysisHistory(): AnalysisHistoryRecord[] {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    }
  } catch {
    // ignore
  }
  return [];
}

export function saveAnalysisHistory(records: AnalysisHistoryRecord[]): void {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(records));
  } catch {
    // ignore
  }
}

export function recordLiveAnalysis(
  result: TriageResponse,
  fileName: string,
  observationId: string
): AnalysisHistoryRecord {
  const domainDecision = result.domain_validation?.decision || 'COMPATIBLE';
  const isCompatible = domainDecision === 'COMPATIBLE';
  const isUncertain = domainDecision === 'UNCERTAIN';
  const triageScore = result.experimental_triage_score ?? 0.0;

  const newRecord: AnalysisHistoryRecord = {
    id: `HIST-${Date.now()}`,
    timestamp: new Date().toISOString(),
    source: 'RESEARCH_UPLOAD',
    observation_id: observationId,
    filename: fileName,
    domain_status: domainDecision as 'COMPATIBLE' | 'UNCERTAIN' | 'INCOMPATIBLE',
    morphology: (isCompatible || isUncertain) ? (result.predicted_class || 'OTHER') : 'UNVERIFIED',
    confidence: result.class_confidence ?? 0.0,
    triage_score: triageScore,
    priority: (result.priority_level as PriorityLevel) || 'LOW',
    status: (!isCompatible && !isUncertain) ? 'REJECTED' : triageScore > 0.8 ? 'FLAGGED_FOR_REVIEW' : 'COMPLETED',
    is_demo: false,
  };

  const current = getAnalysisHistory();
  const updated = [newRecord, ...current];
  saveAnalysisHistory(updated);
  return newRecord;
}
