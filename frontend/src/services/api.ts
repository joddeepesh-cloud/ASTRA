import type { HealthResponse, TriageResponse, ApiErrorResponse, SpaceAIRequest, SpaceAIResponse, EvidenceResponse } from '../types/api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

export class ApiError extends Error {
  errorType: string;
  statusCode: number;

  constructor(message: string, errorType: string = 'api_error', statusCode: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.errorType = errorType;
    this.statusCode = statusCode;
  }
}

/**
 * Perform asynchronous health check against FastAPI backend.
 */
export async function getHealth(externalSignal?: AbortSignal): Promise<HealthResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: externalSignal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(`Health check failed with status ${response.status}`, 'health_failed', response.status);
    }

    const data: HealthResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError('Backend health check timed out.', 'timeout', 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'ASTRA analysis service is currently offline.', 'network_error', 0);
  }
}

/**
 * Upload image for real scientific triage analysis.
 */
export async function triageImage(
  file: File,
  externalSignal?: AbortSignal,
  userSelectedStudyType?: string,
  ra?: number,
  dec?: number,
  observationId?: string
): Promise<TriageResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

  const formData = new FormData();
  formData.append('file', file, file.name);
  if (userSelectedStudyType) {
    formData.append('user_selected_study_type', userSelectedStudyType);
  }
  if (ra !== undefined && ra !== null) {
    formData.append('ra', ra.toString());
  }
  if (dec !== undefined && dec !== null) {
    formData.append('dec', dec.toString());
  }
  if (observationId) {
    formData.append('observation_id', observationId);
  }


  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/triage`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: formData,
      signal: externalSignal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errMessage = `Server error (${response.status})`;
      let errType = 'server_error';

      try {
        const errData: ApiErrorResponse = await response.json();
        if (errData.message) errMessage = errData.message;
        if (errData.error) errType = errData.error;
      } catch {
        // use fallback message
      }

      throw new ApiError(errMessage, errType, response.status);
    }

    const data: TriageResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError('Analysis request timed out after 15 seconds. Please try again.', 'timeout', 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err.message || "ASTRA's analysis service is currently unavailable. Live analysis cannot be performed.",
      'network_error',
      0
    );
  }
}

/**
 * Submit question to ASTRA Space Help AI backend endpoint.
 */
export async function askSpaceAI(
  input: SpaceAIRequest | string,
  obsContextOrSignal?: Record<string, any> | AbortSignal,
  externalSignal?: AbortSignal
): Promise<SpaceAIResponse> {
  let reqPayload: SpaceAIRequest;
  let signalToUse: AbortSignal | undefined;

  if (typeof input === 'string') {
    reqPayload = {
      question: input,
      observation_context: (obsContextOrSignal && !('aborted' in obsContextOrSignal)) ? obsContextOrSignal : null,
    };
    signalToUse = externalSignal || (obsContextOrSignal && ('aborted' in obsContextOrSignal) ? (obsContextOrSignal as AbortSignal) : undefined);
  } else {
    reqPayload = input;
    signalToUse = (obsContextOrSignal && ('aborted' in obsContextOrSignal)) ? (obsContextOrSignal as AbortSignal) : externalSignal;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/space-ai`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(reqPayload),
      signal: signalToUse || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(`Space AI request failed with status ${response.status}`, 'space_ai_error', response.status);
    }

    const data: SpaceAIResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError('Space Help AI request timed out.', 'timeout', 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Space Help AI service is currently unreachable.', 'network_error', 0);
  }
}

/**
 * Alias for askSpaceAI for AskAstra modal backward compatibility.
 */
export const askAstraAI = askSpaceAI;

/**
 * Fetch multi-modal catalog evidence fusion result for observation.
 */
export async function getObservationEvidence(
  observationId: string,
  externalSignal?: AbortSignal
): Promise<EvidenceResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/observations/${encodeURIComponent(observationId)}/evidence`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: externalSignal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new ApiError(`Evidence fetch failed with status ${response.status}`, 'evidence_error', response.status);
    }

    const data: EvidenceResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    return {
      observation_id: observationId,
      evidence_status: 'UNAVAILABLE',
      catalog_sources_queried: ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
      contributing_catalogs: [],
      explanation: 'Catalog evidence service is currently offline.',
      provenance: [],
      conflicts: [],
    };
  }
}

/**
 * Trigger background catalog evidence enrichment for an observation.
 */
export async function triggerObservationEnrichment(
  observationId: string,
  ra?: number,
  dec?: number
): Promise<EvidenceResponse> {
  const formData = new FormData();
  if (ra !== undefined && ra !== null) formData.append('ra', ra.toString());
  if (dec !== undefined && dec !== null) formData.append('dec', dec.toString());

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/observations/${encodeURIComponent(observationId)}/enrich`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(`Enrichment trigger failed (${response.status})`, 'enrichment_error', response.status);
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    return {
      observation_id: observationId,
      evidence_status: 'UNAVAILABLE',
      catalog_sources_queried: ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
      contributing_catalogs: [],
      explanation: 'Enrichment service unavailable.',
      provenance: [],
      conflicts: [],
    };
  }
}


