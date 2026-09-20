import type { Observation } from '../types';

export interface ObservationAIContext {
  observation_id: string;
  source: 'USER_UPLOAD' | 'LIBRARY';
  asset_id?: number;
  dr7objid?: string;
  image_url?: string;
  object_type: string | null;
  predicted_object_type: string | null;
  fused_object_type: string | null;
  object_type_status?: string | null;
  broad_morphology?: string;
  gz2class?: string;
  confidence: number | null;
  confidence_pct: string;
  coordinates: {
    ra: number;
    dec: number;
  } | null;
  has_coordinates: boolean;
  provenance?: string;
  probabilities: {
    smooth: number;
    edge_on: number;
    featured_disk: number;
    spiral: number;
    oddity: number;
  };
  triage: {
    priority: string;
    anomaly_score: number;
    ood_score: number;
    novelty_score?: number | null;
    uncertainty_score?: number | null;
    oddity_score?: number | null;
  };
  triage_response?: Record<string, any>;
  scientific_explanation?: string;
  meaning_explanation?: string;
  why_interesting?: string;
  suggested_questions?: string[];
}

/**
 * Derives deterministic, scientifically cautious morphology explanations.
 */
export function getMorphologyMeaning(morphology: string, objectType?: string | null): string {
  const obj = (objectType || '').toUpperCase();
  if (obj && !obj.includes('GALAXY') && obj !== 'UNKNOWN') {
    return `Galaxy Zoo morphology specialist was not executed because this target was resolved as a non-galaxy observation (${objectType}).`;
  }

  switch (morphology) {
    case 'SPIRAL':
      return 'Spiral galaxies are disk-shaped galaxies in which curved structures called spiral arms can be visible, formed by density waves sweeping through interstellar gas and dust.';
    case 'EDGE_ON':
      return 'This galaxy is viewed close to the parallel plane of its disk, making its structure appear elongated or narrow with potential central bulge and dust lane signatures.';
    case 'SMOOTH':
      return 'The galaxy appears smooth and elliptical, featuring a regular, symmetric light distribution without visible spiral arms or distinct disk features.';
    case 'FEATURED_DISK':
      return 'The observation displays disk-related structural features such as central bars, rings, or irregular light concentrations that distinguish it from a visually smooth galaxy.';
    default:
      return 'The observation displays structural features that are currently categorized within the survey morphology pipeline.';
  }
}

/**
 * Derives deterministic, non-fabricated reasons why an observation is scientifically interesting.
 */
export function getWhyInteresting(obs: Observation): string {
  const pOdd = obs.p_odd ?? obs.triage_response?.oddity_score ?? 0.0;
  const conf = obs.confidence;
  const tr = obs.triage_response;
  const objType = tr?.fused_evidence?.fused_object_type || tr?.predicted_object_type || tr?.object_type || obs.object_type;

  if (pOdd >= 0.30) {
    return `The observation exhibits an elevated oddity signal (score = ${pOdd.toFixed(2)}), suggesting unusual visual or structural features worth closer inspection.`;
  }
  if (conf != null && conf < 0.65) {
    return `ASTRA detects competing probability signals, meaning the classification carries higher uncertainty and warrants detailed expert review.`;
  }
  if (obs.anomaly_score >= 0.65) {
    return `ASTRA's prioritization heuristic flagged an elevated triage score (${obs.anomaly_score.toFixed(2)}), prioritizing this record for scientific review.`;
  }
  return `This observation provides a validated record of target ${obs.id} (${objType || 'Astronomical source'}) from the mission database.`;
}

/**
 * Transforms an Observation record into a clean, canonical AI context payload.
 */
