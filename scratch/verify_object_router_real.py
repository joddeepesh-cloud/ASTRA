import os
import sys
import io
import time
import numpy as np
from PIL import Image, ImageDraw

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app

def create_synthetic_point_source() -> bytes:
    """Create a synthetic point-source star cutout on astronomical background."""
    np.random.seed(42)
    bg = np.random.poisson(lam=15, size=(224, 224)).astype(np.float32)
    y, x = np.ogrid[:224, :224]
    r2 = (x - 112) ** 2 + (y - 112) ** 2
    star = 220.0 * np.exp(-r2 / (2.0 * 2.5 ** 2))
    img_arr = np.clip(bg + star, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_arr, mode="L").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def create_synthetic_nebula() -> bytes:
    """Create a synthetic diffuse nebula cutout on astronomical background."""
    np.random.seed(42)
    bg = np.random.poisson(lam=15, size=(224, 224)).astype(np.float32)
    y, x = np.ogrid[:224, :224]
    nebula = np.zeros((224, 224), dtype=np.float32)
    for cx, cy, amp in [(80, 90, 80), (130, 120, 100), (110, 140, 70)]:
        r2 = (x - cx) ** 2 + (y - cy) ** 2
        nebula += amp * np.exp(-r2 / (2.0 * 25.0 ** 2))
    img_arr = np.clip(bg + nebula, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_arr, mode="L").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def create_synthetic_non_astro() -> bytes:
    """Create a non-astronomical image."""
    img = Image.new("RGB", (224, 224), (200, 100, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 200, 200], fill=(50, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_verification():
    with TestClient(app) as client:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        gz2_dir = os.path.join(repo_root, "ml", "data", "processed", "galaxy_zoo", "images")
        non_astro_dir = os.path.join(repo_root, "ml", "data", "domain_gate", "non_astronomical")

        test_cases = []

        # 1. Genuine Galaxy (20027.jpg)
        p20027 = os.path.join(gz2_dir, "20027.jpg")
        if os.path.exists(p20027):
            with open(p20027, "rb") as f:
                test_cases.append(("20027.jpg (Galaxy)", f.read(), "GALAXY"))

        # 2. Genuine Galaxy (100035.jpg)
        p100035 = os.path.join(gz2_dir, "100035.jpg")
        if os.path.exists(p100035):
            with open(p100035, "rb") as f:
                test_cases.append(("100035.jpg (Galaxy)", f.read(), "GALAXY"))

        # 3. Bright Point Source
        test_cases.append(("point_source_test.jpg (Point Source)", create_synthetic_point_source(), "AMBIGUOUS_POINT_SOURCE"))

        # 4. Nebular Cloud
        test_cases.append(("nebula_test.jpg (Nebula Cloud)", create_synthetic_nebula(), "NEBULA"))

        # 5. Non-astronomical image
        pnon = os.path.join(non_astro_dir, "non_astro_0001.jpg")
        if os.path.exists(pnon):
            with open(pnon, "rb") as f:
                test_cases.append(("non_astro_0001.jpg (Non-Astro)", f.read(), "INCOMPATIBLE"))
        else:
            test_cases.append(("non_astro_synthetic.jpg (Non-Astro)", create_synthetic_non_astro(), "INCOMPATIBLE"))

    print("=" * 80)
    print("ASTRA LOCAL EVIDENCE-FUSION OBJECT ROUTER VERIFICATION SUITE")
    print("=" * 80)

    passed_count = 0
    total_count = len(test_cases)

    for label, img_bytes, expected_type in test_cases:
        t0 = time.perf_counter()
        resp = client.post(
            "/api/v1/triage",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        t1 = time.perf_counter()
        latency = (t1 - t0) * 1000.0

        assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
        data = resp.json()

        dom_status = data.get("domain_validation", {}).get("decision")
        obj_info = data.get("object_type_info") or {}
        pred_obj = data.get("predicted_object_type") or data.get("object_type")
        status = data.get("object_type_status") or obj_info.get("status")
        vis_score = data.get("visual_similarity_score")
        margin = data.get("object_margin")
        morph_info = data.get("morphology_info") or {}
        morph_conf = morph_info.get("confidence")
        triage_score = data.get("experimental_triage_score")
        priority = data.get("priority_level")

        print(f"\n[TEST CASE] {label}")
        print(f"  Domain Status:              {dom_status}")
        print(f"  Predicted Object Type:      {pred_obj}")
        print(f"  Object Status:              {status}")
        print(f"  Visual Similarity Score:    {vis_score}")
        print(f"  Decision Margin:            {margin}")
        print(f"  Galaxy Morphology Label:    {morph_info.get('label')}")
        print(f"  Galaxy Morphology Conf:     {morph_conf if morph_conf is not None else 'N/A (Not Applicable)'}")
        print(f"  Triage Score:               {triage_score if triage_score is not None else 'N/A'}")
        print(f"  Priority Level:             {priority if priority is not None else 'N/A'}")
        print(f"  Pipeline Latency:           {latency:.2f} ms")
        print(f"  Evidence Summary:           {data.get('explanation')}")

        # CRITICAL ACCEPTANCE ASSERTS:
        if "Point Source" in label:
            assert pred_obj in ("AMBIGUOUS_POINT_SOURCE", "STAR", "ASTRONOMICAL_SOURCE_AMBIGUOUS"), \
                f"Point source must NOT be falsely classified as Quasar! Got {pred_obj}"
            assert morph_conf is None, f"Non-galaxy morphology confidence must be null! Got {morph_conf}"
            print("  ✓ CRITICAL GUARDRAIL PASSED: Point source was NOT falsely classified as Quasar.")

        elif "Nebula" in label:
            assert pred_obj in ("NEBULA", "NEBULA CANDIDATE", "AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"), \
                f"Nebula target must NOT be forced into GALAXY! Got {pred_obj}"
            assert morph_conf is None, f"Nebula morphology confidence must be null! Got {morph_conf}"
            print("  ✓ CRITICAL GUARDRAIL PASSED: Nebula cloud was NOT forced into Galaxy Zoo.")

        elif "Non-Astro" in label:
            assert dom_status == "INCOMPATIBLE", f"Expected INCOMPATIBLE, got {dom_status}"
            assert morph_conf is None, f"Non-astronomical morphology confidence must be null! Got {morph_conf}"
            print("  ✓ CRITICAL GUARDRAIL PASSED: Non-astronomical image correctly rejected.")

        elif "Galaxy" in label:
            assert dom_status == "COMPATIBLE", f"Expected COMPATIBLE galaxy, got {dom_status}"
            print("  ✓ GALAXY ROUTE PASSED: Target domain compatibility verified.")

        passed_count += 1

    print("\n" + "=" * 80)
    print(f"VERIFICATION RESULTS: {passed_count}/{total_count} PASSED CLEANLY (100%)")
    print("=" * 80)

if __name__ == "__main__":
    run_verification()
