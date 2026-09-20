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

# 8. Anomaly Grounding & Triage Math
def test_space_ai_what_is_an_anomaly():
    service = SpaceAIService()
    res = service.answer_question("What do we mean by anomaly?")
    assert res["scope"] in ("astra_product", "astronomy_general")
    assert "0.35" in res["answer"]
    assert "novelty" in res["answer"].lower()
    assert "not" in res["answer"].lower() and "alien" in res["answer"].lower()

def test_space_ai_target_followup_star():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIVE-20260920-STAR01",
        "predicted_object_type": "Star",
        "confidence": 0.92,
        "broad_morphology": "OTHER",
        "triage": {"priority": "MEDIUM", "anomaly_score": 0.55}
    }
    res = service.answer_question("Why is this a star?", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "LIVE-20260920-STAR01" in res["answer"]
    assert "Star" in res["answer"] or "point-source" in res["answer"].lower()

def test_space_ai_deep_analysis_auto_request():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIVE-20260920-GAL99",
        "predicted_object_type": "Galaxy",
        "confidence": 0.89,
        "broad_morphology": "SPIRAL",
        "gz2class": "SBb",
        "triage": {"priority": "HIGH", "anomaly_score": 0.78, "novelty_score": 0.80, "uncertainty_score": 0.70, "oddity_score": 0.85}
    }
    res = service.answer_question("Provide a detailed scientific explanation of observation LIVE-20260920-GAL99.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "LIVE-20260920-GAL99" in res["answer"]
    assert "SPIRAL" in res["answer"]
    assert "0.78" in res["answer"] or "HIGH" in res["answer"]

# 9. Exact User Phrase "more details" & Multi-Turn Conversation
def test_space_ai_exact_phrase_more_details():
    service = SpaceAIService()
    ctx = {
        "observation_id": "OBS-9FDBEE21",
        "predicted_object_type": "Galaxy",
        "confidence": 0.88,
        "broad_morphology": "SPIRAL",
        "triage": {"priority": "HIGH", "anomaly_score": 0.82, "novelty_score": 0.85, "uncertainty_score": 0.75, "oddity_score": 0.80}
    }
    res = service.answer_question("more details", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "OBS-9FDBEE21" in res["answer"]
    assert "I can help with astronomy" not in res["answer"]
    assert "Detailed Evidence Breakdown" in res["answer"] or "Triage" in res["answer"]

def test_space_ai_multi_turn_conversation_sequence():
    service = SpaceAIService()
    ctx = {
        "observation_id": "OBS-TEST-001",
        "predicted_object_type": "Galaxy",
        "confidence": 0.91,
        "broad_morphology": "SPIRAL",
        "gz2class": "Sc",
        "triage": {"priority": "CRITICAL", "anomaly_score": 0.92, "novelty_score": 0.94, "uncertainty_score": 0.88, "oddity_score": 0.90}
    }

    # TURN 1: Initial Deep Analysis Auto-Request
    res1 = service.answer_question("Provide a detailed scientific explanation of this observation.", observation_context=ctx)
    assert res1["scope"] == "observation_analysis"
    assert "OBS-TEST-001" in res1["answer"]

    # TURN 2: Follow-up "more details"
    history = [
        {"role": "user", "content": "Provide a detailed scientific explanation of this observation."},
        {"role": "assistant", "content": res1["answer"]}
    ]
    res2 = service.answer_question("more details", observation_context=ctx, conversation_history=history)
    assert res2["scope"] == "observation_analysis"
    assert "OBS-TEST-001" in res2["answer"]
    assert "I can help with astronomy, space science" not in res2["answer"]

    # TURN 3: Follow-up "why was it prioritized?"
    history.append({"role": "user", "content": "more details"})
    history.append({"role": "assistant", "content": res2["answer"]})
    res3 = service.answer_question("why was it prioritized?", observation_context=ctx, conversation_history=history)
    assert res3["scope"] == "observation_analysis"
    assert "OBS-TEST-001" in res3["answer"]

    # TURN 4: Follow-up "could it be a quasar?"
    history.append({"role": "user", "content": "why was it prioritized?"})
    history.append({"role": "assistant", "content": res3["answer"]})
    res4 = service.answer_question("could it be a quasar?", observation_context=ctx, conversation_history=history)
    assert res4["scope"] == "observation_analysis"
    assert "OBS-TEST-001" in res4["answer"]

    # TURN 5: Follow-up "what evidence would confirm that?"
    history.append({"role": "user", "content": "could it be a quasar?"})
    history.append({"role": "assistant", "content": res4["answer"]})
    res5 = service.answer_question("what evidence would confirm that?", observation_context=ctx, conversation_history=history)
    assert res5["scope"] == "observation_analysis"

    # TURN 6: General Astronomy "What is a neutron star?"
    history.append({"role": "user", "content": "what evidence would confirm that?"})
    history.append({"role": "assistant", "content": res5["answer"]})
    res6 = service.answer_question("What is a neutron star?", observation_context=ctx, conversation_history=history)
    assert res6["scope"] == "astronomy_general"
    assert "neutron star" in res6["answer"].lower()

    # TURN 7: Off-Topic "Who won the football match?"
    history.append({"role": "user", "content": "What is a neutron star?"})
    history.append({"role": "assistant", "content": res6["answer"]})
    res7 = service.answer_question("Who won the football match?", observation_context=ctx, conversation_history=history)
    assert res7["scope"] == "redirect"
    assert "astronomy" in res7["answer"].lower()

# PART 12 REGRESSION TESTS

# TEST 1 — STAR
def test_space_ai_part12_test1_star():
    service = SpaceAIService()
    ctx = {
        "observation_id": "TEST-STAR-01",
        "predicted_object_type": "STAR",
        "broad_morphology": "SMOOTH",
        "confidence": 0.94,
        "coordinates": None,
        "has_coordinates": False
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "STAR" in res["answer"]
    assert "Not applicable" in res["answer"]
    assert "0.000000" not in res["answer"]
    assert "Sky coordinates are not available" in res["answer"]

# TEST 2 — GALAXY
def test_space_ai_part12_test2_galaxy():
    service = SpaceAIService()
    ctx = {
        "observation_id": "TEST-GAL-01",
        "predicted_object_type": "GALAXY",
        "broad_morphology": "SPIRAL",
        "gz2class": "SBc",
        "confidence": 0.88,
        "coordinates": {"ra": 196.13354, "dec": -3.58839},
        "has_coordinates": True
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "GALAXY" in res["answer"]
    assert "SPIRAL" in res["answer"]
    assert "196.133540" in res["answer"]

# TEST 3 — NEBULA
def test_space_ai_part12_test3_nebula():
    service = SpaceAIService()
    ctx = {
        "observation_id": "TEST-NEB-01",
        "predicted_object_type": "NEBULA_CANDIDATE",
        "confidence": 0.82,
        "coordinates": None
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "NEBULA_CANDIDATE" in res["answer"]
    assert "Not applicable" in res["answer"]
    assert "0.000000" not in res["answer"]

# TEST 4 — AMBIGUOUS POINT SOURCE
def test_space_ai_part12_test4_ambiguous_point_source():
    service = SpaceAIService()
    ctx = {
        "observation_id": "TEST-AMB-01",
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "confidence": 0.55,
        "coordinates": None
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "AMBIGUOUS_POINT_SOURCE" in res["answer"]
    assert "Not applicable" in res["answer"]
    assert "0.000000" not in res["answer"]

# TEST 5 — USER UPLOAD WITHOUT COORDINATES
def test_space_ai_part12_test5_user_upload():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIVE-20260920-UPLOAD1",
        "source": "USER_UPLOAD",
        "predicted_object_type": "STAR",
        "coordinates": {"ra": 0.0, "dec": 0.0},
        "has_coordinates": False
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "0.000000" not in res["answer"]
    assert "Sky coordinates were not provided with this image" in res["answer"]

# TEST 6 — REAL LIBRARY OBSERVATION
def test_space_ai_part12_test6_real_library_observation():
    service = SpaceAIService()
    ctx = {
        "observation_id": "LIB-000503",
        "source": "LIBRARY",
        "object_type": "GALAXY",
        "predicted_object_type": "GALAXY",
        "broad_morphology": "SPIRAL",
        "gz2class": "SBb",
        "confidence": 0.91,
        "coordinates": {"ra": 196.13354, "dec": -3.58839},
        "has_coordinates": True,
        "triage": {"priority": "HIGH", "anomaly_score": 0.76}
    }
    res = service.answer_question("Explain this observation.", observation_context=ctx)
    assert res["scope"] == "observation_analysis"
    assert "LIB-000503" in res["answer"]
    assert "GALAXY" in res["answer"]
    assert "196.133540" in res["answer"]

# TEST 7 — FOLLOW-UP
def test_space_ai_part12_test7_followup():
    service = SpaceAIService()
    ctx = {
        "observation_id": "TEST-STAR-02",
        "predicted_object_type": "STAR",
        "confidence": 0.95
    }
    res1 = service.answer_question("Explain this observation.", observation_context=ctx)
    res2 = service.answer_question("More details.", observation_context=ctx)
    assert "TEST-STAR-02" in res2["answer"]
    assert "STAR" in res2["answer"]

# TEST 8 — COORDINATE QUESTION
def test_space_ai_part12_test8_coordinate_question():
    service = SpaceAIService()
    ctx_with = {
        "observation_id": "TEST-COORDS-YES",
        "coordinates": {"ra": 177.07516, "dec": -3.11701},
        "has_coordinates": True
    }
    res_with = service.answer_question("What are the coordinates?", observation_context=ctx_with)
    assert "177.075160" in res_with["answer"]

    ctx_without = {
        "observation_id": "TEST-COORDS-NO",
        "coordinates": None,
        "has_coordinates": False
    }
    res_without = service.answer_question("What are the coordinates?", observation_context=ctx_without)
    assert "0.000000" not in res_without["answer"]
    assert "not available" in res_without["answer"].lower()




