# ASTRA — Production Deployment Audit Report

**Date**: September 20, 2026  
**Git Commit**: `b46b270` (`main` branch)  
**Repository**: `https://github.com/joddeepesh-cloud/ASTRA.git`  
**Status**: Verified Stable — Zero ML/Scientific Logic Modifications  

---

## 1. Overview & Repository Architecture

ASTRA is an astronomical observation anomaly detection and scientific triage application combining multi-stage deep learning (Universal Semantic Gate, MobileNetV3 Domain Gate V2, OpenCLIP Zero-Shot Object Classifier, EfficientNet-B0 Galaxy Zoo Morphology Model) with background multi-modal astronomical catalog enrichment (Gaia DR3, SDSS DR16, ALLWISE, TESS, NASA Exoplanet Archive).

### Repository Directory Structure
```
ASTRA/
├── frontend/                  # React 18 / Vite SPA Frontend
│   ├── public/                # Static assets & Curated Observation Library images
│   ├── src/                   # Components, Views, Hooks, Storage (IndexedDB)
│   ├── package.json           # Frontend dependencies & build scripts
│   └── vite.config.ts         # Vite build configuration
├── backend/                   # FastAPI Backend Service
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint, lifespan startup, router
│   │   ├── config.py          # Environment settings & Pydantic config
│   │   ├── schemas.py         # Request/Response Pydantic models
│   │   ├── dependencies.py    # FastAPI service dependency injection
│   │   └── services/          # MLService, SpaceAIService, EvidenceWorker, Stores
│   └── tests/                 # 127 automated unit tests
├── ml/                        # Machine Learning Pipeline
│   ├── models/                # Production model weights
│   │   ├── best_model.pt      # Galaxy Zoo EfficientNet-B0 (~15.4 MB)
│   │   └── domain_gate_v2_best.pt # Domain Gate V2 MobileNetV3 (~6.1 MB)
│   ├── src/                   # ML inference engines
│   │   ├── semantic_gate.py   # Universal Semantic Gate (OpenCLIP ViT-B/32)
│   │   ├── domain_gate.py     # Domain Gate V2
│   │   ├── object_classifier.py # Object Identification Engine
│   │   ├── dataset.py         # Preprocessing & Transforms
│   │   └── triage.py          # Scientific Triage Engine & Scoring
│   └── data/                  # Reference embeddings & metadata
├── docs/                      # Deployment documentation & audit reports
├── requirements.txt           # Backend Python dependencies
├── README.md                  # Project overview
└── .gitignore                 # Git exclusions
```

---

## 2. Component Architecture Details

### Frontend Architecture
- **Framework**: React 18, Vite 5, Tailwind CSS, Lucide Icons
- **State & Storage Architecture**:
  - Browser-side `IndexedDB` (`astra-image-store`) for full user-uploaded image persistence across browser sessions.
  - Custom state management for Anomaly Queue (pinned observations, status, notes), Analysis History, Dossier selection, Space Help AI grounded chat context.
  - Zero external state server requirements; all historical observation metadata & images reconstruct client-side.
- **Build Output**: Static HTML, JS, CSS bundle produced via `npm run build` in `frontend/dist/`.
- **Environment Configuration**: `VITE_API_BASE_URL` specifies the production backend base URL (`https://...`).

### Backend Architecture
- **Framework**: FastAPI with ASGI server (Uvicorn / Gunicorn with Uvicorn workers).
- **Process Model**: Single warm process per worker instance (1 worker recommended for production CPU/RAM footprint).
- **Lifespan Initialization**: Models are loaded strictly **once** during FastAPI `lifespan` application startup before any HTTP requests are accepted:
  1. Load application configuration (`backend/app/config.py`).
  2. Load ML models (Semantic Gate, Domain Gate V2, Galaxy Zoo EfficientNet-B0).
  3. Load static triage reference tensors.
  4. Perform single PyTorch dummy warmup inference pass.
  5. Mark backend status as `is_ready = True`.
- **Health Check**: `GET /api/v1/health` is lightweight and returns status without invoking ML models or external network calls.
- **Asynchronous Catalog Enrichment**: `POST /api/v1/triage` processes local ML inference immediately and enqueues external TAP/API queries (Gaia DR3, SDSS DR16, ALLWISE, TESS, NASA Exoplanet Archive, SIMBAD) as non-blocking `BackgroundTasks`.

---

## 3. ML Runtime Dependencies & Model Artifacts

