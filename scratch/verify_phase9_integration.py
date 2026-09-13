import os
import json
from fastapi.testclient import TestClient
from backend.app.main import app

def verify_direct_backend():
    print("=== Direct Backend Test via TestClient ===")
    image_path = "ml/data/processed/galaxy_zoo/images/20027.jpg"
    assert os.path.exists(image_path), f"Image missing: {image_path}"

    with TestClient(app) as client:
        # 1. Health check
        health_resp = client.get("/api/v1/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        print("Health Check Response:")
        print(json.dumps(health_resp.json(), indent=2))

        # 2. Triage image
        with open(image_path, "rb") as f:
            response = client.post(
                "/api/v1/triage",
                files={"file": ("20027.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print("\nDirect Backend Triage Response for 20027.jpg:")
        print(json.dumps(data, indent=2))

        print("\nVerified key fields:")
        print(f"  predicted_class:           {data['predicted_class']}")
        print(f"  class_confidence:          {data['class_confidence']}")
        print(f"  novelty_score:             {data['novelty_score']}")
        print(f"  uncertainty_score:         {data['uncertainty_score']}")
        print(f"  oddity_score:              {data['oddity_score']}")
        print(f"  experimental_triage_score: {data['experimental_triage_score']}")
        print(f"  priority_level:            {data['priority_level']}")
        print(f"  total_triage_ms:           {data['total_triage_ms']} ms")
        return data

if __name__ == "__main__":
    verify_direct_backend()
