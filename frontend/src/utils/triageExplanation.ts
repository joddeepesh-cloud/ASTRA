/**
 * ASTRA Triage Explanation Generator Utility
 * 
 * Generates human-readable, judge-friendly, and scientifically grounded
 * explanations from actual ASTRA triage engine outputs.
 * 
 * Rules:
 * - NO fake measurements (no fabricated brightness, redshift, exoplanet, dark matter claims).
 * - Strictly consumes canonical signals: Novelty (35%), Uncertainty (35%), Oddity (30%).
 * - Preserves canonical score equation: Score = 0.35*Novelty + 0.35*Uncertainty + 0.30*Oddity.
 * - Enforces scientific disclaimer: Prioritization heuristic, NOT proof of anomaly/discovery.
 */

export interface TriageInputSignals {
  score: number | null | undefined;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null | undefined;
  novelty_score?: number | null;
  uncertainty_score?: number | null;
  oddity_score?: number | null;
  raw_embedding_distance?: number | null;
  confidence?: number | null;
  p_odd?: number | null;
  predicted_class?: string | null;
  nearest_reference_class?: string | null;
  model_version?: string | null;
}

export interface SignalContribution {
  name: 'Novelty' | 'Uncertainty' | 'Oddity';
  key: 'novelty' | 'uncertainty' | 'oddity';
  score: number | null;
  weight: number; // 0.35 or 0.30
  weightedContribution: number | null;
  magnitudeLabel: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH' | 'UNAVAILABLE';
  simpleExplanation: string;
  technicalDescription: string;
}

export interface TriageExplanationResult {
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priorityWording: string;
  priorityDescription: string;
  triageScore: number | null;
  contributions: SignalContribution[];
  dominantReasons: { rank: number; name: string; label: string; description: string }[];
  summarySentence: string;
  scientificDisclaimer: string;
  simpleTerms: {
    noveltyMeaning: string;
    uncertaintyMeaning: string;
    oddityMeaning: string;
  };
  technicalDetails: {
    rawEmbeddingDistance: number | null;
    confidence: number | null;
    pOdd: number | null;
    predictedClass: string | null;
    nearestReferenceClass: string | null;
    modelVersion: string;
    mathBreakdown: string;
  };
}

/**
 * Categorize a 0.0 - 1.0 signal into standard magnitude tiers.
 */
export function getSignalMagnitude(val: number | null | undefined): 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH' | 'UNAVAILABLE' {
  if (val === null || val === undefined || isNaN(val)) return 'UNAVAILABLE';
  if (val >= 0.75) return 'VERY HIGH';
  if (val >= 0.50) return 'HIGH';
  if (val >= 0.25) return 'MODERATE';
  return 'LOW';
}

/**
 * Generate a complete, dynamic explanation object from raw observation triage signals.
 */
