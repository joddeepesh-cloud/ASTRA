import os
import io
import pytest
import numpy as np
from PIL import Image

from backend.app.services.ml_service import ml_service
from ml.src.object_identification import ObjectIdentificationService

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLE_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")
SAMPLE_NON_ASTRO_IMG_PATH = os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg")

def test_galaxy_zoo_output_alone_cannot_produce_galaxy():
    """Verify ObjectIdentificationService.classify_pil_image operates independently without Galaxy Zoo input."""
    # Create a synthetic compact point source
    pt_img = Image.new("L", (64, 64), color=10)
    pt_arr = np.array(pt_img, dtype=np.float32)
    y, x = np.indices((64, 64))
    r2 = (x - 32)**2 + (y - 32)**2
    pt_arr += 230.0 * np.exp(-r2 / (2 * 1.5**2))
    pt_pil = Image.fromarray(np.clip(pt_arr, 0, 255).astype(np.uint8)).convert("RGB")

    # Object identification service must return point source / STAR / ambiguous, NOT GALAXY
    res = ml_service.object_id_service.classify_pil_image(pt_pil, filename="compact_star.jpg")
    assert res["predicted_object_type"] != "GALAXY"
    assert res["predicted_object_type"] in ["STAR", "QUASAR_CANDIDATE", "AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"]

def test_non_galaxy_does_not_become_galaxy_from_gz_morphology():
    """Verify non-galaxy point source cutout sent to ml_service.analyze_image does NOT become GALAXY."""
    pt_img = Image.new("L", (64, 64), color=10)
    pt_arr = np.array(pt_img, dtype=np.float32)
    y, x = np.indices((64, 64))
    r2 = (x - 32)**2 + (y - 32)**2
    pt_arr += 230.0 * np.exp(-r2 / (2 * 1.5**2))
    pt_pil = Image.fromarray(np.clip(pt_arr, 0, 255).astype(np.uint8)).convert("RGB")
    buf = io.BytesIO()
    pt_pil.save(buf, format="JPEG")

    out = ml_service.analyze_image(buf.getvalue(), filename="star_point_source.jpg")
    if out["domain_validation"]["decision"] == "COMPATIBLE":
        assert out["predicted_object_type"] != "GALAXY"
        assert out["predicted_object_type"] in ["STAR", "QUASAR_CANDIDATE", "AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"]
        assert out["morphology"] is None
        assert out["morphology_info"]["status"] == "NOT_APPLICABLE"

def test_genuine_galaxy_behavior_intact():
    """Verify genuine galaxy image remains classified as GALAXY and receives Galaxy Zoo morphology."""
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    out = ml_service.analyze_image(file_bytes, filename="20027.jpg")
    assert out["domain_validation"]["decision"] == "COMPATIBLE"
    assert out["predicted_object_type"] == "GALAXY"
    assert out["morphology"] in ["SMOOTH", "SPIRAL", "FEATURED_DISK", "EDGE_ON"]
    assert out["morphology_info"]["status"] == "SUPPORTED"
    assert 0.0 <= out["experimental_triage_score"] <= 1.0

def test_non_astronomy_rejection_intact():
    """Verify non-astronomical images remain INCOMPATIBLE."""
    with open(SAMPLE_NON_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    out = ml_service.analyze_image(file_bytes, filename="non_astro_0001.jpg")
    assert out["domain_validation"]["decision"] == "INCOMPATIBLE"
    assert out["predicted_object_type"] == "INCOMPATIBLE"
    assert out.get("predicted_class") is None
    assert out.get("experimental_triage_score") is None

def test_existing_triage_calculation_untouched():
    """Verify canonical triage calculation formula and scores are untouched for genuine galaxies."""
    with open(SAMPLE_ASTRO_IMG_PATH, "rb") as f:
        file_bytes = f.read()

    out = ml_service.analyze_image(file_bytes, filename="20027.jpg")
    novelty = out["novelty_score"]
    uncertainty = out["uncertainty_score"]
    oddity = out["oddity_score"]
    expected_score = round(0.35 * novelty + 0.35 * uncertainty + 0.30 * oddity, 4)
    assert round(out["experimental_triage_score"], 4) == expected_score
