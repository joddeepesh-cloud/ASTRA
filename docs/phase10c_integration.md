# ASTRA — Phase 10C: Astronomy Domain Gate Integration Documentation

This document details the architecture, upload pipeline workflow, domain decisions, API response structure, startup lifecycle, test validation, performance benchmarks, and scientific safety guidelines for Phase 10C.

---

## 1. System Architecture & Upload Pipeline Flow

In Phase 10C, the Astronomy Domain Gate model ([`ml/models/domain_gate_best.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/domain_gate_best.pt)) was integrated into the real FastAPI upload pipeline ([`backend/app/services/ml_service.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/app/services/ml_service.py)).

The Domain Gate MUST execute BEFORE downstream Galaxy Zoo morphology inference and triage scoring.

```text
                  USER UPLOAD (POST /api/v1/triage)
                                 │
                                 ▼
                     CLIENT-SIDE VALIDATION
                                 │
                                 ▼
                     FASTAPI UPLOAD HANDLER
                                 │
                                 ▼
                    PIL IMAGE DECODING (RGB)
                                 │
                                 ▼
               [ DOMAIN GATE (MobileNetV3-Small) ]
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
P(Astro) >= 0.80       0.20 < P(Astro) < 0.80     P(Astro) <= 0.20
   (COMPATIBLE)               (UNCERTAIN)            (INCOMPATIBLE)
         │                       │                       │
         ▼                       ▼                       ▼
  Run Galaxy Zoo          SKIP Morphology        REJECT UPLOAD
Morphology & Triage        Return Safe            SKIP Morphology
         │                 Uncertainty            Return Safe
         ▼                  Response               Rejection
  Full Scientific                │                      │
  Triage Response                ▼                      ▼
                               Frontend               Frontend
                               Uncertain              Rejection
                                  UI                     UI
```

---

## 2. Startup Lifecycle & Lifespan Warmup

1. **FastAPI Lifespan Startup**:
   - `MLService.initialize()` is called once during FastAPI startup.
   - Loads `DomainGate` model (`~6.1 MB`, `1.52M` parameters) from `settings.DOMAIN_GATE_PATH`.
   - Loads `GalaxyZooInference` (`best_model.pt`) and `ASTRATriageEngine` (`triage_reference.json`).
2. **PyTorch Warmup**:
   - A dummy 224x224 RGB image is passed through both `DomainGate.predict()` and `ASTRATriageEngine.triage_single_image()`.
   - Compiles PyTorch MPS/CUDA shaders before servicing real requests.
   - Warmup duration recorded in `HealthResponse.startup_duration_ms` (~753.65 ms).

---

## 3. Policy & Decision Thresholds

- **`P(ASTRONOMICAL) >= 0.80` $\rightarrow$ `COMPATIBLE`**:
  Domain validation passed. Downstream Galaxy Zoo morphology and triage analysis is executed.
- **`P(ASTRONOMICAL) <= 0.20` $\rightarrow$ `INCOMPATIBLE`**:
  Upload rejected. Galaxy Zoo classifier and OOD scoring are skipped.
  Explanation: `"This image does not appear to contain astronomical observation data. No astronomical classification was performed."`
- **`0.20 < P(ASTRONOMICAL) < 0.80` $\rightarrow$ `UNCERTAIN`**:
  Ambiguous image rejected from confident classification. Galaxy Zoo classifier skipped.
  Explanation: `"This image could not be confidently verified as compatible with ASTRA's astronomical observation domain. No astronomical classification was performed."`

---

## 4. Response Schemas

### GET `/api/v1/health`
```json
{
  "status": "ok",
  "service": "ASTRA",
  "ml_ready": true,
  "model_loaded": true,
  "domain_gate_loaded": true,
  "model_version": "galaxy-zoo-efficientnet-b0-epoch10",
  "domain_gate_model_version": "mobilenet_v3_small_domain_gate_epoch15",
  "device": "mps",
  "backend_version": "1.0.0",
  "startup_duration_ms": 753.65
}
```

### POST `/api/v1/triage` (COMPATIBLE Example)
```json
{
  "domain_validation": {
    "probability_astronomical": 1.0,
    "probability_non_astronomical": 0.0,
    "decision": "COMPATIBLE",
    "model_version": "mobilenet_v3_small_domain_gate_epoch15",
    "inference_time_ms": 6.10
  },
  "predicted_class": "SMOOTH",
  "class_confidence": 0.9252,
  "class_probabilities": {
    "SMOOTH": 0.9252,
    "EDGE_ON": 0.0035,
    "FEATURED_DISK": 0.0621,
    "SPIRAL": 0.0092
  },
  "scientific_attributes": {
    "prob_smooth": 0.9252,
    "prob_features": 0.0748,
    "prob_edgeon": 0.0035,
    "prob_spiral": 0.0092,
    "prob_bar": 0.0150,
    "prob_odd": 0.0410
  },
  "experimental_triage_score": 0.1245,
  "priority_level": "LOW",
  "explanation": "Domain validation passed. Proceeding with astronomical morphology and triage analysis. Observation is consistent with learned reference distribution.",
  "model_version": "galaxy-zoo-efficientnet-b0-epoch10",
  "inference_time_ms": 15.82,
  "total_triage_ms": 22.04,
  "score_interpretation": "Experimental prioritization heuristic; not a calibrated anomaly probability."
}
```

### POST `/api/v1/triage` (INCOMPATIBLE Example)
```json
{
  "domain_validation": {
    "probability_astronomical": 0.0,
    "probability_non_astronomical": 1.0,
    "decision": "INCOMPATIBLE",
    "model_version": "mobilenet_v3_small_domain_gate_epoch15",
    "inference_time_ms": 5.81
  },
  "explanation": "This image does not appear to contain astronomical observation data. No astronomical classification was performed.",
  "model_version": "galaxy-zoo-efficientnet-b0-epoch10",
  "inference_time_ms": 5.81,
  "total_triage_ms": 6.03,
  "score_interpretation": "Domain validation failed; image is outside ASTRA astronomical observation domain."
}
```

---

## 5. Measured Performance Benchmarks

From [`scratch/benchmark_phase10c.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/scratch/benchmark_phase10c.py):

| Category | Domain Decision | P(Astro) | Domain Gate Mean (ms) | Total Triage Mean (ms) | HTTP API Mean (ms) | HTTP API P95 (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Known Galaxy Zoo (`20027.jpg`)** | `COMPATIBLE` | `1.0000` | 6.10 ms | 22.04 ms | 22.94 ms | 23.78 ms |
| **Non-Astronomy Image (`non_astro_0001.jpg`)** | `INCOMPATIBLE` | `0.0000` | 5.81 ms | 6.03 ms | 6.83 ms | 7.35 ms |
| **Ambiguous Image (`ambiguous_001.jpg`)** | `INCOMPATIBLE` | `0.0000` | 5.77 ms | 5.98 ms | 6.77 ms | 7.01 ms |

---

## 6. Scientific Safety & Guardrails

- Pre-filtering prevents non-astronomical images (people, cars, memes, landscapes) from generating false galaxy classifications or anomaly scores.
- Safety messages avoid inventing detected objects (never says "AI detected a dog" or "100% certain").
- Deterministic behavior: Galaxy Zoo image `20027.jpg` produces identical classification (`SMOOTH`, ~0.925 confidence) before and after domain gate integration.
