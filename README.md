# ASTRA — AI-Based Astronomical Observation Triage System

**SIH 2026 Space-Tech Project**

ASTRA is an intelligent, high-performance astronomical observation triage and prioritization system designed to optimize satellite downlink bandwidth and accelerate scientific discovery.

---

## 🚀 Core Concept & Pipeline

Modern spaceborne telescopes generate vast volumes of observation data, far exceeding available satellite-to-Earth downlink bandwidth. ASTRA solves this challenge through onboard and ground-based AI triage:

```
[ Satellite Observation ]
         │
         ▼
[ Domain Input Validation ]  ---> Rejects non-astronomical images (landscapes, objects, noise)
         │
         ▼
[ Lightweight AI Triage ]    ---> Galaxy morphology analysis & tabular classification
         │
         ▼
[ Anomaly / OOD Detection ]  ---> Statistically unusual or out-of-distribution detection
         │
         ▼
[ Priority Scoring ]        ---> Downlink bandwidth prioritization
         │
         ▼
[ Earth-Side Analysis ]     ---> Catalog cross-matching & deeper pipeline processing
         │
         ▼
[ Scientific Review ]       ---> AI Mission Copilot explanation & human review
```

---

## 🎯 Scientific Position & Claims

ASTRA explicitly adheres to strict scientific defense principles:
* **Out-of-Distribution (OOD) & Anomaly Detection**: The system identifies observations that are statistically unusual or outside its learned distribution and prioritizes them for expert scientific review.
* **Strict Input Validation**: Non-astronomical images (such as landscape photos, memes, text screenshots, animals, or human photos) are explicitly detected and rejected as unsupported inputs before ML processing.

---

## 🛠️ Architecture & Tech Stack

* **Machine Learning & Physics**: PyTorch (MPS acceleration), Torchvision, TIMM, Scikit-learn, Astropy
* **Datasets Integrated**:
  1. **Galaxy Zoo 2**: ~243,000 galaxy images (morphology classification, embeddings, OOD detection)
  2. **SDSS DR16 Catalog**: ~15,000 spectral & photometric objects (stars, galaxies, quasars)
  3. **NASA Exoplanet Archive**: Confirmed planet parameters (secondary module)
* **Backend**: FastAPI + Uvicorn (sub-second cold start & low-latency API inference)
* **Frontend**: React + Vite (high-aesthetic observation library, triage dashboard, mission copilot)

---

## 📁 Repository Structure

```
ASTRA/
├── frontend/        # Web application user interface (React + Vite)
├── backend/         # Production FastAPI triage services
├── ml/              # Machine learning pipelines, models, and artifacts
│   ├── data/        # Raw, processed, and split dataset references
│   ├── notebooks/   # Exploratory research and model training notebooks
│   ├── src/         # ML source modules (classifiers, OOD detectors, feature extractors)
│   ├── models/      # Saved model checkpoints (.pth, .joblib)
│   ├── artifacts/   # Precomputed feature vectors, embeddings, and scalers
│   └── tests/       # ML unit and integration tests
├── scripts/         # Utility scripts (data setup, precomputation, benchmarks)
├── docs/            # Project documentation and architectural diagrams
└── requirements.txt # Python dependencies
```

---

## 🔒 Environment & Setup

Ensure Python 3.13 and a dedicated virtual environment are used:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
