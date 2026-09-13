import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ASTRA"
    assert data["ml_ready"] is True
    assert data["model_loaded"] is True
    assert data["domain_gate_loaded"] is True
    assert "domain_gate" in data["domain_gate_model_version"].lower()
    assert "v2" in data["domain_gate_model_version"].lower()
    assert "epoch10" in data["model_version"]
    assert data["device"] in ["mps", "cuda", "cpu"]
    assert "startup_duration_ms" in data

def test_production_model_is_v2_not_v1(client):
    from backend.app.config import settings
    assert settings.DOMAIN_GATE_PATH.endswith("domain_gate_v2_best.pt")
    assert not settings.DOMAIN_GATE_PATH.endswith("domain_gate_best.pt")
    assert os.path.exists(settings.DOMAIN_GATE_PATH)
    assert os.path.exists(os.path.join(settings.PROJECT_ROOT, "ml", "models", "domain_gate_best.pt")) # V1 preserved!
