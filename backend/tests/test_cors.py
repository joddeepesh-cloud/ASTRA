import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_cors_health_origin_header(client):
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5176"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5176"

def test_cors_triage_options_preflight(client):
    response = client.options(
        "/api/v1/triage",
        headers={
            "Origin": "http://localhost:5176",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5176"
    assert "POST" in response.headers.get("access-control-allow-methods", "")

def test_cors_disallowed_origin(client):
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://malicious-site.com"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None
