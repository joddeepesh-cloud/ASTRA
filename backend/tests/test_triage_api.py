import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_service import ml_service

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLE_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")
SAMPLE_NON_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg")

def test_triage_valid_astronomy_image(client):
    assert os.path.exists(SAMPLE_ASTRO_IMG_PATH), f"Sample astronomy image missing at {SAMPLE_ASTRO_IMG_PATH}"
    
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/triage",
        files={"file": ("20027.jpg", file_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check Domain Gate
    assert "domain_validation" in data
    domain = data["domain_validation"]
    assert domain["decision"] == "COMPATIBLE"
    assert domain["probability_astronomical"] >= 0.80
    assert "model_version" in domain
    assert "inference_time_ms" in domain
    
    # Check downstream Galaxy Zoo results
    assert data["predicted_class"] == "SMOOTH"
    assert round(data["class_confidence"], 2) == 0.93 or round(data["class_confidence"], 1) == 0.9
    assert "class_probabilities" in data
    assert "scientific_attributes" in data
    assert "novelty_score" in data
    assert 0.0 <= data["novelty_score"] <= 1.0
    assert "uncertainty_score" in data
    assert 0.0 <= data["uncertainty_score"] <= 1.0
    assert "oddity_score" in data
    assert 0.0 <= data["oddity_score"] <= 1.0
    assert "experimental_triage_score" in data
    assert 0.0 <= data["experimental_triage_score"] <= 1.0
    assert "priority_level" in data
    assert data["priority_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "explanation" in data
    assert len(data["explanation"]) > 0
    assert "inference_time_ms" in data
    assert "total_triage_ms" in data
    assert "score_interpretation" in data

def test_triage_incompatible_non_astronomy_image(client):
    assert os.path.exists(SAMPLE_NON_ASTRO_IMG_PATH), f"Sample non-astronomy image missing at {SAMPLE_NON_ASTRO_IMG_PATH}"

    with open(SAMPLE_NON_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/triage",
        files={"file": ("non_astro_0001.jpg", file_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()

    assert "domain_validation" in data
    domain = data["domain_validation"]
    assert domain["decision"] == "INCOMPATIBLE"
    assert domain["semantic_gate_status"] == "SEMANTIC_INCOMPATIBLE"

    # Ensure Galaxy Zoo morphology outputs are NOT executed or populated
    assert data.get("predicted_class") is None
    assert data.get("class_confidence") is None
    assert data.get("class_probabilities") is None
    assert data.get("scientific_attributes") is None
    assert data.get("experimental_triage_score") is None
    assert data.get("priority_level") is None

    assert "This image does not appear to contain astronomical observation data. No astronomical classification was performed." in data["explanation"]

def test_rejected_image_does_not_invoke_morphology_model(client):
    with open(SAMPLE_NON_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    with patch.object(ml_service.triage_engine, "triage_single_image") as mock_triage:
        response = client.post(
            "/api/v1/triage",
            files={"file": ("non_astro_0001.jpg", file_bytes, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["domain_validation"]["decision"] == "INCOMPATIBLE"

        # Verify downstream morphology model was NEVER invoked
        mock_triage.assert_not_called()

def test_triage_invalid_corrupted_image(client):
    corrupted_bytes = b"this is not an image file payload"
    response = client.post(
        "/api/v1/triage",
        files={"file": ("fake.jpg", corrupted_bytes, "image/jpeg")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_image"

def test_triage_unsupported_format(client):
    text_bytes = b"hello world plain text file"
    response = client.post(
        "/api/v1/triage",
        files={"file": ("test.txt", text_bytes, "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "unsupported_format"

def test_triage_oversized_image(client):
    huge_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    response = client.post(
        "/api/v1/triage",
        files={"file": ("large.png", huge_bytes, "image/png")}
    )
    assert response.status_code == 413
    data = response.json()
    assert data["error"] == "file_too_large"

def test_triage_determinism(client):
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    res1 = client.post("/api/v1/triage", files={"file": ("20027.jpg", file_bytes, "image/jpeg")}).json()
    res2 = client.post("/api/v1/triage", files={"file": ("20027.jpg", file_bytes, "image/jpeg")}).json()

    assert res1["domain_validation"]["probability_astronomical"] == res2["domain_validation"]["probability_astronomical"]
    assert res1["predicted_class"] == res2["predicted_class"]
    assert res1["class_confidence"] == res2["class_confidence"]
    assert res1["novelty_score"] == res2["novelty_score"]
    assert res1["uncertainty_score"] == res2["uncertainty_score"]
    assert res1["oddity_score"] == res2["oddity_score"]
    assert res1["experimental_triage_score"] == res2["experimental_triage_score"]
    assert res1["priority_level"] == res2["priority_level"]

def test_triage_unresolved_astronomical_source(client):
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    # Upload with a generic filename without galaxy hint or explicit galaxy route
    res = client.post(
        "/api/v1/triage",
        files={"file": ("unknown_cutout.jpg", file_bytes, "image/jpeg")}
    ).json()

    assert res["domain_validation"]["decision"] == "COMPATIBLE"
    # Object identification service returns a supported astronomical label
    assert res["predicted_object_type"] in ["GALAXY", "STAR", "NEBULA", "QUASAR", "PLANETARY", "UNKNOWN", "AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS", "NEBULA_CANDIDATE", "STAR_CANDIDATE", "QUASAR_CANDIDATE"]
    assert res["object_type_status"] in ["SPECIALIST_CONFIRMED", "SUPERVISED_SPECIALIST_SUPPORTED", "EXPERIMENTAL_VISUAL_EVIDENCE", "EXPERIMENTAL_ZERO_SHOT", "INSUFFICIENT_VISUAL_EVIDENCE", "REFERENCE_LIBRARY_TARGET", "UNAVAILABLE"]
    # If not GALAXY, morphology model must not run and morphology/predicted_class must be None
    if res["predicted_object_type"] != "GALAXY":
        assert res["morphology"] is None
        assert res["predicted_class"] is None
        assert res["class_confidence"] is None
        assert res["experimental_triage_score"] is None
    else:
        assert 0.0 <= res["experimental_triage_score"] <= 1.0

def test_user_cannot_inject_object_type(client):
    """Verify frontend/user cannot inject object_type parameter to alter model classification."""
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    # Attempt to inject object_type Form parameter
    res = client.post(
        "/api/v1/triage",
        files={"file": ("cutout.jpg", file_bytes, "image/jpeg")},
        data={"object_type": "STAR"}
    ).json()

    # The classification must be determined by the model, not by the injected Form parameter
    assert res["domain_validation"]["decision"] == "COMPATIBLE"
    assert res["predicted_object_type"] != "STAR" or res["object_type_status"] in ["EXPERIMENTAL_ZERO_SHOT", "REFERENCE_LIBRARY_TARGET"]

def test_user_selected_study_type_does_not_alter_triage(client):
    """Verify user_selected_study_type tag is recorded without changing triage math or object model classification."""
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    res1 = client.post(
        "/api/v1/triage",
        files={"file": ("cutout.jpg", file_bytes, "image/jpeg")}
    ).json()

    res2 = client.post(
        "/api/v1/triage",
        files={"file": ("cutout.jpg", file_bytes, "image/jpeg")},
        data={"user_selected_study_type": "STARS_RESEARCH_PROJECT"}
    ).json()

    assert res2["user_selected_study_type"] == "STARS_RESEARCH_PROJECT"
    assert res1["predicted_object_type"] == res2["predicted_object_type"]
    assert res1["experimental_triage_score"] == res2["experimental_triage_score"]



