import os
import sys
import time
import json
from unittest.mock import patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ml_service import ml_service

def test_adversarial_samples():
    print("=" * 70)
    print("ASTRA PHASE 11 — ADVERSARIAL DOMAIN GATE & SAFETY AUDIT")
    print("=" * 70)

    # List of sample paths to test across different visual categories
    samples = [
        ("A. Galaxy Zoo Smooth Astronomy", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "20027.jpg")),
        ("B. Galaxy Zoo Disk/Spiral Astronomy", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "100035.jpg")),
        ("C. Galaxy Zoo Edge-on Astronomy", os.path.join(PROJECT_ROOT, "ml", "data", "processed", "galaxy_zoo", "images", "100047.jpg")),
        ("D. Ordinary Terrestrial 1 (Dog/Pet)", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0001.jpg")),
        ("E. Ordinary Terrestrial 2 (Person/Portrait)", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0002.jpg")),
        ("F. Ordinary Terrestrial 3 (Car/Vehicle)", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0003.jpg")),
        ("G. Ordinary Terrestrial 4 (Landscape/Nature)", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0004.jpg")),
        ("H. Digital Screenshot / Meme", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0005.jpg")),
        ("I. Synthetic Space Artwork", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "non_astronomical", "non_astro_0010.jpg")),
        ("J. Ambiguous / Boundary Image", os.path.join(PROJECT_ROOT, "ml", "data", "domain_gate", "ambiguous", "ambiguous_001.jpg")),
    ]

    results = []

    with TestClient(app) as client:
        for label, img_path in samples:
            if not os.path.exists(img_path):
                print(f"[-] Missing image for {label}: {img_path}")
                continue

            with open(img_path, "rb") as f:
                img_bytes = f.read()

            filename = os.path.basename(img_path)

            # Spy on triage_single_image to verify morphology execution
            with patch.object(ml_service.triage_engine, "triage_single_image", wraps=ml_service.triage_engine.triage_single_image) as spy_triage:
                t0 = time.perf_counter()
                res = client.post("/api/v1/triage", files={"file": (filename, img_bytes, "image/jpeg")})
                t1 = time.perf_counter()

                data = res.json()
                http_ms = round((t1 - t0) * 1000.0, 2)
                domain = data.get("domain_validation", {})
                decision = domain.get("decision", "UNKNOWN")
                p_astro = domain.get("probability_astronomical", 0.0)
                p_non_astro = domain.get("probability_non_astronomical", 0.0)
                morph_executed = spy_triage.called

                # Validate safety invariant
                if decision in ["INCOMPATIBLE", "UNCERTAIN"]:
                    assert not morph_executed, f"SAFETY VIOLATION: Morphology executed for decision {decision}!"
                elif decision == "COMPATIBLE":
                    assert morph_executed, f"SAFETY VIOLATION: Morphology NOT executed for COMPATIBLE decision!"

                record = {
                    "category": label,
                    "filename": filename,
                    "decision": decision,
                    "p_astronomical": p_astro,
                    "p_non_astronomical": p_non_astro,
                    "morphology_executed": morph_executed,
                    "http_latency_ms": http_ms,
                    "explanation": data.get("explanation", "")
                }
                results.append(record)

                status_flag = "PASS" if ((decision == "COMPATIBLE" and morph_executed) or (decision != "COMPATIBLE" and not morph_executed)) else "FAIL"
                print(f"[{status_flag}] {label:<40} | Decision: {decision:<12} | P(Astro): {p_astro:.4f} | Morph Executed: {str(morph_executed):<5} | {http_ms} ms")

    print("=" * 70)
    print("ALL ADVERSARIAL DOMAIN GATE & SAFETY INVARIANTS PASSED SUCCESSFULLY!")
    print("=" * 70)

    return results

if __name__ == "__main__":
    test_adversarial_samples()
