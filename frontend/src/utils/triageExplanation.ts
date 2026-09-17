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
  domain_status?: 'COMPATIBLE' | 'UNCERTAIN' | 'INCOMPATIBLE' | string | null;
  domain_reason?: string | null;
  object_type?: string | null;
  morphology?: string | null;
  object_type_info?: {
    label: string | null;
    predicted_object_type?: string | null;
    confidence?: number | null;
    status: string;
    evidence_quality?: string | null;
    object_evidence_source?: string[] | null;
    visual_similarity_score?: number | null;
    object_margin?: number | null;
    object_confidence?: number | null;
    top_score?: number | null;
    margin_between_top_and_second?: number | null;
    evidence?: string[] | null;
  } | null;
  morphology_info?: {
    label: string | null;
    confidence: number | null;
    status: 'SUPPORTED' | 'NOT_APPLICABLE' | 'UNAVAILABLE' | string;
  } | null;
  scientific_attributes?: {
    prob_smooth?: number;
    prob_features?: number;
    prob_edgeon?: number;
    prob_spiral?: number;
    prob_bar?: number;
    prob_odd?: number;
  } | null;
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

export interface AnomalyInterpretation {
  isDomainCompatible: boolean;
  objectType: string;               // e.g. "Galaxy" or "Unresolved astronomical source" or "ASTRONOMICAL OBSERVATION NOT CONFIRMED"
  objectTypeLabel: string;          // e.g. "Confirmed galaxy route" or "Astronomical object — type unresolved"
  morphology: string;               // e.g. "Spiral", "Edge-on", or "Not applicable"
  confidencePct: string;            // e.g. "82.4%" or "Not applicable"
  whatLooksDifferent: string;       // Dynamic explanation derived from signals & attributes
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priorityWording: string;          // Priority title
  whyThisPriority: string;          // Priority-specific explanation matching canonical text
  recommendedAction: string;        // Space station operator recommendation
  primaryReason: string;            // Concise primary driver statement
}

