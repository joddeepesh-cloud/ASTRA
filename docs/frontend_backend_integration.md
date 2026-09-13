# ASTRA Phase 9 — Frontend ↔ FastAPI Integration & Real Scientific Analysis UX

This document details the production integration between the React frontend (`frontend/`) and the FastAPI backend (`backend/`) for real-time astronomical observation triage.

---

## 1. System Architecture Overview

```
                  +-----------------------------------+
                  |        USER / BROWSER             |
                  |     (ASTRA React Frontend)        |
                  +-----------------------------------+
                                    |
                    Client-Side Basic Validation
                  (Format: JPEG/PNG/WEBP, Max 10MB)
                                    |
                    POST /api/v1/triage (Multipart)
                                    v
                  +-----------------------------------+
                  |        FASTAPI BACKEND            |
                  |      (http://localhost:8000)      |
                  +-----------------------------------+
                                    |
                      GalaxyZooInference (PyTorch MPS)
                   (EfficientNet-B0 Latent 1280-d)
                                    |
                       ASTRATriageEngine Layer
                   (Centroid distances & attributes)
                                    v
                  +-----------------------------------+
                  |     REAL TRIAGE JSON RESPONSE     |
                  +-----------------------------------+
                                    |
                   Frontend Scientific UX Mapping
                 (Triage gauge, priority badge, HUD)
```

---

## 2. Environment & Configuration

### Frontend Base URL Configuration
The API client (`frontend/src/services/api.ts`) retrieves the backend base URL via Vite environment variables:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

### Environment Files
- `frontend/.env.example`:
  ```env
  VITE_API_BASE_URL=http://localhost:8000
  ```

---

## 3. Asynchronous Non-Blocking Backend Readiness

The top navigation bar (`frontend/src/components/TopBar.tsx`) polls `GET /api/v1/health` asynchronously upon mount with a 5-second timeout:

- **State `online`**: Displays `ML API ONLINE (device: mps, model: Epoch 10)`.
- **State `offline`**: Displays `LIVE ANALYSIS OFFLINE`.
- **Non-blocking guarantee**: The landing page and curated observation catalog render immediately without waiting for API response.

---

## 4. Research Mode Upload & Real Inference Flow

### Upload State Machine (`UploadDropzone.tsx`)
```
IDLE  --->  VALIDATING  --->  ANALYZING  --->  SUCCESS  (Real Triage UI)
  |             |                 |
  +-------------+-----------------+--------->  ERROR    (Honest Error Message)
```

1. **IDLE**: User drops or selects an image cutout (JPEG, PNG, WEBP).
2. **VALIDATING**: Client validates MIME type and file size (< 10 MB). Displays astronomy domain requirements banner.
3. **ANALYZING**: Sends `multipart/form-data` payload (`file`) to `POST /api/v1/triage` with an `AbortController` (15-second timeout).
4. **SUCCESS**: Maps exact backend JSON fields to UI visualization components.
5. **ERROR**: Renders honest error states (e.g. `ASTRA's analysis service is currently unavailable`). **No fake ML fallbacks, mock confidence values, or randomized fallback classes.**

---

## 5. Response Schema & Scientific UX Mapping

| FastAPI Field | Frontend Mapping / Visual Element | Example Value |
|---|---|---|
| `predicted_class` | Predicted Morphology Designation | `SMOOTH` |
| `class_confidence` | Primary Model Confidence Percentage | `0.925` (`92.5%`) |
| `class_probabilities` | Morphology Probability Bars (`ConfidenceBar`) | `{"SMOOTH": 0.925, ...}` |
| `scientific_attributes` | Attribute Head Predictions | `prob_smooth`, `prob_spiral`, `prob_odd` |
| `novelty_score` | Latent Centroid Euclidean Distance Gauge | `0.1555` |
| `uncertainty_score` | Classification Entropy Gauge | `0.1000` |
| `oddity_score` | Model Oddity Attribute Gauge | `0.1480` |
| `experimental_triage_score` | Primary ASTRA Triage Score | `0.1338` |
| `priority_level` | System Priority Badge (`PriorityBadge`) | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `explanation` | Deterministic Scientific Triage Text | Exists in returned JSON |
| `score_interpretation` | Mandatory Scientific Safety Disclaimer | Exists in returned JSON |
| `model_version` | Model Checkpoint Version Badge | `Epoch 10` |
| `inference_time_ms` | PyTorch Forward Pass Latency | `15.75 ms` |
| `total_triage_ms` | Full Pipeline Processing Latency | `15.87 ms` |

---

## 6. Scientific Safety UX & Domain Validation

### Domain Validation Architecture
- **Input Requirements Banner**: Communicates that uploaded imagery must represent astronomical observation cutouts (SDSS, HST, FITS cutouts).
- **Domain Gate Interface**: Cleanly structured via `DomainValidationGate` type to allow inserting a trained binary astronomy classifier in future phases.
- **Scientific Framing**: Results explicitly display the disclaimer:
  > *"ASTRA's triage score is an experimental prioritization heuristic for allocating scientific review attention. It is not a calibrated anomaly probability and does not establish the discovery of a new astronomical object."*

---

## 7. Live Upload vs Curated Mission Archive

- **Curated Mission Archive**: Pre-existing SDSS observation catalog items retained for mission demonstration.
- **Live Analysis**: Generated upon uploading user images.
  - Assigned temporary designation: `LIVE-YYYYMMDD-HHMMSS`.
  - Marked clearly with `LIVE UPLOAD ANALYSIS` badge.
  - Passes full `TriageResponse` context to `ObservationDetailPage` and `CopilotPage`.

---

## 8. Development & Verification Commands

### Start FastAPI Backend
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Start React Frontend
```bash
cd frontend
npm run dev
```

### Build Production Bundle
```bash
cd frontend
npm run build
```

### Backend Unit Tests
```bash
source .venv/bin/activate
PYTHONPATH=. pytest backend/tests
```

---

*Document created for ASTRA Phase 9 Integration.*
