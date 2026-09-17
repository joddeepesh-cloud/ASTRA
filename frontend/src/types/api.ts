export interface HealthResponse {
  status: string;
  service: string;
  ml_ready: boolean;
  model_loaded: boolean;
  domain_gate_loaded: boolean;
  semantic_gate_loaded?: boolean;
  model_version: string;
  domain_gate_model_version: string;
  semantic_gate_model_version?: string;
  device: string;
  backend_version: string;
  startup_duration_ms: number;
}

export type DomainDecision = 'COMPATIBLE' | 'UNCERTAIN' | 'INCOMPATIBLE';

export interface DomainValidation {
  probability_astronomical: number;
  probability_non_astronomical: number;
  decision: DomainDecision;
  model_version: string;
  inference_time_ms: number;
  semantic_gate_status?: 'SEMANTIC_COMPATIBLE' | 'SEMANTIC_UNCERTAIN' | 'SEMANTIC_INCOMPATIBLE';
  semantic_astronomical_score?: number;
  semantic_competing_score?: number;
  semantic_margin?: number;
  semantic_reason?: string;
}

export interface ClassProbabilities {
  SMOOTH: number;
  EDGE_ON: number;
  FEATURED_DISK: number;
  SPIRAL: number;
  [key: string]: number;
}

export interface ScientificAttributes {
  prob_smooth: number;
  prob_features: number;
  prob_edgeon: number;
  prob_spiral: number;
  prob_bar: number;
  prob_odd: number;
  [key: string]: number;
}

export interface ObjectTypeInfo {
  label: 'GALAXY' | 'STAR' | 'QUASAR' | 'NEBULA' | 'PLANETARY' | 'AMBIGUOUS_POINT_SOURCE' | 'ASTRONOMICAL_SOURCE_AMBIGUOUS' | 'UNKNOWN' | 'INCOMPATIBLE' | string;
  confidence: number | null;
  status: 'EXPERIMENTAL_ZERO_SHOT' | 'REFERENCE_LIBRARY_TARGET' | 'UNAVAILABLE' | string;
  predicted_object_type?: string | null;
  visual_similarity_score?: number | null;
  object_margin?: number | null;
  object_confidence?: number | null;
  object_type_confidence?: number | null;
  object_type_status?: string | null;
  top_class?: string | null;
  top_score?: number | null;
  second_best_class?: string | null;
  margin_between_top_and_second?: number | null;
}

export interface MorphologyInfo {
  label: 'SMOOTH' | 'EDGE_ON' | 'FEATURED_DISK' | 'SPIRAL' | string | null;
  confidence: number | null;
  status: 'SUPPORTED' | 'NOT_APPLICABLE' | 'UNAVAILABLE' | string;
}

export interface TriageResponse {
  domain_validation: DomainValidation;
  object_type_info?: ObjectTypeInfo | null;
  morphology_info?: MorphologyInfo | null;
  predicted_object_type?: string | null;
  visual_similarity_score?: number | null;
  object_margin?: number | null;
  object_confidence?: number | null;
  object_type_confidence?: number | null;
  object_type_status?: string | null;
  user_selected_study_type?: string | null;
  object_type?: 'GALAXY' | 'STAR' | 'QUASAR' | 'NEBULA' | 'PLANETARY' | 'AMBIGUOUS_POINT_SOURCE' | 'ASTRONOMICAL_SOURCE_AMBIGUOUS' | 'UNKNOWN' | 'INCOMPATIBLE' | string | null;
  morphology?: string | null;
  predicted_class?: 'SMOOTH' | 'EDGE_ON' | 'FEATURED_DISK' | 'SPIRAL' | null;
  class_confidence?: number | null;
  class_probabilities?: ClassProbabilities | null;
  scientific_attributes?: ScientificAttributes | null;
  raw_embedding_distance?: number | null;
  raw_pred_class_distance?: number | null;
  nearest_reference_class?: string | null;
  novelty_score?: number | null;
  classification_entropy_bits?: number | null;
  uncertainty_score?: number | null;
  oddity_score?: number | null;
  experimental_triage_score?: number | null;
  priority_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null;
  explanation: string;
  model_version: string;
  inference_time_ms: number;
  total_triage_ms: number;
  score_interpretation: string;
  observation_id?: string | null;
  evidence_status?: 'PENDING' | 'COMPLETE' | 'UNAVAILABLE' | 'ERROR' | string | null;
  ra?: number | null;
  dec?: number | null;
  fused_evidence?: Record<string, any> | null;
}

export interface EvidenceResponse {
  observation_id: string;
  evidence_status: 'PENDING' | 'COMPLETE' | 'UNAVAILABLE' | 'ERROR' | string;
  ra?: number | null;
  dec?: number | null;
  fused_object_type?: string | null;
  evidence_level?: string | null;
  match_quality?: string | null;
  catalog_sources_queried: string[];
  contributing_catalogs: string[];
  explanation: string;
  provenance: string[];
  conflicts: string[];
  fused_result?: Record<string, any> | null;
  updated_at?: string | null;
}


export interface ApiErrorResponse {
  error: string;
  message: string;
}

export type DomainValidationStatus = 'not_implemented' | 'compatible' | 'incompatible' | 'uncertain';

export interface DomainValidationGate {
  compatible: boolean | null;
  status: DomainValidationStatus;
  message: string;
}

export interface SpaceAIRequest {
  question: string;
  observation_context?: Record<string, any> | null;
  conversation_history?: Array<{ sender: string; content: string; role?: string }> | null;
  image_base64?: string | null;
}

export interface SpaceAIResponse {
  answer: string;
  scope: 'observation' | 'astronomy' | 'astra' | 'redirect' | 'error';
  observation_id?: string | null;
  grounded: boolean;
  available: boolean;
  model: string;
  provider: string;
  error?: string | null;
}
