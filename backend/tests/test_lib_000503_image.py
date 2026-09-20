import os
import json
import pytest

def test_lib_000503_canonical_record_and_asset():
    lib_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "data", "observationLibrary.json")
    assert os.path.exists(lib_path), "observationLibrary.json file must exist"

    with open(lib_path, "r") as f:
        data = json.load(f)

    # 1. Verify LIB-000503 exists in observationLibrary.json
    match = next((item for item in data if item.get("id") == "LIB-000503"), None)
    assert match is not None, "LIB-000503 record must exist in observationLibrary.json"

    # 2. Check metadata
    assert match["id"] == "LIB-000503"
    assert match["asset_id"] == 3954
    assert match["dr7objid"] == "587725039025193064"
    assert match["image_url"] == "/library/images/3954.jpg"

    # 3. Verify physical file exists under frontend/public
    public_img_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "library", "images", "3954.jpg")
    assert os.path.exists(public_img_path), f"Physical file must exist at {public_img_path}"
    assert os.path.getsize(public_img_path) > 0, "Image file must not be 0 bytes"
