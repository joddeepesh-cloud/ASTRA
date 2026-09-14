import type { Observation } from '../types';

export interface ObservationAIContext {
  observation_id: string;
  asset_id: number;
  dr7objid: string;
  image_url: string;
  broad_morphology: string;
  gz2class: string;
  confidence: number;
  confidence_pct: string;
  coordinates: {
    ra: number;
    dec: number;
  };
  provenance: string;
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
  };
  scientific_explanation: string;
  meaning_explanation: string;
  why_interesting: string;
  suggested_questions: string[];
}

/**
 * Derives deterministic, scientifically cautious morphology explanations.
 */
export function getMorphologyMeaning(morphology: string): string {
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
  const pOdd = obs.p_odd ?? 0.0;
  const conf = obs.confidence;

  if (pOdd >= 0.30) {
    return `The observation exhibits an elevated Galaxy Zoo oddity signal (prob_odd = ${pOdd.toFixed(2)}), suggesting unusual visual structure worth closer inspection.`;
  }
  if (conf < 0.65) {
    return `ASTRA detects competing morphology probability signals, meaning the classification carries higher uncertainty and warrants detailed expert review.`;
  }
  if (obs.broad_morphology === 'SPIRAL' && (obs.p_spiral ?? 0) >= 0.80) {
    return `The observation exhibits a prominent, high-confidence spiral morphology signal (${((obs.p_spiral ?? conf) * 100).toFixed(0)}%), providing clear structural detail.`;
  }
  if (obs.broad_morphology === 'EDGE_ON' && (obs.p_edgeon ?? 0) >= 0.80) {
    return `The observation presents a strong edge-on disk profile, useful for analyzing vertical disk scale heights and attenuation structures.`;
  }
  if (obs.anomaly_score >= 0.65) {
    return `ASTRA's prioritization heuristic flagged an elevated triage score (${obs.anomaly_score.toFixed(2)}), prioritizing this record for review.`;
  }
  return `This observation provides a clean baseline example of ${obs.broad_morphology.toLowerCase().replace('_', ' ')} galaxy morphology from the survey catalog.`;
}

/**
 * Transforms an Observation record into a clean, structured AI context payload.
 */
export function createObservationAIContext(obs: Observation): ObservationAIContext {
  const pSmooth = obs.p_smooth ?? (obs.broad_morphology === 'SMOOTH' ? obs.confidence : 0.1);
  const pEdgeon = obs.p_edgeon ?? (obs.broad_morphology === 'EDGE_ON' ? obs.confidence : 0.1);
  const pFeatures = obs.p_features ?? (obs.broad_morphology === 'FEATURED_DISK' ? obs.confidence : 0.1);
  const pSpiral = obs.p_spiral ?? (obs.broad_morphology === 'SPIRAL' ? obs.confidence : 0.1);
  const pOdd = obs.p_odd ?? 0.0;

  return {
    observation_id: obs.id,
    asset_id: obs.asset_id,
    dr7objid: obs.dr7objid,
    image_url: obs.image_url,
    broad_morphology: obs.broad_morphology,
    gz2class: obs.gz2class,
    confidence: obs.confidence,
    confidence_pct: `${(obs.confidence * 100).toFixed(1)}%`,
    coordinates: {
      ra: obs.ra,
      dec: obs.dec,
    },
    provenance: obs.provenance || 'Galaxy Zoo 2 Survey / SDSS DR7',
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
    },
    scientific_explanation: obs.explanation || `Astronomical survey observation record (${obs.id}).`,
    meaning_explanation: getMorphologyMeaning(obs.broad_morphology),
    why_interesting: getWhyInteresting(obs),
    suggested_questions: [
      'What am I looking at in this observation?',
      `Why is this classified as ${obs.broad_morphology.replace('_', ' ')}?`,
      'What does the morphology tell us about galaxy structure?',
      'Why does ASTRA consider this observation interesting?',
      'What do these confidence and probability values mean?',
      'Explain this observation like I am new to astronomy.',
    ],
  };
}

/**
 * Alias for createObservationAIContext
 */
export const buildAskAstraContextPayload = createObservationAIContext;

function round4(val: number): number {
  return Math.round(val * 10000) / 10000;
}
