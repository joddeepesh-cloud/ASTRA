#!/usr/bin/env python3
"""
ASTRA Feature 2 — Validate Scientific Observation Library
---------------------------------------------------------
Validates the generated 2,000-record observation library dataset for integrity,
uniqueness, image validity, scientific bounds, and provenance.
"""

import os
import json
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIBRARY_JSON = os.path.join(PROJECT_ROOT, "ml", "data", "library", "observation_library.json")
FRONTEND_DATA_JSON = os.path.join(PROJECT_ROOT, "frontend", "src", "data", "observationLibrary.json")
LIBRARY_IMAGES_DIR = os.path.join(PROJECT_ROOT, "ml", "data", "library", "images")
FRONTEND_PUBLIC_IMAGES = os.path.join(PROJECT_ROOT, "frontend", "public", "library", "images")

VALID_MORPHOLOGIES = {"SMOOTH", "EDGE_ON", "FEATURED_DISK", "SPIRAL"}
VALID_PRIORITIES = {"HIGH", "MEDIUM", "LOW", "CRITICAL"}

def validate_library():
    print("=" * 60)
    print("VALIDATING ASTRA OBSERVATION LIBRARY DATASET")
    print("=" * 60)

    if not os.path.exists(LIBRARY_JSON):
        raise FileNotFoundError(f"Library JSON file missing at: {LIBRARY_JSON}")

    with open(LIBRARY_JSON, "r") as f:
        records = json.load(f)

    # 1. Total records check
    total_records = len(records)
    print(f"Total records found: {total_records}")
    assert total_records == 2000, f"Expected 2000 records, got {total_records}"

    # 2. Unique IDs & Asset IDs
    obs_ids = [r["id"] for r in records]
    asset_ids = [r["asset_id"] for r in records]
    dr7objids = [r["dr7objid"] for r in records]

    assert len(set(obs_ids)) == 2000, "Duplicate observation IDs found!"
    assert len(set(asset_ids)) == 2000, "Duplicate asset IDs found!"
    assert len(set(dr7objids)) == 2000, "Duplicate dr7objids found!"
    print("✓ All 2,000 observation IDs, asset IDs, and DR7 object IDs are unique.")

    # 3. Image File Validation & Corruption Check
    missing_images = 0
    corrupt_images = 0

    for r in records:
        aid = r["asset_id"]
        lib_img_path = os.path.join(LIBRARY_IMAGES_DIR, f"{aid}.jpg")
        pub_img_path = os.path.join(FRONTEND_PUBLIC_IMAGES, f"{aid}.jpg")

        if not os.path.exists(lib_img_path) or not os.path.exists(pub_img_path):
            missing_images += 1
            continue

        try:
            with Image.open(pub_img_path) as img:
                img.verify()
        except Exception:
            corrupt_images += 1

    print(f"✓ Image audit: Missing={missing_images}, Corrupt={corrupt_images}")
    assert missing_images == 0, f"Found {missing_images} missing images!"
    assert corrupt_images == 0, f"Found {corrupt_images} corrupt images!"

    # 4. Field & Value Range Audit
    morphology_counts = {}
    confidence_dist = {">=90%": 0, "80-90%": 0, "<80%": 0}

    for r in records:
        # Required non-empty string fields
        assert r["id"].startswith("LIB-"), f"Invalid ID format: {r['id']}"
        assert r["broad_morphology"] in VALID_MORPHOLOGIES, f"Invalid morphology: {r['broad_morphology']}"
        assert r["priority"] in VALID_PRIORITIES, f"Invalid priority: {r['priority']}"
        assert len(r["explanation"]) > 10, f"Description too short or missing for {r['id']}"
        assert len(r["provenance"]) > 0, f"Provenance missing for {r['id']}"

        # Coordinate bounds
        assert 0.0 <= r["ra"] <= 360.0, f"RA out of bounds: {r['ra']}"
        assert -90.0 <= r["dec"] <= 90.0, f"DEC out of bounds: {r['dec']}"

        # Confidence bounds
        conf = r["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence out of bounds: {conf}"
        if conf >= 0.90:
            confidence_dist[">=90%"] += 1
        elif conf >= 0.80:
            confidence_dist["80-90%"] += 1
        else:
            confidence_dist["<80%"] += 1

        # Probability bounds
        for prob_key in ["p_smooth", "p_features", "p_edgeon", "p_spiral", "p_odd"]:
            val = r[prob_key]
            assert 0.0 <= val <= 1.0, f"{prob_key} out of bounds: {val}"

        morph = r["broad_morphology"]
        morphology_counts[morph] = morphology_counts.get(morph, 0) + 1

    print("\nMorphology Distribution:")
    for k, v in morphology_counts.items():
        print(f"  - {k}: {v}")

    print("\nConfidence Distribution:")
    for k, v in confidence_dist.items():
        print(f"  - {k}: {v}")

    print("\n" + "=" * 60)
    print("ALL VALIDATION ASSERTS PASSED CLEANLY (100% SCIENTIFIC INTEGRITY)")
    print("=" * 60)

if __name__ == "__main__":
    validate_library()
