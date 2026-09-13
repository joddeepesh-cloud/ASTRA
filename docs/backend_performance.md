# ASTRA FastAPI Backend Performance Report

---

## 1. Summary Metrics

- **Device**: `mps` (Apple Silicon MPS)
- **Model Version**: `galaxy-zoo-efficientnet-b0-epoch10`
- **Startup Duration (Model Load + Warmup)**: `371.02 ms` (~0.37s)
- **Health Endpoint Latency**: `1.12 ms`
- **First Post-Startup Triage API Call**: `22.72 ms`
- **Warm 30-Request Triage API Mean Latency**: **`16.92 ms`**
- **Warm Median**: `16.86 ms` | **Warm P95**: `17.51 ms` | **Min**: `16.27 ms` | **Max**: `17.52 ms`

---

## 2. Startup & Model Lifecycle Performance

| Phase | Duration | Description |
| :--- | :--- | :--- |
| **Model & Reference Load** | `367.35 ms` | PyTorch checkpoint (`best_model.pt`, 51.99 MB) & reference json loaded into memory |
| **Warmup Forward Pass** | ~`15 ms` | Dummy 224x224 RGB image pass to compile MPS shaders / CUDA kernels |
| **Total Backend Startup** | `371.02 ms` | Backend service achieves `ml_ready == true` readiness status |

---

## 3. API Endpoint Benchmark Table

| Endpoint | Method | Conditions | Mean Latency | Median | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | Readiness check | `1.12 ms` | `1.12 ms` | `1.12 ms` |
| `/api/v1/triage` | `POST` | First Call (Post-Warmup) | `22.72 ms` | - | - |
| `/api/v1/triage` | `POST` | Warm 30 Iterations | **`16.92 ms`** | `16.86 ms` | `17.51 ms` |