export interface TriageExplanationResult {
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priorityWording: string;
  priorityDescription: string;
  triageScore: number | null;
  interpretation: AnomalyInterpretation;
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
  }

  // 3. Resolve Oddity
  let oddity: number | null = null;
  if (input.oddity_score !== undefined && input.oddity_score !== null && !isNaN(input.oddity_score)) {
    oddity = Math.min(Math.max(input.oddity_score, 0), 1);
  }

  // 4. Resolve Canonical Score
  let score: number | null = null;
  if (input.score !== undefined && input.score !== null && !isNaN(input.score)) {
    score = Math.min(Math.max(input.score, 0), 1);
  } else if (novelty !== null && uncertainty !== null && oddity !== null) {
    score = Math.min(Math.max(0.35 * novelty + 0.35 * uncertainty + 0.30 * oddity, 0), 1);
  }

  // 5. Resolve Canonical Priority using strict boundaries
  let priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' = input.priority || 'LOW';
  if (score !== null) {
    if (score >= 0.70) priority = 'CRITICAL';
    else if (score >= 0.50) priority = 'HIGH';
    else if (score >= 0.30) priority = 'MEDIUM';
    else priority = 'LOW';
  }

  // Domain Compatibility check
  const isDomainIncompatible = input.domain_status === 'INCOMPATIBLE' || input.domain_status === 'UNCERTAIN';
  const rawObjType = (input.object_type_info?.label || input.object_type_info?.predicted_object_type || input.object_type || '').toUpperCase();
  const isGalaxyRoute = !isDomainIncompatible && (rawObjType === 'GALAXY');
  const isStarRoute = !isDomainIncompatible && (rawObjType === 'STAR' || rawObjType === 'STAR_CANDIDATE');
  const isNebulaRoute = !isDomainIncompatible && (rawObjType === 'NEBULA' || rawObjType === 'NEBULA_CANDIDATE');
  const isQuasarRoute = !isDomainIncompatible && (rawObjType === 'QUASAR' || rawObjType === 'QUASAR_CANDIDATE');
  const isPlanetaryRoute = !isDomainIncompatible && (rawObjType === 'PLANETARY' || rawObjType === 'PLANETARY_CANDIDATE');
  const isPointAmbiguousRoute = !isDomainIncompatible && (rawObjType === 'AMBIGUOUS_POINT_SOURCE');
  const isAmbiguousRoute = !isDomainIncompatible && (rawObjType === 'ASTRONOMICAL_SOURCE_AMBIGUOUS' || rawObjType === 'AMBIGUOUS' || rawObjType === 'INSUFFICIENT_VISUAL_EVIDENCE');

  // 6. Scientific Object & Morphology Separation
  let objectType = 'Unresolved astronomical source';
  let objectTypeLabel = 'Astronomical object — type unresolved';
  let morphologyText = 'Not applicable';
  let confPctStr = 'Not established';

  if (isDomainIncompatible) {
    objectType = 'ASTRONOMICAL OBSERVATION NOT CONFIRMED';
    objectTypeLabel = 'Observation domain not confirmed';
    morphologyText = 'Not performed';
    confPctStr = 'Not applicable';
  } else if (isGalaxyRoute) {
    objectType = 'GALAXY';
    objectTypeLabel = 'Confirmed galaxy route';

    const morphologyVal = input.morphology_info?.label || input.morphology || input.predicted_class;
    if (morphologyVal) {
      const cls = morphologyVal.toUpperCase();
      if (cls === 'SPIRAL') morphologyText = 'Spiral';
      else if (cls === 'EDGE_ON') morphologyText = 'Edge-on';
      else if (cls === 'FEATURED_DISK') morphologyText = 'Featured Disk';
      else if (cls === 'SMOOTH') morphologyText = 'Smooth';
      else morphologyText = morphologyVal;
    } else {
      morphologyText = 'Unclassified galaxy morphology';
    }

    const confVal = input.morphology_info?.confidence ?? input.confidence;
    if (confVal !== null && confVal !== undefined && !isNaN(confVal)) {
      confPctStr = `${(confVal * 100).toFixed(1)}%`;
    } else {
      confPctStr = 'Supported by specialist';
    }
  } else if (isStarRoute) {
    objectType = 'STAR CANDIDATE';
    objectTypeLabel = 'Stellar source candidate';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else if (isNebulaRoute) {
    objectType = 'NEBULA CANDIDATE';
    objectTypeLabel = 'Nebular emission candidate';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else if (isQuasarRoute) {
    objectType = 'QUASAR CANDIDATE';
    objectTypeLabel = 'Quasar candidate classification';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else if (isPlanetaryRoute) {
    objectType = 'PLANETARY CANDIDATE';
    objectTypeLabel = 'Planetary candidate classification';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else if (isPointAmbiguousRoute) {
    objectType = 'AMBIGUOUS POINT SOURCE';
    objectTypeLabel = 'Point-like source (Star vs Quasar unconfirmed)';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else if (isAmbiguousRoute) {
    objectType = 'ASTRONOMICAL SOURCE AMBIGUOUS';
    objectTypeLabel = 'Astronomical object — classification ambiguous';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  } else {
    // UNKNOWN / UNRESOLVED Route
    objectType = 'INSUFFICIENT VISUAL EVIDENCE';
    objectTypeLabel = 'Astronomical object — type unresolved';
    morphologyText = 'Not applicable';
    confPctStr = 'Not applicable';
  }

  // 7. Dynamic "WHAT LOOKS DIFFERENT" Generation (Strictly Routed by Object Type)
  let whatLooksDifferent = '';
  if (isDomainIncompatible) {
    whatLooksDifferent = input.domain_reason || 'ASTRA did not find sufficient evidence that this image is compatible with the supported astronomical observation domain. Morphological classification was not performed.';
  } else if (isGalaxyRoute) {
    const nVal = novelty || 0;
    const uVal = uncertainty || 0;
    const oVal = oddity || 0;

    if (nVal >= 0.5 && uVal >= 0.5 && oVal >= 0.5) {
      whatLooksDifferent = 'The observation shows a strong combination of model uncertainty, unusual embedding distance, and elevated oddity signals relative to ASTRA\'s reference galaxies.';
    } else if (nVal >= 0.5 && uVal >= 0.5) {
      whatLooksDifferent = 'The observation shows a combination of model uncertainty and unusual embedding distance relative to ASTRA\'s reference galaxies.';
    } else if (nVal >= 0.5 && oVal >= 0.5) {
      whatLooksDifferent = 'The observation shows a combination of unusual embedding distance and elevated oddity signals relative to ASTRA\'s reference galaxies.';
    } else if (uVal >= 0.5 && oVal >= 0.5) {
      whatLooksDifferent = 'The observation shows a combination of elevated morphology classification uncertainty and unusual oddity attributes.';
    } else if (nVal >= 0.5) {
      whatLooksDifferent = 'The observation exhibits a visual representation that is noticeably distant from ASTRA\'s learned reference galaxy population in feature space.';
    } else if (uVal >= 0.5) {
      whatLooksDifferent = 'The observation displays elevated classification ambiguity across galaxy morphology heads, indicating complex visual features.';
    } else if (oVal >= 0.5) {
      whatLooksDifferent = 'The observation exhibits elevated irregular or unusual morphology attributes compared to typical reference galaxies.';
    } else {
      whatLooksDifferent = 'The observation aligns closely with standard reference galaxies in ASTRA\'s dataset with low classification uncertainty and no irregular attributes.';
    }

    if (input.scientific_attributes) {
      const sa = input.scientific_attributes;
      if (sa.prob_spiral && sa.prob_spiral > 0.6) {
        whatLooksDifferent += ' Strong spiral-structure evidence detected.';
      } else if (sa.prob_edgeon && sa.prob_edgeon > 0.6) {
        whatLooksDifferent += ' Clear edge-on disk profile presented.';
      } else if (sa.prob_bar && sa.prob_bar > 0.5) {
        whatLooksDifferent += ' Distinct central bar structure identified.';
      } else if (sa.prob_odd && sa.prob_odd > 0.5) {
        whatLooksDifferent += ' Elevated odd/irregular feature probability detected.';
      } else if (sa.prob_features && sa.prob_features > 0.6) {
        whatLooksDifferent += ' Distinct disk features and resonance rings identified.';
      } else if (sa.prob_smooth && sa.prob_smooth > 0.75) {
        whatLooksDifferent += ' Highly symmetric smooth light distribution.';
      }
    }
  } else if (isStarRoute) {
    whatLooksDifferent = 'The observation displays stellar point-source characteristics. Baseline feature representations were computed for scientific prioritization.';
  } else if (isNebulaRoute) {
    whatLooksDifferent = 'Diffuse extended structure + visual evidence supports a nebular cloud candidate.';
  } else if (isQuasarRoute) {
    whatLooksDifferent = 'The observation is identified as a Quasar candidate by the visual evidence router. Baseline feature representations were computed for scientific prioritization.';
  } else if (isPlanetaryRoute) {
    whatLooksDifferent = 'The observation is identified as a planetary candidate object. Baseline feature representations were computed for scientific prioritization.';
  } else if (isPointAmbiguousRoute) {
    whatLooksDifferent = 'Visual evidence supports a compact astronomical source, but the available image does not reliably distinguish a star from a quasar.';
  } else {
    // UNKNOWN / UNRESOLVED / AMBIGUOUS Route
    whatLooksDifferent = 'Visual imaging alone does not provide sufficient evidence for a definitive object classification.';
  }

  // 8. Primary Driver Statement (Strictly Routed by Object Type)
  let primaryReason = '';
  if (isDomainIncompatible) {
    primaryReason = 'Primary reason: Image failed onboard domain validation filter.';
  } else if (isGalaxyRoute) {
    const nVal = novelty || 0;
    const uVal = uncertainty || 0;
    const oVal = oddity || 0;

    if (uVal >= nVal && uVal >= oVal && uVal >= 0.35) {
      primaryReason = 'Primary reason: ASTRA is less confident about the galaxy morphology classification.';
    } else if (nVal >= uVal && nVal >= oVal && nVal >= 0.35) {
      primaryReason = 'Primary reason: The image\'s learned visual representation is noticeably different from reference galaxies.';
    } else if (oVal >= nVal && oVal >= uVal && oVal >= 0.30) {
      primaryReason = 'Primary reason: The galaxy observation has stronger unusual/odd morphology signals than typical reference galaxies.';
    } else if (score !== null && score >= 0.50) {
      primaryReason = 'Primary reasons: The galaxy observation differs from reference galaxies and morphology prediction is relatively uncertain.';
    } else {
      primaryReason = 'Primary reason: The observation aligns closely with standard reference galaxies in ASTRA\'s dataset.';
    }
  } else if (isStarRoute) {
    primaryReason = 'Primary reason: Target source classified as a stellar candidate; Galaxy Zoo morphology classification non-applicable.';
  } else if (isNebulaRoute) {
    primaryReason = 'Primary reason: Target source exhibits diffuse extended nebular emission; Galaxy Zoo morphology classification non-applicable.';
  } else if (isQuasarRoute) {
    primaryReason = 'Primary reason: Target source identified as a quasar candidate; Galaxy Zoo morphology classification non-applicable.';
  } else if (isPlanetaryRoute) {
    primaryReason = 'Primary reason: Target source identified as a planetary candidate; Galaxy Zoo morphology classification non-applicable.';
  } else if (isPointAmbiguousRoute) {
    primaryReason = 'Primary reason: Compact astronomical source; visual imaging alone is insufficient to distinguish a star from a quasar.';
  } else {
    // UNKNOWN / UNRESOLVED Route
    primaryReason = 'Primary reason: Astronomical object evidence insufficient; Galaxy Zoo morphology classification non-applicable.';
  }

  // 9. Canonical Priority Explanations & Operator Recommended Actions
  const priorityWordings: Record<string, string> = {
    LOW: 'Routine observation',
    MEDIUM: 'Worth monitoring',
    HIGH: 'Prioritize for scientific review',
    CRITICAL: 'Strongly prioritize for scientific review'
  };

  const priorityDescriptions: Record<string, string> = {
    LOW: 'This observation looks broadly consistent with ASTRA\'s reference observations. The model is reasonably confident and there is no strong combination of unusual signals. It can remain in the routine observation stream.',
    MEDIUM: 'This observation shows some deviation from the reference population, but the evidence is not strong enough to make it a high-priority target. It is worth keeping in the secondary review queue.',
    HIGH: 'This observation differs noticeably from ASTRA\'s reference population and/or the model is less certain about its classification. The combined evidence is strong enough to justify scientific review.',
    CRITICAL: 'This observation is substantially different from ASTRA\'s reference population and has a strong combination of unusual-signal and/or uncertainty evidence. It should receive attention before routine observations.'
  };

  const recommendedActions: Record<string, string> = {
    LOW: 'Routine processing; no immediate intervention required.',
    MEDIUM: 'Monitor and review when resources permit.',
    HIGH: 'Prioritize for scientific review.',
    CRITICAL: 'Strongly prioritize for scientific review.'
  };

  // Build Prominent Anomaly Interpretation Object
  const interpretation: AnomalyInterpretation = {
    isDomainCompatible: !isDomainIncompatible,
    objectType,
    objectTypeLabel,
    morphology: morphologyText,
    confidencePct: isDomainIncompatible ? 'N/A' : confPctStr,
    whatLooksDifferent,
    priority,
    priorityWording: priorityWordings[priority],
    whyThisPriority: priorityDescriptions[priority],
    recommendedAction: isDomainIncompatible
      ? 'No astronomical classification performed. Verify input file domain.'
      : recommendedActions[priority],
    primaryReason
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
    interpretation,
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

