# ASTRA — Render Free Prototype Deployment & Feasibility Report

**Date**: September 21, 2026  
**Git Commit**: `358fd01` (`main` branch)  
**Status**: OPTION D FALLBACK — PROTOTYPE REQUIRES ≥ 2 GB RAM HOSTING PLATFORM  

---

## 1. Baseline Memory Profiling (Stage-by-Stage)

Empirical memory profiling was performed directly on the codebase using CPython process RSS tracking on CPU (`ASTRA_DEVICE=cpu`):

| Stage | Name | Incremental RSS (MB) | Cumulative RSS (MB) |
| :---: | :--- | :---: | :---: |
| 1 | Python startup | 9.81 MB | 9.81 MB |
| 2 | FastAPI & Pydantic imports | 35.31 MB | 45.12 MB |
| 3 | NumPy import | 10.92 MB | 56.05 MB |
| 4 | SciPy import | 1.03 MB | 57.08 MB |
| 5 | pandas import | 57.20 MB | 114.28 MB |
| 6 | PyTorch import | 149.02 MB | 263.30 MB |
| 7 | torchvision & transforms import | 76.66 MB | 339.95 MB |
| 8 | transformers import | 30.45 MB | 370.41 MB |
| 9 | OpenCLIP import | 135.50 MB | 505.91 MB |
| 10 | OpenCLIP model construction (unweighted) | 565.92 MB | 1,071.83 MB |
| 11 | OpenCLIP weights loaded (`laion2b_s34b_b79k`) | 1,183.94 MB | 2,255.77 MB |
| 12 | Domain Gate V2 loaded (MobileNetV3) | 0.00 MB | 2,255.77 MB |
| 13 | EfficientNet-B0 loaded (Galaxy Zoo) | 0.00 MB | 2,255.77 MB |
| 14 | MLService initialization | 159.33 MB | 2,415.09 MB |
| 15 | Warmup pass completed | 0.00 MB | 2,415.09 MB |
| 16 | First real triage inference pass | 0.00 MB | **2,304.84 MB** |

---

## 2. Memory Optimization Experiments & Results

| Optimization Technique Tested | Impact on Peak RSS | Scientific Behavior Status |
| :--- | :--- | :--- |
| `torch.inference_mode()` & `torch.no_grad()` | Reduced initial tensor allocations by ~25 MB | **PASS** — Zero accuracy change |
| `torch.set_num_threads(1)` (Single Thread CPU) | Prevented thread stack memory multiplication | **PASS** — Latency maintained at ~193ms |
| Garbage collection (`gc.collect()`) after prompt ensemble | Reclaimed ~15 MB transient text tokens | **PASS** — Prompts preserved |
| Unloading OpenCLIP post-routing | CPython allocator retains peak RSS high-water mark | **FAIL** — cgroup memory peak still 2.3 GB |
| Dynamic Quantization (`qint8`) | Unsupported for full OpenCLIP ViT-B/32 CPU vision ops | **N/A** — Throws prepack error |

**Final Measured Peak RSS**: **2,304.84 MB RAM** (~2.25 GB).

---

## 3. Memory Target Evaluation

- **PREFERRED Target (≤ 450 MB)**: UNMET
- **ACCEPTABLE Target (450–500 MB)**: UNMET
- **RISKY Target (500–512 MB)**: UNMET
- **FINAL CATEGORY**: **NOT VIABLE (> 512 MB)**
- **Render Free Container RAM Limit**: **512.0 MB**
- **Memory Deficit**: **-1,792.84 MB OVER RENDER FREE LIMIT**

Per project guidelines: *"If the optimized backend is still >512 MB: DO NOT pretend it fits. Report 'Render Free cannot safely host the complete ML runtime.'"*

---

## 4. Retained & Verified ML Models

All three deep learning models in ASTRA's multi-stage pipeline remain 100% untouched and operational:
1. **Universal Semantic Gate & Object Identification**: OpenCLIP `ViT-B-32` (`laion2b_s34b_b79k`) — 350 MB weights.
2. **Domain Compatibility Gate V2**: MobileNetV3-Small (`domain_gate_v2_best.pt`) — 6.1 MB weights.
3. **Galaxy Zoo Morphology Specialist**: EfficientNet-B0 (`best_model.pt`) — 15.4 MB weights.

---

## 5. Scientific Regression Validation

All **127 backend unit tests** were executed against the optimized ML service baseline (`PYTHONPATH=. pytest backend/tests/ -v`):
- **Test Result**: **127 / 127 PASSED** (0 failures, 0 regressions, 0 scientific guardrail changes).
- **Verified Classifications**: `STAR`, `GALAXY`, `NEBULA_CANDIDATE`, `QUASAR_CANDIDATE`, `EXOPLANET_CANDIDATE`, `AMBIGUOUS_POINT_SOURCE`, `ASTRONOMICAL_SOURCE_AMBIGUOUS`, `INCOMPATIBLE`.
- **Verified Triage Formula**: Canonical 4-component equation ($T = 0.40 N + 0.25 D_{\text{raw}} + 0.20 O + 0.15 S$) preserved.

---

## 6. Recommended Prototype Fallback (OPTION D)

Because deploying the 2.3 GB PyTorch ML runtime onto Render Free's 512 MB RAM container causes immediate Linux cgroup Out-Of-Memory termination (`exit code 137` / SIGKILL), **Option D** is adopted:

> **Option D Strategy**: Document the exact hardware limitation honestly. Keep the production deployment infrastructure (`deploy/gunicorn.conf.py`, `deploy/astra-backend.service`, `deploy/nginx.conf`, `.github/workflows/deploy.yml`) fully built and validated for deployment to an always-warm cloud host with ≥ 2 GB RAM (such as Oracle Cloud Infrastructure Always Free ARM 4 vCPU / 24 GB RAM instance or a standard Cloud VPS).

---

## 7. URLs & Status Matrix

- **Frontend URL**: `https://2ea36865.astra-3ll.pages.dev` (Cloudflare Pages CDN)
- **Public Backend Health URL**: `https://api.astra.app/api/v1/health` (Configured; awaiting ≥2GB host)
- **Local Backend Health URL**: `http://localhost:8000/api/v1/health` (Verified operational; 0.69ms latency)
- **Render Free Stability**: **Unstable for full 2.3 GB ML runtime due to 512 MB cgroup memory limit**.
