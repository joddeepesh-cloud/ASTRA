export type ReviewState = 'UNREVIEWED' | 'REVIEW_PENDING' | 'APPROVED' | 'DEEP_ANALYSIS_REQUESTED';
export type ReviewAction = 'HUMAN_REVIEW' | 'APPROVE' | 'DEEP_ANALYSIS';

export interface ReviewEvent {
  id: string;
  observationId: string;
  action: ReviewAction;
  timestamp: string; // ISO string
  title: string;
  message: string;
  status: ReviewState;
  read: boolean;
}

const EVENTS_STORAGE_KEY = 'astra_review_events';
const STATES_STORAGE_KEY = 'astra_observation_review_states';
const PINNED_STORAGE_KEY = 'astra_pinned_observations';
export const REVIEW_EVENT_CUSTOM_TYPE = 'astra-review-event-updated';

/**
 * Retrieve all persisted review states dictionary from localStorage.
 */
export function getAllObservationReviewStates(): Record<string, ReviewState> {
  try {
    const raw = localStorage.getItem(STATES_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

/**
 * Get review state for a specific observation ID.
 * Defaults to 'UNREVIEWED'.
 */
export function getObservationReviewState(observationId: string): ReviewState {
  if (!observationId) return 'UNREVIEWED';
  const states = getAllObservationReviewStates();
  return states[observationId] || 'UNREVIEWED';
}

/**
 * Set review state for a specific observation ID in localStorage.
 */
export function setObservationReviewState(observationId: string, state: ReviewState): void {
  if (!observationId) return;
  try {
    const states = getAllObservationReviewStates();
    states[observationId] = state;
    localStorage.setItem(STATES_STORAGE_KEY, JSON.stringify(states));
  } catch (err) {
    console.warn('Failed to save review state:', err);
  }
}

/**
 * Retrieve all recorded review events from localStorage.
 * Sorted chronologically by timestamp (newest first).
 */
export function getReviewEvents(): ReviewEvent[] {
  try {
    const raw = localStorage.getItem(EVENTS_STORAGE_KEY);
    if (!raw) return [];
    const events: ReviewEvent[] = JSON.parse(raw);
    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  } catch {
    return [];
  }
}

/**
 * Retrieve list of human-pinned observation IDs.
 */
export function getPinnedObservations(): string[] {
  try {
    const raw = localStorage.getItem(PINNED_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/**
 * Check if a specific observation is human-pinned.
 */
export function isObservationPinned(observationId: string): boolean {
  if (!observationId) return false;
  const pinned = getPinnedObservations();
  return pinned.includes(observationId);
}

/**
 * Pin an observation to the Anomaly Queue (separate from ML priority).
 */
export function pinObservation(observationId: string): void {
  if (!observationId) return;
  try {
    const pinned = getPinnedObservations();
    if (!pinned.includes(observationId)) {
      pinned.push(observationId);
      localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE));
        window.dispatchEvent(
          new CustomEvent('astra-toast', {
            detail: {
              title: 'Pinned to Anomaly Queue',
              message: `Observation ${observationId} pinned for further scientific review.`,
              type: 'info'
            }
          })
        );
      }
    }
  } catch (err) {
    console.warn('Failed to pin observation:', err);
  }
}

/**
 * Unpin an observation from the Anomaly Queue.
 */
export function unpinObservation(observationId: string): void {
  if (!observationId) return;
  try {
    const pinned = getPinnedObservations().filter((id) => id !== observationId);
    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE));
    }
  } catch (err) {
    console.warn('Failed to unpin observation:', err);
  }
}

/**
 * Record a new review event when a user performs a review action.
 * Creates an event, updates observation review state, persists both, and dispatches a DOM event + Toast notification.
 */
export function recordReviewEvent(
  observationId: string,
  action: ReviewAction,
  _metadata?: { priority?: string; morphology?: string }
): { event: ReviewEvent; state: ReviewState } {
  let newState: ReviewState = 'UNREVIEWED';
  let title = '';
  let message = '';

  if (action === 'HUMAN_REVIEW') {
    newState = 'REVIEW_PENDING';
    title = 'Human Review Requested';
    message = `Observation ${observationId} queued for human scientific review.`;
  } else if (action === 'APPROVE') {
    newState = 'APPROVED';
    title = 'Observation Approved';
    message = `ASTRA recorded your approval for observation ${observationId}.`;
  } else if (action === 'DEEP_ANALYSIS') {
    newState = 'DEEP_ANALYSIS_REQUESTED';
    title = 'Deep analysis requested';
    message = `Observation ${observationId} has been flagged for further scientific analysis.`;
  }

  // Update observation review state
  const existingState = getObservationReviewState(observationId);
  setObservationReviewState(observationId, newState);

  const existingEvents = getReviewEvents();
  const isDuplicateDeepAnalysis =
    action === 'DEEP_ANALYSIS' &&
    existingState === 'DEEP_ANALYSIS_REQUESTED' &&
    existingEvents.some((e) => e.observationId === observationId && e.action === 'DEEP_ANALYSIS');

  // Create review event if not duplicate
  let newEvent: ReviewEvent;
  if (isDuplicateDeepAnalysis) {
    newEvent = existingEvents.find((e) => e.observationId === observationId && e.action === 'DEEP_ANALYSIS')!;
  } else {
    newEvent = {
      id: `rev-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      observationId,
      action,
      timestamp: new Date().toISOString(),
      title,
      message,
      status: newState,
      read: false
    };

    try {
      const events = getReviewEvents();
      events.unshift(newEvent);
      localStorage.setItem(EVENTS_STORAGE_KEY, JSON.stringify(events));
    } catch (err) {
      console.warn('Failed to save review event:', err);
    }
  }

  // Broadcast custom event for reactive UI re-renders & notification center integration
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE, { detail: { event: newEvent, state: newState } }));

    // Dispatch toast event
    window.dispatchEvent(
      new CustomEvent('astra-toast', {
        detail: {
          title,
          message,
          type: action === 'APPROVE' ? 'success' : action === 'DEEP_ANALYSIS' ? 'info' : 'warning',
        }
      })
    );
  }

  return { event: newEvent, state: newState };
}

/**
 * Get count of unread review events (for Step 5 notification center).
 */
export function getUnreadEventCount(): number {
  const events = getReviewEvents();
  return events.filter((e) => !e.read).length;
}

/**
 * Mark all review events as read (for Step 5 notification center).
 */
export function markEventsAsRead(): void {
  try {
    const events = getReviewEvents().map((e) => ({ ...e, read: true }));
    localStorage.setItem(EVENTS_STORAGE_KEY, JSON.stringify(events));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE));
    }
  } catch (err) {
    console.warn('Failed to mark review events as read:', err);
  }
}

/**
 * Mark a single review event as read by ID.
 */
export function markSingleEventAsRead(eventId: string): void {
  try {
    const events = getReviewEvents().map((e) => (e.id === eventId ? { ...e, read: true } : e));
    localStorage.setItem(EVENTS_STORAGE_KEY, JSON.stringify(events));
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE));
    }
  } catch (err) {
    console.warn('Failed to mark event as read:', err);
  }
}

/**
 * Utility to clear all review events and pinned observations (e.g. testing).
 */
export function clearAllReviewEvents(): void {
  try {
    localStorage.removeItem(EVENTS_STORAGE_KEY);
    localStorage.removeItem(STATES_STORAGE_KEY);
    localStorage.removeItem(PINNED_STORAGE_KEY);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(REVIEW_EVENT_CUSTOM_TYPE));
    }
  } catch {
    // Ignore error
  }
}