| Component | Architecture / Model | Weight File / Source | File Size | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Semantic Gate** | OpenCLIP `ViT-B-32` (`laion2b_s34b_b79k`) | HuggingFace Cache | ~350 MB | ~400 MB RAM |
| **Domain Gate V2** | MobileNetV3-Small | `ml/models/domain_gate_v2_best.pt` | 6.1 MB | ~20 MB RAM |
| **Galaxy Zoo Model** | EfficientNet-B0 | `ml/models/best_model.pt` | 15.4 MB | ~50 MB RAM |
| **Object Classifier** | OpenCLIP Zero-Shot Ensemble | Shared OpenCLIP weights | — | (Shared) |
| **Triage Engine** | PyTorch Reference Embeddings | `ml/data/train_embeddings.pt` | ~1.2 MB | ~10 MB RAM |

**Total Runtime Memory Footprint**: ~1.1 GB – 1.3 GB RAM.

---

## 4. Environment Variables & External APIs

### Environment Variables
- `ASTRA_DEVICE`: Force target PyTorch device (`cpu`, `cuda`, `mps`). Default: auto-detects `cuda` -> `mps` -> `cpu`.
- `HF_HUB_OFFLINE`: Set to `1` in production to prevent HuggingFace hub network checks during startup.
- `PORT`: HTTP port for ASGI server (default: `8000`).
- `HOST`: Bind address (must be `0.0.0.0` in production).
- `ALLOWED_ORIGINS`: Comma-separated CORS allowed origins (e.g. `https://astra.pages.dev,http://localhost:5173`).
- `FRONTEND_ORIGIN`: Deployed frontend HTTPS origin URL.
- `GEMINI_API_KEY`: (Optional) API key for Google Gemini provider. If omitted, Space Help AI uses ASTRA's built-in deterministic astronomy fallback engine.

### External APIs (All Non-Blocking / Asynchronous)
- **Gaia DR3 TAP**: `https://gea.esac.esa.int/tap-server/tap`
- **SDSS DR16 SkyServer**: `https://skyserver.sdss.org/dr16/SkyServerWS/SearchTools/SqlSearch`
- **ALLWISE TAP**: `https://irsa.ipac.caltech.edu/TAP`
- **TESS MAST**: `https://mast.stsci.edu/api/v0/tap`
- **NASA Exoplanet Archive**: `https://exoplanetarchive.ipac.caltech.edu/TAP`
- **SIMBAD CDS**: `https://cdsarc.cds.unistra.fr/viz-bin/tap`

---

## 5. Local Development Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend server
cd backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Execute all backend tests
PYTHONPATH=. pytest backend/tests/ -v
```

### Frontend
```bash
# Install dependencies
cd frontend
npm ci

# Run dev server
npm run dev

# Production build
npm run build
```

---

## 6. Empirical Performance Benchmarks (Local Baseline)

**Benchmarked Machine**: Apple Silicon M4, PyTorch MPS / CPU mode.

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Backend Import Time** | — | **1.417 s** | PASS |
| **Full Startup & Warmup (`HF_HUB_OFFLINE=1`)** | ≤ 2.0 s target / ≤ 5.0 s hard | **3.251 s** | PASS |
| **Health Endpoint (`GET /api/v1/health`) p50** | < 100 ms | **0.69 ms** | EXCEEDED |
| **Health Endpoint (`GET /api/v1/health`) p95** | < 100 ms | **0.81 ms** | EXCEEDED |
| **First Warm Triage Request** | < 500 ms | **250.0 ms** | EXCEEDED |
| **Warm Triage Request (`POST /api/v1/triage`) p50** | < 500 ms | **193.41 ms** | EXCEEDED |
| **Warm Triage Request (`POST /api/v1/triage`) p95** | < 500 ms | **195.46 ms** | EXCEEDED |
| **Warm Triage Request (`POST /api/v1/triage`) max** | ≤ 2000 ms | **195.82 ms** | EXCEEDED |
| **CPU Triage Request (10 runs) p50** | < 500 ms | **193.20 ms** | EXCEEDED |

---

## 7. Production Resource Requirements

- **Processor**: 2 vCPU minimum (ARM64 or x86_64).
- **RAM**: 2 GB RAM minimum (1.3 GB active ML allocation + OS overhead).
- **Disk Storage**: 4 GB free disk space (Python virtualenv, PyTorch CPU wheel, model weights, OpenCLIP weights).
- **Network**: HTTPS support with reverse proxy (Nginx or Caddy) handling SSL termination and proxying to Gunicorn/Uvicorn on `0.0.0.0:8000`.
- **Hosting Tier**: Always-On Free VM (e.g., Oracle Cloud Always Free 4 ARM vCPU / 24 GB RAM instance or persistent Cloud VPS) or Always-Warm container instance. Render Free web services are explicitly excluded due to idle spin-down sleeping behavior.
