import type { HealthResponse, TriageResponse, ApiErrorResponse } from '../types/api';

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
export async function triageImage(file: File, externalSignal?: AbortSignal): Promise<TriageResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

  const formData = new FormData();
  formData.append('file', file, file.name);

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
