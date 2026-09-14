#!/usr/bin/env python3
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.space_ai_router import (
    SpaceAIRouter, INTENT_GREETING, INTENT_OFF_TOPIC, INTENT_ASTRONOMY_GENERAL,
    INTENT_ASTRA_PRODUCT, INTENT_OBSERVATION_ANALYSIS, INTENT_UNSUPPORTED
)

# Acceptance Test Matrix (30 Representative Queries)
TEST_CASES = [
    # GREETINGS (with and without observation context)
    ("hi", INTENT_GREETING),
    ("hello", INTENT_GREETING),
    ("hey", INTENT_GREETING),
    ("good morning", INTENT_GREETING),
    ("who are you?", INTENT_GREETING),
    ("what can you do?", INTENT_GREETING),

    # OFF-TOPIC (with and without observation context)
    ("who won fifa?", INTENT_OFF_TOPIC),
    ("write python code to sort an array", INTENT_OFF_TOPIC),
    ("what is the best phone to buy?", INTENT_OFF_TOPIC),
    ("who is the president of India?", INTENT_OFF_TOPIC),
    ("tell me a joke", INTENT_OFF_TOPIC),
    ("what is the weather today?", INTENT_OFF_TOPIC),
    ("how to make a pizza", INTENT_OFF_TOPIC),

    # GENERAL ASTRONOMY
    ("what is a spiral galaxy?", INTENT_ASTRONOMY_GENERAL),
    ("what is a nebula?", INTENT_ASTRONOMY_GENERAL),
    ("what does redshift mean?", INTENT_ASTRONOMY_GENERAL),
    ("what is an elliptical galaxy?", INTENT_ASTRONOMY_GENERAL),
    ("what is an edge-on galaxy?", INTENT_ASTRONOMY_GENERAL),
    ("how do stars form?", INTENT_ASTRONOMY_GENERAL),

    # ASTRA PRODUCT / PIPELINE
    ("how does ASTRA work?", INTENT_ASTRA_PRODUCT),
    ("what does the semantic gate do?", INTENT_ASTRA_PRODUCT),
    ("why does ASTRA use a domain gate?", INTENT_ASTRA_PRODUCT),
    ("what is the triage score?", INTENT_ASTRA_PRODUCT),
    ("how does the observation library work?", INTENT_ASTRA_PRODUCT),

    # OBSERVATION ANALYSIS
    ("why was this observation prioritized?", INTENT_OBSERVATION_ANALYSIS),
    ("what morphology did ASTRA predict for this image?", INTENT_OBSERVATION_ANALYSIS),
    ("why is this observation interesting?", INTENT_OBSERVATION_ANALYSIS),
    ("explain the unusual features in this observation", INTENT_OBSERVATION_ANALYSIS),
    ("why is the triage score high for this target?", INTENT_OBSERVATION_ANALYSIS),
    ("what are the ra and dec coordinates of this observation?", INTENT_OBSERVATION_ANALYSIS),
]

def run_matrix():
    router = SpaceAIRouter()
    passed = 0
    total = len(TEST_CASES)

    print("=" * 80)
    print("RUNNING ASTRA SPACE HELP AI SEMANTIC INTENT ROUTER TEST MATRIX")
    print("=" * 80)

    for query, expected in TEST_CASES:
        res = router.classify_intent(query)
        predicted = res["intent"]
        is_pass = predicted == expected
        if is_pass:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"[{status}] Query: '{query}'")
        print(f"       Expected: {expected} | Predicted: {predicted} (Reason: {res['reason']})\n")

    print("=" * 80)
    print(f"RESULT: {passed}/{total} Passed ({passed/total*100:.1f}%)")
    print("=" * 80)

    if passed < total:
        sys.exit(1)

if __name__ == "__main__":
    run_matrix()
