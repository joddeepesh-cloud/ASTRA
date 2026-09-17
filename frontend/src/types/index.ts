import type { TriageResponse } from './api';

export type BroadMorphology = 'SMOOTH' | 'EDGE_ON' | 'FEATURED_DISK' | 'SPIRAL' | 'DISK_FEATURE' | 'OTHER';
export type ObjectType = 'Galaxy' | 'GALAXY' | 'Star' | 'Quasar' | 'Unresolved astronomical source' | 'Astronomical object — type unresolved' | 'Unknown';
export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type CatalogMatchStatus = 'MATCHED' | 'WEAK_MATCH' | 'NO_MATCH' | 'UNCHECKED';
export type ActiveTab = 'landing' | 'briefing' | 'observations' | 'anomalies' | 'library' | 'detail' | 'research' | 'copilot' | 'history' | 'settings';

export interface AnalysisHistoryRecord {
  id: string; // e.g. "HIST-20260913-001"
  timestamp: string; // ISO string
  source: 'SIMULATION_STREAM' | 'RESEARCH_UPLOAD' | 'SURVEY_INGEST';
  observation_id: string;
  filename: string;
  domain_status: 'COMPATIBLE' | 'UNCERTAIN' | 'INCOMPATIBLE';
  object_type?: string;
  morphology: string;
  confidence: number | null; // 0.0 - 1.0 or null
  triage_score: number; // 0.0 - 1.0
  priority: PriorityLevel;
  status: 'COMPLETED' | 'FLAGGED_FOR_REVIEW' | 'REJECTED';
  is_demo: boolean;
}

export interface Observation {
  id: string; // e.g. "LIB-000001" or "LIVE-20260912-010500"
  dr7objid: string;
  asset_id: number;
  ra: number;
  dec: number;
  gz2class: string;
  broad_morphology: BroadMorphology;
  object_type: ObjectType;
  confidence: number | null; // 0.0 - 1.0 or null
  anomaly_score: number; // 0.0 - 1.0
  ood_score: number; // Out of distribution score
  priority: PriorityLevel;
  catalog_status: CatalogMatchStatus;
  catalog_name?: string;
  observation_time: string;
  image_url: string;
  split?: 'train' | 'val' | 'test' | 'live';
  explanation?: string;
  provenance?: string;
  p_smooth?: number;
  p_features?: number;
  p_edgeon?: number;
  p_spiral?: number;
  p_bar?: number;
  p_odd?: number;
  morphology_probs: {
    label: string;
    probability: number | null;
  }[];
  is_demo?: boolean;
  is_live?: boolean;
  triage_response?: TriageResponse;
}

export interface SystemTelemetry {
  observations_received: number;
  onboard_processed: number;
  anomalies_flagged: number;
  priority_observations: number;
  downlink_saved_percent: number;
  is_demo: boolean;
}

export interface CopilotMessage {
  id: string;
  sender: 'user' | 'system' | 'copilot';
  timestamp: string;
  content: string;
  observation_id?: string;
  suggested_actions?: string[];
  is_demo?: boolean;
}