export function createObservationAIContext(obs: Observation): ObservationAIContext {
  const tr = obs.triage_response;

  // Authoritative Object Type Hierarchy
  const fusedObjectType = tr?.fused_evidence?.fused_object_type || (obs as any).fused_object_type || null;
  const predictedObjectType = tr?.predicted_object_type || tr?.object_type || tr?.object_type_info?.predicted_object_type || (obs.object_type !== 'Unknown' ? obs.object_type : null);
  const canonicalObjectType = fusedObjectType || predictedObjectType || (obs.object_type && obs.object_type !== 'Unknown' ? obs.object_type : null);

  // Strict Coordinate Validation (NEVER default missing coordinates to 0,0)
  const isLiveUpload = Boolean(obs.is_live || obs.id?.startsWith('LIVE-') || obs.dr7objid === 'USER-UPLOAD');
  const hasValidCoords = typeof obs.ra === 'number' && typeof obs.dec === 'number' && !isNaN(obs.ra) && !isNaN(obs.dec) && !(obs.ra === 0 && obs.dec === 0);

  const coordinates = hasValidCoords ? { ra: obs.ra, dec: obs.dec } : null;

  const pSmooth = obs.p_smooth ?? tr?.scientific_attributes?.prob_smooth ?? (obs.broad_morphology === 'SMOOTH' ? (obs.confidence ?? 0.1) : 0.1);
  const pEdgeon = obs.p_edgeon ?? tr?.scientific_attributes?.prob_edgeon ?? (obs.broad_morphology === 'EDGE_ON' ? (obs.confidence ?? 0.1) : 0.1);
  const pFeatures = obs.p_features ?? tr?.scientific_attributes?.prob_features ?? (obs.broad_morphology === 'FEATURED_DISK' ? (obs.confidence ?? 0.1) : 0.1);
  const pSpiral = obs.p_spiral ?? tr?.scientific_attributes?.prob_spiral ?? (obs.broad_morphology === 'SPIRAL' ? (obs.confidence ?? 0.1) : 0.1);
  const pOdd = obs.p_odd ?? tr?.scientific_attributes?.prob_odd ?? tr?.oddity_score ?? 0.0;

  return {
    observation_id: obs.id,
    source: isLiveUpload ? 'USER_UPLOAD' : 'LIBRARY',
    asset_id: obs.asset_id,
    dr7objid: obs.dr7objid,
    image_url: obs.image_url,
    object_type: canonicalObjectType,
    predicted_object_type: predictedObjectType,
    fused_object_type: fusedObjectType,
    object_type_status: tr?.object_type_status || tr?.object_type_info?.status || 'EXPERIMENTAL',
    broad_morphology: obs.broad_morphology,
    gz2class: obs.gz2class,
    confidence: obs.confidence,
    confidence_pct: obs.confidence != null ? `${(obs.confidence * 100).toFixed(1)}%` : 'N/A',
    coordinates,
    has_coordinates: hasValidCoords,
    provenance: obs.provenance || (isLiveUpload ? 'User Research Upload' : 'Galaxy Zoo 2 Survey / SDSS DR7'),
    probabilities: {
      smooth: round4(pSmooth),
      edge_on: round4(pEdgeon),
      featured_disk: round4(pFeatures),
      spiral: round4(pSpiral),
      oddity: round4(pOdd),
    },
    triage: {
      priority: obs.priority,
      anomaly_score: obs.anomaly_score,
      ood_score: obs.ood_score,
      novelty_score: tr?.novelty_score,
      uncertainty_score: tr?.uncertainty_score,
      oddity_score: tr?.oddity_score,
    },
    triage_response: tr ? (tr as Record<string, any>) : undefined,
    scientific_explanation: obs.explanation || `Astronomical survey observation record (${obs.id}).`,
    meaning_explanation: getMorphologyMeaning(obs.broad_morphology, canonicalObjectType),
    why_interesting: getWhyInteresting(obs),
    suggested_questions: [
      'Tell me about this observation.',
      'Why was this prioritized?',
      'What evidence do we have for this object?',
      'What else can you tell me about this target?',
      'Explain this observation like I am new to astronomy.'
    ],
  };
}

/**
 * Alias for createObservationAIContext
 */
export const buildAskAstraContextPayload = createObservationAIContext;

function round4(val: number | null): number {
  if (val == null) return 0;
  return Math.round(val * 10000) / 10000;
}
