# Phase 10F — Domain Gate V2 Promotion & Integration Verification

## Executive Summary
Phase 10F promotes the Domain Gate V2 checkpoint (`ml/models/domain_gate_v2_best.pt`) into the production FastAPI inference pipeline. This model replaces V1 in production while preserving `ml/models/domain_gate_best.pt` on disk for auditability and comparative analysis.

---

## Production Configuration
- **Model Checkpoint**: `ml/models/domain_gate_v2_best.pt`
- **Architecture**: MobileNetV3-Small binary domain classifier (~1.52M parameters)
- **Model Version String**: `mobilenet_v3_small_domain_gate_v2_epoch15`
- **Calibration Temperature**: $T = 1.4996$
- **Decision Thresholds**:
  - `COMPATIBLE`: $P(\text{Astronomical}) \ge 0.80$
  - `UNCERTAIN`: $0.20 < P(\text{Astronomical}) < 0.80$
  - `INCOMPATIBLE`: $P(\text{Astronomical}) \le 0.20$

---

## End-to-End HTTP API Regression Benchmark Results
Evaluated against the full 380-sample Phase 10D adversarial benchmark suite via live HTTP POST requests to `http://localhost:8000/api/v1/triage`:

| Metric / Category | Phase 10E Validation | Phase 10F HTTP API Production |
| :--- | :--- | :--- |
| **False Acceptance Rate (FAR @ 0.80)** | 0.00% (0 / 260) | **0.00% (0 / 260)** |
| **Astronomical Recall (COMPATIBLE @ 0.80)** | 100.00% (120 / 120) | **100.00% (120 / 120)** |
| **Hard-Negative INCOMPATIBLE Rejections** | 257 / 260 | **255 / 260** |
| **Hard-Negative UNCERTAIN Abstentions** | 3 / 260 | **5 / 260** |
| **Hard-Negative False Acceptances** | 0 / 260 | **0 / 260** |

---

## Safety Controls & Execution Logic
1. **`INCOMPATIBLE`**:
   - Skips Galaxy Zoo EfficientNet-B0 morphology model execution completely.
   - Skips `ASTRATriageEngine` anomaly scoring.
   - Returns safe message: *"This image does not appear to contain astronomical observation data. No astronomical classification was performed."*
2. **`UNCERTAIN`**:
   - Skips morphology and triage execution completely.
   - Returns safe uncertainty message requiring manual scientific verification.
3. **`COMPATIBLE`**:
   - Executes full 4-class Galaxy Zoo morphology, attribute regression, embedding extraction, and scientific triage scoring.

---

## Latency & Performance Benchmarks
- **FastAPI Startup Time**: ~2.04 seconds (models loaded lazily once during lifespan; zero per-request loading).
- **GET `/api/v1/health` Latency**: ~2.60 ms.
- **`INCOMPATIBLE` / `UNCERTAIN` Latency**: ~7.59 ms (mean), ~7.54 ms (median), max 8.04 ms.
- **`COMPATIBLE` Full Analysis Latency**: ~25.23 ms (mean), ~23.59 ms (median), max 34.54 ms.

---

## Scope & Limitations
- **Held-Out Adversarial Benchmark vs. Universal Recognition**: The 380-sample adversarial suite demonstrates high robustness against known hard negatives (animals, weather radar, dark screenshots, night scenes, heatmaps). However, this does not guarantee universal arbitrary image recognition against unconstrained distribution shifts.
- **Abstention Policy**: Boundary images falling into $[0.20, 0.80]$ abstain from classification to prioritize scientific safety over forced prediction.