export function generateTriageExplanation(input: TriageInputSignals): TriageExplanationResult {
  // 1. Resolve Novelty
  let novelty: number | null = null;
  if (input.novelty_score !== undefined && input.novelty_score !== null && !isNaN(input.novelty_score)) {
    novelty = Math.min(Math.max(input.novelty_score, 0), 1);
  }

  // 2. Resolve Uncertainty
  let uncertainty: number | null = null;
  if (input.uncertainty_score !== undefined && input.uncertainty_score !== null && !isNaN(input.uncertainty_score)) {
    uncertainty = Math.min(Math.max(input.uncertainty_score, 0), 1);
  } else if (input.confidence !== undefined && input.confidence !== null && !isNaN(input.confidence)) {
    uncertainty = Math.min(Math.max((1.0 - input.confidence) / 0.75, 0), 1);
  }

  // 3. Resolve Oddity
  let oddity: number | null = null;
  if (input.oddity_score !== undefined && input.oddity_score !== null && !isNaN(input.oddity_score)) {
    oddity = Math.min(Math.max(input.oddity_score, 0), 1);
  } else if (input.p_odd !== undefined && input.p_odd !== null && !isNaN(input.p_odd)) {
    oddity = Math.min(Math.max(input.p_odd, 0), 1);
  }

  // 4. Resolve Triage Score
  let score: number | null = null;
  if (input.score !== undefined && input.score !== null && !isNaN(input.score)) {
    score = Math.min(Math.max(input.score, 0), 1);
  } else if (novelty !== null && uncertainty !== null && oddity !== null) {
    score = Math.min(Math.max(0.35 * novelty + 0.35 * uncertainty + 0.30 * oddity, 0), 1);
  }

  // 5. Resolve Canonical Priority
  let priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' = input.priority || 'LOW';
  if (score !== null) {
    if (score >= 0.70) priority = 'CRITICAL';
    else if (score >= 0.50) priority = 'HIGH';
    else if (score >= 0.30) priority = 'MEDIUM';
    else priority = 'LOW';
  }

  // Priority Wordings & Descriptions
  const priorityWordings: Record<string, string> = {
    LOW: 'Routine observation',
    MEDIUM: 'Worth monitoring',
    HIGH: 'Prioritize for scientific review',
    CRITICAL: 'Strongly prioritize for scientific review'
  };

  const priorityDescriptions: Record<string, string> = {
    LOW: 'ASTRA considers this observation relatively routine compared with its reference observations. Its combined novelty, uncertainty, and oddity signals do not currently justify elevated triage priority.',
    MEDIUM: 'ASTRA found some signals worth monitoring, but the combined evidence is not strong enough to place this observation in the high-priority queue.',
    HIGH: 'ASTRA detected a stronger combination of unusualness and/or model uncertainty. This observation is therefore prioritized for scientific review.',
    CRITICAL: 'ASTRA detected a particularly strong combination of triage signals. This observation should be reviewed earlier than lower-priority observations.'
  };

  // Signal Dynamic Explanations
  const getNoveltyText = (val: number | null): string => {
    if (val === null) return 'ASTRA could not compute novelty distance for this target.';
    if (val >= 0.75) return 'ASTRA found this observation significantly distant from its reference embedding space, strongly increasing its novelty contribution.';
    if (val >= 0.50) return 'ASTRA found this observation relatively distant from its reference embedding space, increasing its novelty contribution.';
    if (val >= 0.25) return 'The observation shows a moderate distance from reference embeddings, contributing modestly to novelty.';
    return 'The observation is relatively close to ASTRA\'s reference observations, so novelty contributes little to the priority score.';
  };

  const getUncertaintyText = (val: number | null): string => {
    if (val === null) return 'Morphology model classification uncertainty is unavailable.';
    if (val >= 0.75) return 'The morphology model is highly uncertain about its classification, which strongly increases the review priority.';
    if (val >= 0.50) return 'The morphology model is relatively uncertain about its classification, which increases the review priority.';
    if (val >= 0.25) return 'The morphology model exhibits moderate ambiguity across morphology classes.';
    return 'The morphology model is relatively confident in its classification, so uncertainty contributes little to the priority score.';
  };

  const getOddityText = (val: number | null): string => {
    if (val === null) return 'Galaxy Zoo oddity signal is unavailable for this target.';
    if (val >= 0.75) return 'The learned Galaxy Zoo morphology signals indicate strong odd characteristics, significantly elevating the priority score.';
    if (val >= 0.50) return 'The learned morphology signals indicate relatively strong odd characteristics, increasing the priority score.';
    if (val >= 0.25) return 'The learned morphology signals indicate moderate unusual attributes.';
    return 'The learned oddity signal is low, so unusual morphology contributes little to the priority score.';
  };

  // Build Contributions
  const noveltyContrib = novelty !== null ? novelty * 0.35 : null;
  const uncertaintyContrib = uncertainty !== null ? uncertainty * 0.35 : null;
  const oddityContrib = oddity !== null ? oddity * 0.30 : null;

  const contributions: SignalContribution[] = [
    {
      name: 'Novelty',
      key: 'novelty',
      score: novelty,
      weight: 0.35,
      weightedContribution: noveltyContrib,
      magnitudeLabel: getSignalMagnitude(novelty),
      simpleExplanation: getNoveltyText(novelty),
      technicalDescription: 'Cosine distance of observation representation from training class centroids normalized against dataset bounds [0.214, 0.912].'
    },
    {
      name: 'Uncertainty',
      key: 'uncertainty',
      score: uncertainty,
      weight: 0.35,
      weightedContribution: uncertaintyContrib,
      magnitudeLabel: getSignalMagnitude(uncertainty),
      simpleExplanation: getUncertaintyText(uncertainty),
      technicalDescription: 'Morphology classifier ambiguity derived from top-1 prediction confidence: clip((1.0 - confidence) / 0.75, 0, 1).'
    },
    {
      name: 'Oddity',
      key: 'oddity',
      score: oddity,
      weight: 0.30,
      weightedContribution: oddityContrib,
      magnitudeLabel: getSignalMagnitude(oddity),
      simpleExplanation: getOddityText(oddity),
      technicalDescription: 'Galaxy Zoo-derived continuous odd attribute probability head prediction (prob_odd).'
    }
  ];

  // Primary / Dominant Reasons Ranking
  const validContributions = contributions
    .filter((c) => c.weightedContribution !== null && c.score !== null)
    .sort((a, b) => (b.weightedContribution || 0) - (a.weightedContribution || 0));

  const dominantReasons = validContributions.map((c, index) => {
    const mag = c.magnitudeLabel;
    let desc = '';
    if (c.name === 'Novelty') {
      desc = mag === 'VERY HIGH' || mag === 'HIGH'
        ? 'Significant embedding distance from learned reference centroids.'
        : mag === 'MODERATE'
        ? 'Moderate embedding distance from reference distribution.'
        : 'Low embedding distance contribution.';
    } else if (c.name === 'Uncertainty') {
      desc = mag === 'VERY HIGH' || mag === 'HIGH'
        ? 'Elevated classification uncertainty across morphology heads.'
        : mag === 'MODERATE'
        ? 'Moderate classification ambiguity.'
        : 'High classifier confidence (low uncertainty).';
    } else {
      desc = mag === 'VERY HIGH' || mag === 'HIGH'
        ? 'Strong Galaxy Zoo oddity attribute signal.'
        : mag === 'MODERATE'
        ? 'Moderate unusual morphology attributes.'
        : 'Standard regular morphology attributes.';
    }

    return {
      rank: index + 1,
      name: c.name,
      label: index === 0 ? 'Largest Contribution' : index === 1 ? 'Secondary Driver' : 'Tertiary Signal',
      description: desc
    };
  });

  // Summary sentence construction
  let summarySentence = `ASTRA assigned ${priority} priority (${score !== null ? score.toFixed(2) : 'N/A'}) `;
  if (priority === 'CRITICAL' || priority === 'HIGH') {
    summarySentence += `because the observation shows a strong combination of unusual embedding distance, model uncertainty, and/or unusual morphology.`;
  } else if (priority === 'MEDIUM') {
    summarySentence += `because moderate signals were detected across embedding novelty, classification uncertainty, or oddity heads.`;
  } else {
    summarySentence += `because the observation aligns closely with learned standard reference galaxies with low uncertainty and oddity.`;
  }

  // Math breakdown string
  const nStr = novelty !== null ? (novelty * 0.35).toFixed(3) : 'N/A';
  const uStr = uncertainty !== null ? (uncertainty * 0.35).toFixed(3) : 'N/A';
  const oStr = oddity !== null ? (oddity * 0.30).toFixed(3) : 'N/A';
  const sumStr = (novelty !== null && uncertainty !== null && oddity !== null)
    ? (novelty * 0.35 + uncertainty * 0.35 + oddity * 0.30).toFixed(3)
    : 'N/A';

  const mathBreakdown = `Score = (0.35 × Novelty [${novelty !== null ? novelty.toFixed(2) : 'N/A'}]) + (0.35 × Uncertainty [${uncertainty !== null ? uncertainty.toFixed(2) : 'N/A'}]) + (0.30 × Oddity [${oddity !== null ? oddity.toFixed(2) : 'N/A'}]) = ${nStr} + ${uStr} + ${oStr} = ${sumStr}`;

  return {
    priority,
    priorityWording: priorityWordings[priority],
    priorityDescription: priorityDescriptions[priority],
    triageScore: score,
    contributions,
    dominantReasons,
    summarySentence,
    scientificDisclaimer: 'ASTRA triage is an experimental prioritization heuristic. A high score does not prove that an object is new, rare, artificial, or scientifically anomalous. Final interpretation requires expert scientific review.',
    simpleTerms: {
      noveltyMeaning: 'How different the observation looks from reference galaxies in ASTRA\'s learned feature space.',
      uncertaintyMeaning: 'How unsure the morphology model is about its classification.',
      oddityMeaning: 'How strongly learned Galaxy Zoo morphology signals indicate unusual characteristics.'
    },
    technicalDetails: {
      rawEmbeddingDistance: input.raw_embedding_distance ?? null,
      confidence: input.confidence ?? null,
      pOdd: input.p_odd ?? null,
      predictedClass: input.predicted_class ?? null,
      nearestReferenceClass: input.nearest_reference_class ?? null,
      modelVersion: input.model_version || 'Epoch 10',
      mathBreakdown
    }
  };
}
