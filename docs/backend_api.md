# ASTRA — FastAPI Backend API & ML Service Specification

This document details the production-ready FastAPI backend architecture, API endpoints, request/response schemas, startup lifecycle, CORS configuration, performance benchmarks, and scientific safety guidelines.

---

## 1. System Architecture

The backend exposes the trained **ASTRA Galaxy Zoo Multi-Head CNN** ([`ml/models/best_model.pt`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/models/best_model.pt)) and the **ASTRA Scientific Triage Engine** ([`ml/src/triage.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/triage.py)) to web clients via HTTP REST endpoints.

```text
[ Client (React Frontend / cURL) ]
             │
             ▼
[ FastAPI Application (backend/app/main.py) ]
             │
             ├─► GET  /api/v1/health  (Readiness Telemetry)
             └─► POST /api/v1/triage  (Multipart Image Upload)
                     │
                     ▼
         [ MLService (Singleton) ]
                     │
                     ├─► 1. DomainGate (domain_gate_best.pt)
                     │       │
                     │       ├─► P(Astro) <= 0.20 -> INCOMPATIBLE (Reject)
                     │       ├─► 0.20 < P < 0.80 -> UNCERTAIN (Safe Response)
                     │       └─► P(Astro) >= 0.80 -> COMPATIBLE
                     │                                 │
                     │                                 ▼
                     ├─► 2. GalaxyZooInference (best_model.pt)
                     └─► 3. ASTRATriageEngine (triage_reference.json)
                             │
                             ▼
                 [ Real Structured Triage Response ]
```

---

## 2. Model Lifecycle & Startup Warmup

1. **Lifespan Initialization**: When Uvicorn starts the application, FastAPI's `lifespan` context manager invokes `ml_service.initialize()`.
2. **Single Load Execution**:
   - `DomainGate` loads MobileNetV3-Small weights (`6.10 MB`) into RAM/VRAM once.
   - `GalaxyZooInference` loads EfficientNet-B0 weights (`51.99 MB`) into RAM/VRAM once.
   - `ASTRATriageEngine` loads the training-only reference artifact (`142.96 KB`) into memory once.
3. **Automatic Device Selection**: Auto-detects `CUDA` $\rightarrow$ `Apple Silicon MPS` $\rightarrow$ `CPU`.
4. **Warmup Pass**: An in-memory 224x224 RGB image is passed through `DomainGate` and `ASTRATriageEngine` during startup to compile PyTorch MPS Metal shaders / CUDA kernels. The first real user request pays **zero** shader compilation penalty.

---

## 3. Environment Variables & Configuration

Configured via `backend/app/config.py` (or `.env` file):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin for frontend requests |
| `API_V1_STR` | `/api/v1` | Base API route prefix |
| `MODEL_PATH` | `<PROJECT_ROOT>/ml/models/best_model.pt` | Path to production morphology model weights |
| `DOMAIN_GATE_PATH` | `<PROJECT_ROOT>/ml/models/domain_gate_v2_best.pt` | Path to production domain gate weights |
| `TRIAGE_REF_PATH` | `<PROJECT_ROOT>/ml/artifacts/triage_reference.json` | Path to training reference artifact |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB) | Maximum permitted image upload size |
| `ALLOWED_IMAGE_TYPES` | `{"image/jpeg", "image/png", "image/webp"}` | Permitted image MIME types |

---

## 4. API Endpoint Specifications

### 4.1 Health Check Endpoint
- **URL**: `GET /api/v1/health`
- **Summary**: Retrieve service readiness and ML model status. Does **not** execute model inference.
- **Response Headers**: `200 OK`

```json
{
  "status": "ok",
  "service": "ASTRA",
  "ml_ready": true,
  "model_loaded": true,
  "domain_gate_loaded": true,
  "model_version": "galaxy-zoo-efficientnet-b0-epoch10",
  "domain_gate_model_version": "mobilenet_v3_small_domain_gate_v2_epoch15",
  "device": "mps",
  "backend_version": "1.0.0",
  "startup_duration_ms": 753.65
}
```

---

### 4.2 Scientific Triage Endpoint
- **URL**: `POST /api/v1/triage`
- **Content-Type**: `multipart/form-data`
- **Parameters**: `file` (Binary image file payload: JPEG, PNG, or WEBP)
- **Response Headers**: `200 OK`

#### Example Success Response (`200 OK`)
```json
{
  "predicted_class": "SMOOTH",
  "class_confidence": 0.9955,
  "class_probabilities": {
    "SMOOTH": 0.9955,
    "EDGE_ON": 0.0012,
    "FEATURED_DISK": 0.0028,
    "SPIRAL": 0.0005
  },
  "scientific_attributes": {
    "prob_smooth": 0.9955,
    "prob_features": 0.0045,
    "prob_edgeon": 0.0012,
    "prob_spiral": 0.0005,
    "prob_bar": 0.0010,
    "prob_odd": 0.0783
  },
  "raw_embedding_distance": 0.3208,
  "raw_pred_class_distance": 0.3208,
  "nearest_reference_class": "SMOOTH",
  "novelty_score": 0.1528,
  "classification_entropy_bits": 0.0452,
  "uncertainty_score": 0.0060,
  "oddity_score": 0.0783,
  "experimental_triage_score": 0.0791,
  "priority_level": "LOW",
  "explanation": "Observation is consistent with the learned morphology distribution and exhibits low triage priority.",
  "model_version": "Epoch 10",
  "inference_time_ms": 15.615,
  "total_triage_ms": 15.75,
  "score_interpretation": "Experimental prioritization heuristic; not a calibrated anomaly probability."
}
```

#### Error Responses
- **HTTP 400 Bad Request** (Invalid image / unsupported format):
  ```json
  {
    "error": "unsupported_format",
    "message": "Only JPEG, PNG, and WEBP image formats are supported."
  }
  ```
- **HTTP 413 Payload Too Large** (File size $> 10$ MB):
  ```json
  {
    "error": "file_too_large",
    "message": "Uploaded file exceeds maximum allowed size of 10 MB."
  }
  ```

---

## 5. Measured Performance Benchmarks

From [`ml/artifacts/backend_latency.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/artifacts/backend_latency.json) and [`docs/backend_performance.md`](file:///Users/deepeshjoshi/Desktop/ASTRA/docs/backend_performance.md):

- **Backend Startup Duration**: **`371.02 ms`** (< 0.4 seconds)
- **Health Endpoint Response Latency**: **`1.12 ms`**
- **First Post-Startup Triage Request Latency**: **`22.72 ms`**
- **Warm 30-Request Triage API Mean Latency**: **`16.92 ms`**
  - *Warm Median*: `16.86 ms`
  - *Warm P95*: `17.51 ms`
  - *Min*: `16.27 ms` | *Max*: `17.52 ms`

---

## 6. Local Server Execution Commands

### Activate Environment & Start Server
```bash
cd /Users/deepeshjoshi/Desktop/ASTRA
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Test Health Endpoint via cURL
```bash
curl http://localhost:8000/api/v1/health
```

### Test Triage Endpoint via cURL
```bash
curl -X POST "http://localhost:8000/api/v1/triage" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ml/data/processed/galaxy_zoo/images/20027.jpg"
```

---

## 7. Interactive API Documentation

Interactive Swagger UI and OpenAPI documentation automatically generated by FastAPI:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 8. Scientific Safety & Disclaimer

> [!IMPORTANT]
> ASTRA API responses strictly describe output metrics as experimental triage scores intended to prioritize observations for human scientific review. The service **never** claims "anomaly confirmation", "new discovery", or "epistemic certainty".
