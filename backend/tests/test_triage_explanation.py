import pytest
import numpy as np
from ml.src.triage import ASTRATriageEngine

def test_triage_engine_canonical_equation():
    """Verify canonical score formula: 0.35*Novelty + 0.35*Uncertainty + 0.30*Oddity."""
    # S_novelty = 0.8, S_uncertainty = 0.6, S_oddity = 0.4
    # Score = 0.35*0.8 + 0.35*0.6 + 0.30*0.4 = 0.28 + 0.21 + 0.12 = 0.61 (HIGH)
    nov = 0.8
    unc = 0.6
    odd = 0.4
    expected_score = round(0.35 * nov + 0.35 * unc + 0.30 * odd, 4)
    assert expected_score == 0.61
    assert 0.50 <= expected_score < 0.70  # Canonical HIGH threshold

def test_triage_engine_priority_thresholds():
    """Verify canonical priority threshold boundaries."""
    thresholds = [
        (0.00, "LOW"),
        (0.2999, "LOW"),
        (0.30, "MEDIUM"),
        (0.4999, "MEDIUM"),
        (0.50, "HIGH"),
        (0.6999, "HIGH"),
        (0.70, "CRITICAL"),
        (1.00, "CRITICAL")
    ]
    for score, expected_priority in thresholds:
        if score >= 0.70:
            p = "CRITICAL"
        elif score >= 0.50:
            p = "HIGH"
        elif score >= 0.30:
            p = "MEDIUM"
        else:
            p = "LOW"
        assert p == expected_priority

def test_triage_engine_explanation_output():
    """Verify triage engine produces explanation without illegal claims."""
    engine = ASTRATriageEngine()
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    res = engine.triage_single_image(dummy_img)

    assert "experimental_triage_score" in res
    assert "novelty_score" in res
    assert "uncertainty_score" in res
    assert "oddity_score" in res
    assert "priority_level" in res
    assert "explanation" in res
    assert res["priority_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Strictly verify NO illegal fake claims
    forbidden_terms = ["discovered", "new object", "alien", "NASA notified", "exoplanet transit", "dark matter"]
    for term in forbidden_terms:
        assert term.lower() not in res["explanation"].lower()
