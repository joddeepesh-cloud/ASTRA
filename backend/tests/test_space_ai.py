import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.space_ai_service import SpaceAIService

client = TestClient(app)

# 1. Greetings
def test_space_ai_hi_greeting():
    service = SpaceAIService()
    res = service.answer_question("hi")
    assert res["scope"] == "greeting"
    assert "hello! i am astra space help ai" in res["answer"].lower()

# 2. General Astronomy Questions (without context)
def test_space_ai_general_black_hole():
    service = SpaceAIService()
    res = service.answer_question("What is a black hole?")
    assert res["scope"] == "astronomy_general"
    assert "spacetime" in res["answer"].lower() or "gravity" in res["answer"].lower()

def test_space_ai_general_supernova():
    service = SpaceAIService()
    res = service.answer_question("What causes a supernova?")
    assert res["scope"] == "astronomy_general"
    assert "supernova" in res["answer"].lower()

def test_space_ai_general_mars_red():
    service = SpaceAIService()
    res = service.answer_question("Why does Mars look red?")
    assert res["scope"] == "astronomy_general"
    assert "iron" in res["answer"].lower() or "mars" in res["answer"].lower()

def test_space_ai_general_gravitational_lensing():
    service = SpaceAIService()
    res = service.answer_question("What is gravitational lensing?")
    assert res["scope"] == "astronomy_general"
    assert "lensing" in res["answer"].lower() or "gravity" in res["answer"].lower()

def test_space_ai_general_exoplanets():
    service = SpaceAIService()
    res = service.answer_question("How do astronomers detect exoplanets?")
    assert res["scope"] == "astronomy_general"
    assert "transit" in res["answer"].lower() or "radial velocity" in res["answer"].lower()

def test_space_ai_general_redshift():
    service = SpaceAIService()
    res = service.answer_question("What does redshift tell us?")
    assert res["scope"] == "astronomy_general"
    assert "redshift" in res["answer"].lower()

def test_space_ai_general_spectrograph():
    service = SpaceAIService()
    res = service.answer_question("How does a spectrograph work?")
    assert res["scope"] == "astronomy_general"
    assert "wavelength" in res["answer"].lower() or "spectrum" in res["answer"].lower()

# 3. ASTRA Product Questions
def test_space_ai_astra_how_it_works():
    service = SpaceAIService()
    res = service.answer_question("How does ASTRA work?")
    assert res["scope"] == "astra_product"
    assert "pipeline" in res["answer"].lower() or "triage" in res["answer"].lower()

def test_space_ai_astra_domain_gate():
    service = SpaceAIService()
    res = service.answer_question("What does the domain gate do?")
    assert res["scope"] == "astra_product"
    assert "validation" in res["answer"].lower() or "domain" in res["answer"].lower()

def test_space_ai_astra_triage_score():
    service = SpaceAIService()
    res = service.answer_question("Explain the triage score calculation")
    assert res["scope"] == "astra_product"
    assert "0.35" in res["answer"] or "novelty" in res["answer"].lower()

def test_space_ai_astra_discovery_caution():
    service = SpaceAIService()
    res = service.answer_question("Why doesn't ASTRA call this a discovery?")
    assert res["scope"] == "astra_product"
    assert "prioritization" in res["answer"].lower() or "not a discovery" in res["answer"].lower()

# 4. Observation-Aware Questions
def test_space_ai_observation_prioritized_with_context():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIB-000042",
        "broad_morphology": "SPIRAL",
        "confidence": 0.85,
        "triage": {"priority": "HIGH", "anomaly_score": 0.72}
    }
    res = service.answer_question("Why was this observation prioritized?", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "LIB-000042" in res["answer"]
    assert "HIGH" in res["answer"]

def test_space_ai_observation_priority_high():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIB-000100",
        "broad_morphology": "EDGE_ON",
        "triage": {"priority": "CRITICAL", "anomaly_score": 0.88, "novelty_score": 0.90, "uncertainty_score": 0.80, "oddity_score": 0.95}
    }
    res = service.answer_question("Why is this CRITICAL priority?", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "LIB-000100" in res["answer"]

def test_space_ai_observation_without_context():
    service = SpaceAIService()
    res = service.answer_question("Why was this observation prioritized?", observation_context=None)
    assert res["scope"] == "observation_analysis"
    assert "active observation payload" in res["answer"].lower() or "select an item" in res["answer"].lower()

# 5. CONTEXT OPTIONALITY: General question WITH observation selected
def test_space_ai_general_question_with_observation_context():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIB-000042",
        "broad_morphology": "SPIRAL",
        "confidence": 0.85,
        "triage": {"priority": "HIGH", "anomaly_score": 0.72}
    }
    # User asks a general question while Galaxy X is selected
    res = service.answer_question("What is a black hole?", observation_context=ctx)
    assert res["scope"] == "astronomy_general"
    assert "black hole" in res["answer"].lower() or "spacetime" in res["answer"].lower()
    # It MUST answer the black hole question directly without forcing target analysis
    assert "LIB-000042" not in res["answer"]

# 6. Off-Topic Filtering & Redirects
def test_space_ai_off_topic_fifa():
    service = SpaceAIService()
    res = service.answer_question("Who won the FIFA match?")
    assert res["scope"] == "redirect"
    assert "astronomy" in res["answer"].lower()

def test_space_ai_off_topic_python():
    service = SpaceAIService()
    res = service.answer_question("Write a Python script")
    assert res["scope"] == "redirect"

def test_space_ai_off_topic_recipe():
    service = SpaceAIService()
    res = service.answer_question("Give me a pasta recipe")
    assert res["scope"] == "redirect"

# 7. Endpoint POST /api/v1/space-ai Verification
def test_space_ai_endpoint():
    payload = {
        "question": "What is a spiral galaxy?",
        "observation_context": None
    }
    response = client.post("/api/v1/space-ai", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "astronomy_general"
    assert "spiral" in data["answer"].lower()

