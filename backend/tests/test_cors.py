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

def test_cors_cloudflare_pages_current_deployment_allowed(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://f306b7ae.astra-3ll.pages.dev",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://f306b7ae.astra-3ll.pages.dev"

def test_cors_cloudflare_pages_wildcard_preview_allowed(client):
    response = client.options(
        "/api/v1/triage",
        headers={
            "Origin": "https://randomhash99.astra-3ll.pages.dev",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://randomhash99.astra-3ll.pages.dev"

def test_cors_evil_pages_dev_rejected(client):
    # GET request with disallowed origin returns HTTP 200 with no Access-Control-Allow-Origin header
    res_get = client.get("/api/v1/health", headers={"Origin": "https://evil.pages.dev"})
    assert res_get.headers.get("access-control-allow-origin") is None
    # Preflight OPTIONS with disallowed origin is rejected
    res_opt = client.options("/api/v1/health", headers={"Origin": "https://evil.pages.dev", "Access-Control-Request-Method": "GET"})
    assert res_opt.headers.get("access-control-allow-origin") is None

def test_cors_evil_com_rejected(client):
    # GET request with disallowed origin returns HTTP 200 with no Access-Control-Allow-Origin header
    res_get = client.get("/api/v1/health", headers={"Origin": "https://evil.com"})
    assert res_get.headers.get("access-control-allow-origin") is None
    # Preflight OPTIONS with disallowed origin is rejected
    res_opt = client.options("/api/v1/health", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"})
    assert res_opt.headers.get("access-control-allow-origin") is None



