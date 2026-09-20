import pytest
from typing import Dict, List, Any, Optional

class ReviewStateStore:
    """
    Python reference implementation of ASTRA Review State Engine & Pinning Ledger
    for verifying business logic and invariants.
    """
    VALID_STATES = {"UNREVIEWED", "REVIEW_PENDING", "APPROVED", "DEEP_ANALYSIS_REQUESTED"}
    VALID_ACTIONS = {"APPROVE", "DEEP_ANALYSIS"}

    def __init__(self):
        self._states: Dict[str, str] = {}
        self._events: List[Dict[str, Any]] = []
        self._pinned: set = set()

    def get_state(self, observation_id: str) -> str:
        return self._states.get(observation_id, "UNREVIEWED")

    def get_events(self) -> List[Dict[str, Any]]:
        return sorted(self._events, key=lambda e: e["timestamp"], reverse=True)

    def get_unread_count(self) -> int:
        return sum(1 for e in self._events if not e.get("read", False))

    def mark_all_read(self) -> None:
        for e in self._events:
            e["read"] = True

    def mark_single_read(self, event_id: str) -> None:
        for e in self._events:
            if e["id"] == event_id:
                e["read"] = True

    def is_pinned(self, observation_id: str) -> bool:
        return observation_id in self._pinned

    def pin_observation(self, observation_id: str) -> None:
        self._pinned.add(observation_id)

    def unpin_observation(self, observation_id: str) -> None:
        self._pinned.discard(observation_id)

    def record_action(self, observation_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if action == "APPROVE":
            new_state = "APPROVED"
            title = "Observation Approved"
            msg = f"ASTRA recorded your approval for observation {observation_id}."
        elif action == "DEEP_ANALYSIS":
            new_state = "DEEP_ANALYSIS_REQUESTED"
            title = "Deep analysis requested"
            msg = f"Observation {observation_id} has been flagged for further scientific analysis."
        else:
            raise ValueError(f"Invalid action: {action}")

        prev_state = self.get_state(observation_id)
        self._states[observation_id] = new_state

        # Check for duplicate deep analysis notification
        if action == "DEEP_ANALYSIS" and prev_state == "DEEP_ANALYSIS_REQUESTED":
            for e in self._events:
                if e["observationId"] == observation_id and e["action"] == "DEEP_ANALYSIS":
                    return e

        event = {
            "id": f"rev-{len(self._events) + 1}",
            "observationId": observation_id,
            "action": action,
            "timestamp": f"2026-09-20T12:00:0{len(self._events)}Z",
            "title": title,
            "message": msg,
            "status": new_state,
            "read": False
        }
        self._events.append(event)
        return event

# 1. Fresh state has 0 notifications and unread count 0
def test_fresh_state_has_no_events():
    store = ReviewStateStore()
    assert store.get_events() == []
    assert store.get_unread_count() == 0
    assert store.get_state("LIB-000001") == "UNREVIEWED"
    assert not store.is_pinned("LIB-000001")

# 2. APPROVE sets state to APPROVED without popup or pinning
def test_approve_action_simple_path():
    store = ReviewStateStore()
    store.record_action("LIB-000042", "APPROVE")
    assert store.get_state("LIB-000042") == "APPROVED"
    assert store.get_unread_count() == 1
    assert not store.is_pinned("LIB-000042")

# 3. DEEP ANALYSIS sets state to DEEP_ANALYSIS_REQUESTED and creates notification
def test_deep_analysis_action():
    store = ReviewStateStore()
    event = store.record_action("LIB-000042", "DEEP_ANALYSIS")
    assert store.get_state("LIB-000042") == "DEEP_ANALYSIS_REQUESTED"
    assert event["title"] == "Deep analysis requested"
    assert event["message"] == "Observation LIB-000042 has been flagged for further scientific analysis."

# 4. Duplicate DEEP ANALYSIS notification is prevented
def test_prevent_duplicate_deep_analysis_notifications():
    store = ReviewStateStore()
    e1 = store.record_action("LIB-000042", "DEEP_ANALYSIS")
    count_1 = len(store.get_events())
    e2 = store.record_action("LIB-000042", "DEEP_ANALYSIS")
    count_2 = len(store.get_events())
    assert count_1 == count_2
    assert e1["id"] == e2["id"]

# 5. Pinning observation creates PINNED state without modifying ML priority or score
def test_pinning_does_not_modify_ml_priority():
    obs = {
        "id": "LIB-000042",
        "priority": "LOW",
        "experimental_triage_score": 0.25
    }
    store = ReviewStateStore()
    store.pin_observation(obs["id"])
    assert store.is_pinned("LIB-000042")
    assert obs["priority"] == "LOW"
    assert obs["experimental_triage_score"] == 0.25

# 6. Both LOW + PINNED and HIGH + PINNED are supported
def test_low_and_high_pinned_support():
    store = ReviewStateStore()
    store.pin_observation("LOW-001")
    store.pin_observation("HIGH-001")
    assert store.is_pinned("LOW-001")
    assert store.is_pinned("HIGH-001")

# 7. Notification state does not modify triage score or morphology
def test_notification_does_not_modify_triage_score():
    observation = {
        "id": "LIB-000001",
        "anomaly_score": 0.85,
        "broad_morphology": "SPIRAL",
        "priority": "HIGH"
    }
    store = ReviewStateStore()
    store.record_action(observation["id"], "APPROVE")
    store.mark_all_read()

    assert observation["anomaly_score"] == 0.85
    assert observation["broad_morphology"] == "SPIRAL"
    assert observation["priority"] == "HIGH"
    assert store.get_state(observation["id"]) == "APPROVED"


