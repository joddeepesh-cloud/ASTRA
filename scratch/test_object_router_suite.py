import os
import sys
import json
import time
from PIL import Image, ImageDraw

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.services.ml_service import ml_service

client = TestClient(app)

def create_synthetic_point_source(filepath):
    """Generate a clean synthetic star/point source cutout for testing."""
    img = Image.new("RGB", (224, 224), color=(5, 5, 10))
    draw = ImageDraw.Draw(img)
    # Draw bright point source with Gaussian-like halo
    for r in range(25, 0, -1):
        brightness = int(255 * (1 - r / 25)**2)
        draw.ellipse([112 - r, 112 - r, 112 + r, 112 + r], fill=(brightness, brightness, int(brightness * 0.9)))
    img.save(filepath)

def create_synthetic_nebula(filepath):
    """Generate a diffuse nebular cloud cutout for testing."""
    img = Image.new("RGB", (224, 224), color=(10, 5, 15))
    draw = ImageDraw.Draw(img)
    for r in range(70, 0, -5):
        alpha = int(180 * (1 - r / 70))
        draw.ellipse([80 - r, 90 - r, 150 + r, 150 + r], fill=(alpha // 2, alpha, int(alpha * 0.8)))
    img.save(filepath)

def run_suite():
    if not ml_service.is_ready:
        ml_service.initialize()

    print("=" * 80)
    print("ASTRA AUTOMATED MULTI-IMAGE OBJECT ROUTER VERIFICATION SUITE")
    print("=" * 80)

    scratch_dir = os.path.join(PROJECT_ROOT, "scratch", "test_images")
    os.makedirs(scratch_dir, exist_ok=True)

    point_path = os.path.join(scratch_dir, "point_source_test.jpg")
    nebula_path = os.path.join(scratch_dir, "nebula_test.jpg")

    create_synthetic_point_source(point_path)
    create_synthetic_nebula(nebula_path)

    test_images = [
        ("Spiral Galaxy (GZ2 20027)", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")),
        ("Smooth Galaxy (GZ2 72807)", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "72807.jpg")),
        ("Edge-On Galaxy (GZ2 153659)", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "153659.jpg")),
        ("Featured Galaxy (GZ2 68687)", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "68687.jpg")),
        ("Stellar Point Source", point_path),
        ("Nebular Cloud", nebula_path),
        ("Non-Astronomical (non_astro_0001.jpg)", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg"))
    ]

    suite_results = []

    for name, path in test_images:
        print(f"\n[TEST TARGET] {name}")
        if not os.path.exists(path):
            print(f"  SKIP: File missing at {path}")
            continue

        with open(path, "rb") as f:
            file_bytes = f.read()

        t0 = time.perf_counter()
        response = client.post(
            "/api/v1/triage",
            files={"file": (os.path.basename(path), file_bytes, "image/jpeg")}
        )
        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000.0

        assert response.status_code == 200, f"API error: {response.status_code} {response.text}"
        data = response.json()

        pred_obj = data.get("predicted_object_type")
        obj_status = data.get("object_type_status")
        vis_score = data.get("visual_similarity_score")
        margin = data.get("object_margin")
        morphology = data.get("morphology")
        morph_conf = data.get("class_confidence")
        triage_score = data.get("experimental_triage_score")
        priority = data.get("priority_level")
        explanation = data.get("explanation")

        print(f"  Domain Status:       {data['domain_validation']['decision']}")
        print(f"  Predicted Object:    {pred_obj}")
        print(f"  Object Status:       {obj_status}")
        print(f"  Visual Similarity:   {vis_score}")
        print(f"  Decision Margin:     {margin}")
        print(f"  Morphology Label:    {morphology}")
        print(f"  Morphology Conf:     {morph_conf if morph_conf is not None else 'N/A (Not Applicable)'}")
        print(f"  Triage Score:        {triage_score if triage_score is not None else 'N/A'}")
        print(f"  Priority Level:      {priority if priority is not None else 'N/A'}")
        print(f"  Latency:             {lat_ms:.2f} ms")
        print(f"  Explanation Snippet: {explanation[:100]}...")

        suite_results.append({
            "target": name,
            "filename": os.path.basename(path),
            "domain": data['domain_validation']['decision'],
            "predicted_object_type": pred_obj,
            "object_status": obj_status,
            "visual_similarity_score": vis_score,
            "object_margin": margin,
            "morphology": morphology,
            "morphology_confidence": morph_conf,
            "triage_score": triage_score,
            "priority": priority,
            "latency_ms": round(lat_ms, 2)
        })

    print("\n" + "=" * 80)
    print("VERIFICATION SUITE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return suite_results

if __name__ == "__main__":
    run_suite()
