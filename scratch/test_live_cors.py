import subprocess
import time
import requests
import os

print("=" * 60)
print("ASTRA CORS LIVE HTTP TEST")
print("=" * 60)

# Start Uvicorn backend on port 8000
proc = subprocess.Popen(
    ["uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd="/Users/deepeshjoshi/Desktop/ASTRA",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3) # Allow startup + PyTorch warmup

try:
    # 1. Test GET /api/v1/health with Origin: http://localhost:5176
    res_health = requests.get(
        "http://127.0.0.1:8000/api/v1/health",
        headers={"Origin": "http://localhost:5176"}
    )
    print(f"GET /api/v1/health Status: {res_health.status_code}")
    print(f"Access-Control-Allow-Origin: {res_health.headers.get('Access-Control-Allow-Origin')}")
    assert res_health.status_code == 200
    assert res_health.headers.get("Access-Control-Allow-Origin") == "http://localhost:5176"

    # 2. Test OPTIONS /api/v1/triage preflight with Origin: http://localhost:5176
    res_options = requests.options(
        "http://127.0.0.1:8000/api/v1/triage",
        headers={
            "Origin": "http://localhost:5176",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    print(f"OPTIONS /api/v1/triage Status: {res_options.status_code}")
    print(f"Access-Control-Allow-Origin: {res_options.headers.get('Access-Control-Allow-Origin')}")
    print(f"Access-Control-Allow-Methods: {res_options.headers.get('Access-Control-Allow-Methods')}")
    assert res_options.status_code == 200
    assert res_options.headers.get("Access-Control-Allow-Origin") == "http://localhost:5176"

    # 3. Test POST /api/v1/triage with astronomy image & Origin: http://localhost:5176
    astro_path = "/Users/deepeshjoshi/Desktop/ASTRA/ml/data/demo/astronomy_galaxy_smooth.jpg"
    with open(astro_path, "rb") as f:
        res_astro = requests.post(
            "http://127.0.0.1:8000/api/v1/triage",
            files={"file": ("astronomy_galaxy_smooth.jpg", f, "image/jpeg")},
            headers={"Origin": "http://localhost:5176"}
        )
    print(f"POST /api/v1/triage (Astronomy) Status: {res_astro.status_code}")
    print(f"Access-Control-Allow-Origin: {res_astro.headers.get('Access-Control-Allow-Origin')}")
    astro_data = res_astro.json()
    print(f"Domain Decision: {astro_data.get('domain_validation', {}).get('decision')}")
    print(f"Predicted Class: {astro_data.get('predicted_class')}")
    assert res_astro.status_code == 200
    assert res_astro.headers.get("Access-Control-Allow-Origin") == "http://localhost:5176"
    assert astro_data.get("domain_validation", {}).get("decision") == "COMPATIBLE"

    # 4. Test POST /api/v1/triage with non-astronomy image & Origin: http://localhost:5176
    non_astro_path = "/Users/deepeshjoshi/Desktop/ASTRA/ml/data/demo/non_astronomy_terrestrial.jpg"
    with open(non_astro_path, "rb") as f:
        res_non_astro = requests.post(
            "http://127.0.0.1:8000/api/v1/triage",
            files={"file": ("non_astronomy_terrestrial.jpg", f, "image/jpeg")},
            headers={"Origin": "http://localhost:5176"}
        )
    print(f"POST /api/v1/triage (Non-Astronomy) Status: {res_non_astro.status_code}")
    print(f"Access-Control-Allow-Origin: {res_non_astro.headers.get('Access-Control-Allow-Origin')}")
    non_astro_data = res_non_astro.json()
    print(f"Domain Decision: {non_astro_data.get('domain_validation', {}).get('decision')}")
    print(f"Predicted Class: {non_astro_data.get('predicted_class')}")
    assert res_non_astro.status_code == 200
    assert res_non_astro.headers.get("Access-Control-Allow-Origin") == "http://localhost:5176"
    assert non_astro_data.get("domain_validation", {}).get("decision") == "INCOMPATIBLE"
    assert non_astro_data.get("predicted_class") is None

    print("=" * 60)
    print("ALL LIVE CORS TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
finally:
    proc.terminate()
    proc.wait()
