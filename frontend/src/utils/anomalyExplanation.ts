import type { Observation } from '../types';

export interface StructuredAnomalyExplanation {
  whatWeAreLookingAt: string;
  astronomyFact: string;
  whyAstraFlaggedIt: string;
  whyFlagged: string;
  whyThisPriority: string;
  whyPriority: string;
  nextSteps: string[];
  recommendedSteps: string[];
}

export function generateAnomalyExplanation(obs: Observation): StructuredAnomalyExplanation {
  const morph = obs.broad_morphology;
  const prio = obs.priority;
  const confPct = obs.confidence != null ? (obs.confidence * 100).toFixed(1) : 'N/A';
  const triageScore = obs.anomaly_score.toFixed(2);
  const oodScore = obs.ood_score ? obs.ood_score.toFixed(2) : triageScore;

  // 1. WHAT ARE WE LOOKING AT?
  let whatText = "";
  let astroFact = "";

  switch (morph) {
    case 'SMOOTH':
      whatText = `Observation ${obs.id} exhibits a Smooth (elliptical) galaxy light profile with symmetric, featureless surface brightness and high model confidence (${confPct}%).`;
      astroFact = "Smooth elliptical galaxies consist primarily of older stellar populations with randomized orbits and minimal interstellar gas or active star formation.";
      break;

    case 'EDGE_ON':
      whatText = `Observation ${obs.id} displays an Edge-On disk galaxy orientation, viewed close to parallel to the galactic plane with a high confidence score (${confPct}%).`;
      astroFact = "Edge-on disk galaxies allow astronomers to study galactic scale heights, vertical dust distribution, and stellar disk thickness across line-of-sight inclinations.";
      break;

    case 'FEATURED_DISK':
      whatText = `Observation ${obs.id} displays Featured Disk morphology, exhibiting visible disk structure, inner ring/bar components, or asymmetric light distributions.`;
      astroFact = "Featured disks represent transitional structural configurations where disk resonance or minor gravitational perturbations produce distinct non-spherical structures.";
      break;

    case 'SPIRAL':
      whatText = `Observation ${obs.id} is classified as a Spiral galaxy, presenting distinct spiral arm structures extending outward from the central galactic bulge (${confPct}% confidence).`;
      astroFact = "Spiral arms are density waves propagating through disk gas and dust, triggering active star formation along bright blue OB stellar associations.";
      break;

    default:
      whatText = `Observation ${obs.id} exhibits complex or disturbed morphology (${obs.gz2class || 'Irregular'}) identified during Galaxy Zoo survey ingest.`;
      astroFact = "Irregular or tidal galaxy structures frequently signal ongoing galactic interactions, merger events, or strong gravitational tidal forces.";
      break;
  }

  // 3. WHY DID ASTRA FLAG IT?
  let whyFlagged = "";
  if (obs.anomaly_score > 0.8) {
    whyFlagged = `ASTRA's triage engine flagged this observation primarily due to high out-of-distribution divergence (OOD score: ${oodScore}). The optical profile falls outside learned standard manifold baselines.`;
  } else if (obs.confidence != null && obs.confidence < 0.75) {
    whyFlagged = `ASTRA flagged this target due to elevated classification uncertainty (${confPct}% confidence). Overlapping morphology features present competing decision-tree hypotheses.`;
  } else {
    whyFlagged = `ASTRA identified this target as presenting a clear reference baseline for ${morph} morphology within the survey dataset.`;
  }

  // 4. WHY THIS PRIORITY?
  let whyPriority = "";
  switch (prio) {
    case 'CRITICAL':
      whyPriority = `Received CRITICAL priority because its experimental triage score (${triageScore}) ranks in the top percentile of out-of-distribution divergence. It is strongly prioritized for scientific review.`;
      break;
    case 'HIGH':
      whyPriority = `Received HIGH priority because its experimental triage score (${triageScore}) signals structural divergence or classification uncertainty warranting Earth-side scientific review.`;
      break;
    case 'MEDIUM':
      whyPriority = `Received MEDIUM priority (triage score: ${triageScore}). Recommended for secondary catalog monitoring during routine operations.`;
      break;
    case 'LOW':
    default:
      whyPriority = `Received LOW priority (triage score: ${triageScore}). Represents a routine, well-conforming baseline observation.`;
      break;
  }

  // 5. WHAT SHOULD A SCIENTIST DO NEXT?
  const nextSteps = [
    "Inspect multi-band photometric cutouts and cross-check sky coordinates in SDSS DR16 / Simbad.",
    "Verify whether non-symmetric light distribution originates from tidal disruption or stellar crowding.",
    "Consider targeted spectroscopic follow-up if out-of-distribution divergence persists during secondary review."
  ];

  return {
    whatWeAreLookingAt: whatText,
    astronomyFact: astroFact,
    whyAstraFlaggedIt: whyFlagged,
    whyFlagged,
    whyThisPriority: whyPriority,
    whyPriority,
    nextSteps,
    recommendedSteps: nextSteps
  };
}

/**
 * Alias for generateAnomalyExplanation
 */
export const getAnomalyExplanation = generateAnomalyExplanation;

