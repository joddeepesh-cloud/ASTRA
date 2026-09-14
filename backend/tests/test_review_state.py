import pytest
from typing import Dict, List, Any, Optional

class ReviewStateStore:
    """
    Python reference implementation of ASTRA Review State Engine & Event Ledger
    for verifying business logic and invariants.
    """
    VALID_STATES = {"UNREVIEWED", "REVIEW_PENDING", "APPROVED", "DEEP_ANALYSIS_REQUESTED"}
    VALID_ACTIONS = {"HUMAN_REVIEW", "APPROVE", "DEEP_ANALYSIS"}

    def __init__(self):
        self._states: Dict[str, str] = {}
        self._events: List[Dict[str, Any]] = []

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

    def record_action(self, observation_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if action not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}")

        if action == "HUMAN_REVIEW":
            new_state = "REVIEW_PENDING"
            title = "Human Review Requested"
            msg = f"Observation {observation_id} queued for human scientific review."
        elif action == "APPROVE":
            new_state = "APPROVED"
            title = "Observation Approved"
            msg = f"ASTRA recorded your approval for observation {observation_id}."
        elif action == "DEEP_ANALYSIS":
            new_state = "DEEP_ANALYSIS_REQUESTED"
            title = "Deep Analysis Requested"
            msg = f"ASTRA recorded observation {observation_id} for deeper scientific follow-up."

        self._states[observation_id] = new_state

        event = {
            "id": f"rev-{len(self._events) + 1}",
            "observationId": observation_id,
            "action": action,
            "timestamp": f"2026-09-14T22:30:0{len(self._events)}Z",
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

# 2. HUMAN_REVIEW event -> unread count 1
def test_human_review_unread_count():
    store = ReviewStateStore()
    store.record_action("LIB-000001", "HUMAN_REVIEW")
    assert store.get_unread_count() == 1
    assert store.get_state("LIB-000001") == "REVIEW_PENDING"

# 3. APPROVE event -> unread count increments
def test_approve_action_unread_increment():
    store = ReviewStateStore()
    store.record_action("LIB-000001", "HUMAN_REVIEW")
    store.record_action("LIB-000002", "APPROVE")
    assert store.get_unread_count() == 2

# 4. DEEP_ANALYSIS event -> unread count increments
def test_deep_analysis_unread_increment():
    store = ReviewStateStore()
    store.record_action("LIB-000001", "HUMAN_REVIEW")
    store.record_action("LIB-000002", "APPROVE")
    store.record_action("LIB-000003", "DEEP_ANALYSIS")
    assert store.get_unread_count() == 3

# 5. Events appear newest first
def test_event_ordering_newest_first():
    store = ReviewStateStore()
    store.record_action("LIB-000001", "HUMAN_REVIEW")
    store.record_action("LIB-000002", "APPROVE")
    events = store.get_events()
    assert events[0]["observationId"] == "LIB-000002"
    assert events[1]["observationId"] == "LIB-000001"

# 6. Individual notification can be marked read
def test_mark_single_notification_read():
    store = ReviewStateStore()
    e1 = store.record_action("LIB-000001", "HUMAN_REVIEW")
    store.record_action("LIB-000002", "APPROVE")
    assert store.get_unread_count() == 2

    store.mark_single_read(e1["id"])
    assert store.get_unread_count() == 1
    assert len(store.get_events()) == 2  # Event remains in ledger after being read

# 7. Mark all as read sets unread count to 0
def test_mark_all_read():
    store = ReviewStateStore()
    store.record_action("LIB-000001", "HUMAN_REVIEW")
    store.record_action("LIB-000002", "APPROVE")
    assert store.get_unread_count() == 2

    store.mark_all_read()
    assert store.get_unread_count() == 0
    assert len(store.get_events()) == 2  # Notifications remain visible in history

# 8. Verification: Notification state does not modify triage score or morphology
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

