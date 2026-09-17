# ASTRA Phase 14 Master Report: Open-World Astronomy Routing & False-Rejection Fix

## 1. Executive Summary
Phase 14 resolves the false-rejection defect where legitimate astronomy-related imagery (black-hole renderings, exoplanet graphics, active galaxy imagery, stellar point sources, and NASA telescope releases) was prematurely aborted as `INCOMPATIBLE`. 

By refining the domain gating control flow in `MLService` ([`ml_service.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/app/services/ml_service.py)), open-world astronomy images with `UNCERTAIN` domain gate states are no longer short-circuited as hard rejections. Instead, they proceed through Object Identification Router V2 and Background Multi-Modal Evidence Enrichment, distinguishing **Observational Evidence** from **Astronomy Visualizations** without retraining PyTorch models or modifying core ML weights.

---

## 2. Current Pipeline Trace
```
UPLOAD FILE
   │
   ▼
Stage 1: Universal Semantic Gate (OpenCLIP Prompt Ensemble)
   │
   ├─► SEMANTIC_INCOMPATIBLE ──► HARD REJECT (INCOMPATIBLE)
   │
   ▼ SEMANTIC_COMPATIBLE / SEMANTIC_UNCERTAIN
Stage 2: Domain Gate V2 (MobileNetV3 Astronomy Gate)
   │
   ├─► Both Gates INCOMPATIBLE ──► HARD REJECT (INCOMPATIBLE)
   │
   ▼ COMPATIBLE / UNCERTAIN
Stage 3: Object Identification Router V2 (Pixel Structure + OpenCLIP)
   │
   ├─► GALAXY ─────────────────► Stage 4: Galaxy Zoo Specialist (Morphology)
   ├─► AMBIGUOUS_POINT_SOURCE ──► Skip Galaxy Zoo (NOT_APPLICABLE)
   ├─► NEBULA_CANDIDATE ───────► Skip Galaxy Zoo (NOT_APPLICABLE)
   └─► ASTRONOMICAL_SOURCE_AMBIGUOUS ──► Skip Galaxy Zoo (NOT_APPLICABLE)
   │
   ▼
Stage 5: Asynchronous Background Multi-Modal Evidence Enrichment
   │ (Gaia DR3, SDSS DR16, ALLWISE, TESS, NASA Exoplanet TAP Archive)
   ▼
Stage 6: Evidence Fusion Engine & Frontend Display
   (GALAXY, STAR, QUASAR_CANDIDATE, EXOPLANET_CANDIDATE, KNOWN_EXOPLANET_MATCH, AMBIGUOUS_POINT_SOURCE)
```

---

## 3. Exact Early-Rejection Points Identified
1. **`backend/app/services/ml_service.py` (Line 172)**: Previously, `if sem_result.status == "SEMANTIC_UNCERTAIN": return {"predicted_object_type": "INCOMPATIBLE"}` immediately returned hard rejection.
2. **`backend/app/services/ml_service.py` (Line 227)**: Previously, `if decision_v2 in ("INCOMPATIBLE", "UNCERTAIN"): return {"predicted_object_type": "INCOMPATIBLE"}` treated `UNCERTAIN` identically to `INCOMPATIBLE`.
3. **`frontend/src/components/UploadDropzone.tsx` (Line 593)**: Previously, `triageResult.domain_validation?.decision === 'UNCERTAIN'` rendered a blocking error card hiding all analysis.

---

## 4. Root Cause
The domain gates (MobileNetV3 and OpenCLIP) returned `UNCERTAIN` when evaluating non-standard telescope imagery, astronomical renders, or compact point sources. Because `MLService` and `UploadDropzone.tsx` treated `UNCERTAIN` as hard `INCOMPATIBLE` rejections, processing was short-circuited before Object Identification or Evidence Fusion could run.

---

## 5. Semantic Gate Behavior
`SemanticDomainGate` ([`semantic_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/semantic_gate.py)) evaluates prompt ensemble similarities across `astronomical`, `terrestrial`, `visualization`, `artwork`, and `fictional_space` families.
* `SEMANTIC_INCOMPATIBLE`: High similarity to terrestrial/office families ($margin \le -0.01$). Triggers hard rejection.
* `SEMANTIC_COMPATIBLE` & `SEMANTIC_UNCERTAIN`: Passes to Stage 2 Domain Gate V2.

---

## 6. Domain Gate Behavior
`DomainGate` ([`domain_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/domain_gate.py)) computes MobileNetV3 astronomical probability.
* Hard rejection occurs **ONLY IF** `decision_v2 == "INCOMPATIBLE"` AND `sem_result.status == "SEMANTIC_INCOMPATIBLE"`.
* If `decision_v2 == "UNCERTAIN"` or `sem_result.status == "SEMANTIC_UNCERTAIN"`, the pipeline continues to Stage 3.

---

## 7. Object Router Behavior
`ObjectIdentificationService` ([`object_identification.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/object_identification.py)) evaluates pixel structure + prompt similarity:
* Extended galaxy profile $\to$ `GALAXY`.
* Unresolved compact point source $\to$ `AMBIGUOUS_POINT_SOURCE`.
* Diffuse nebular emission $\to$ `NEBULA_CANDIDATE` or `ASTRONOMICAL_SOURCE_AMBIGUOUS`.
* Low similarity / visualization $\to$ `ASTRONOMICAL_SOURCE_AMBIGUOUS` with status `INSUFFICIENT_VISUAL_EVIDENCE`.

---

## 8. Galaxy Zoo Interaction
* Galaxy Zoo EfficientNet-B0 morphology specialist runs **ONLY IF** `pred_obj_type == "GALAXY"`.
* For non-galaxy targets (`AMBIGUOUS_POINT_SOURCE`, `ASTRONOMICAL_SOURCE_AMBIGUOUS`, `NEBULA_CANDIDATE`), morphology is marked `NOT_APPLICABLE` and Galaxy Zoo is skipped.

---

## 9. Exoplanet Failure Path Resolved
* Exoplanet visualizations/graphics no longer fail as `INCOMPATIBLE`. They resolve to `ASTRONOMICAL_SOURCE_AMBIGUOUS`.
* Genuine exoplanet target coordinates enrich via NASA Exoplanet TAP Archive (`pscomppars`):
  * TAP confirmed planet $\to$ `KNOWN_EXOPLANET_MATCH`.
  * TESS transit signal / candidate $\to$ `EXOPLANET_CANDIDATE`.

---

## 10. Star / Point Source Failure Path Resolved
* Point sources no longer fail when external catalog evidence is unavailable. They resolve to `AMBIGUOUS_POINT_SOURCE`.
* When Gaia DR3 astrometry is present ($\varpi > 0$ or $|\mu| \ge 3.0$ mas/yr), Evidence Fusion resolves to `STAR`.

---

## 11. Quasar / AGN Failure Path Resolved
* Point sources without quasar spectroscopy resolve to `AMBIGUOUS_POINT_SOURCE`.
* When SDSS spectroscopy ($z > 0.05$) or QSO catalog membership is present, Evidence Fusion resolves to `QUASAR_CANDIDATE`.

---

## 12. Black-Hole Handling
* `BLACK_HOLE_DIRECT_CLASSIFICATION = NOT_SUPPORTED`. Image appearance alone never generates "BLACK HOLE CONFIRMED".
* Black hole renders and accretion disk graphics pass domain gates and resolve to `ASTRONOMICAL_SOURCE_AMBIGUOUS` with status `INSUFFICIENT_VISUAL_EVIDENCE`.

---

## 13. Visualization Handling
* Visualizations are recognized as astronomy-related (`astronomy_related = True`), but `observational_evidence = False`.
* Scientific disclaimer explicitly states: *"This image is astronomy-related, but visual imaging alone is not sufficient to establish direct observational proof for the depicted object."*

---

## 14. Evidence Routing
* Background evidence worker (`run_background_evidence_enrichment`) enqueues non-blocking catalog queries when coordinates are present.
* `EvidenceFusionEngine` synthesizes local image metrics with external catalog evidence.

---

## 15. Frontend Handling
* `frontend/src/components/UploadDropzone.tsx`: Both `COMPATIBLE` and `UNCERTAIN` domain decisions render the main analysis view.
* `UNCERTAIN` displays an amber badge: `"ASTRONOMY IMAGE ACCEPTED — UNCERTAIN DOMAIN"`.
* `INCOMPATIBLE` displays a red rejection card: `"REJECTED: NON-ASTRONOMICAL IMAGE"`.

---

## 16. Exact Files Modified
1. [`backend/app/services/ml_service.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/app/services/ml_service.py)
2. [`ml/src/object_identification.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/object_identification.py)
3. [`frontend/src/components/UploadDropzone.tsx`](file:///Users/deepeshjoshi/Desktop/ASTRA/frontend/src/components/UploadDropzone.tsx)
4. [`backend/tests/test_phase14_routing.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/tests/test_phase14_routing.py)

---

## 17. Exact Code-Level Changes
* **`ml_service.py`**: Removed early return on `SEMANTIC_UNCERTAIN`; updated STAGE 2 rejection condition to require both Domain Gate V2 and Semantic Gate to reject (`decision_v2 == "INCOMPATIBLE" and sem_result.status == "SEMANTIC_INCOMPATIBLE"`).
* **`object_identification.py`**: Updated default low-similarity fallback to `ASTRONOMICAL_SOURCE_AMBIGUOUS`.
* **`UploadDropzone.tsx`**: Rendered full analysis display for `COMPATIBLE` and `UNCERTAIN` domain validation states.

---

## 18. Test Cases & Matrix
* **Test 1**: Non-astronomical grid/terrestrial photo $\to$ `INCOMPATIBLE` (Rejected).
* **Test 2**: Black hole ring visualization $\to$ Pipeline Continues $\to$ `ASTRONOMICAL_SOURCE_AMBIGUOUS` (Not rejected).
* **Test 3**: Unresolved point source $\to$ `AMBIGUOUS_POINT_SOURCE` (Pipeline continues).
* **Test 4**: Galaxy Zoo morphology conditional execution $\to$ Skipped for non-galaxy targets.
* **Test 5**: Exoplanet TAP match $\to$ `KNOWN_EXOPLANET_MATCH`.

---

## 19. Test Results
* **Backend PyTest Suite**: **104 / 104 passed (100% pass rate)**.
* **Python Compilation**: `python3 -m compileall backend/app ml/src scripts` clean (0 errors).
* **Frontend Build**: `cd frontend && npm run build` succeeded cleanly in 931 ms.

---

## 20. Performance
* **Synchronous `/api/v1/triage` Latency**: **15.4 ms** (Local PyTorch inference).
* **Background Evidence Enrichment**: **180–420 ms** (Asynchronous background task).

---

## 21. Scientific Integrity Review
* No keyword hacks or hardcoded filename rules were added.
* Image appearance alone never forces `STAR`, `QUASAR_CANDIDATE`, or `KNOWN_EXOPLANET_MATCH`.
* Uncertainty is preserved as `ASTRONOMICAL_SOURCE_AMBIGUOUS` or `AMBIGUOUS_POINT_SOURCE`.

---

## 22. Remaining Limitations
* Single-band optical cutouts without astrometry, spectroscopy, or coordinate metadata cannot be definitively classified beyond `AMBIGUOUS_POINT_SOURCE` or `ASTRONOMICAL_SOURCE_AMBIGUOUS`.

---

## 23. ML / Data / Model / Triage Diff Verification
* `git diff -- ml/models/ ml/data/ ml/src/triage.py` produced **0 diffs**.
* Core PyTorch weights, datasets, and canonical triage formula ($0.35 N + 0.35 U + 0.30 O$) remain 100% untouched.

---

## Final Acceptance Status
[x] Clearly non-astronomical images are rejected.
[x] Astronomy-related imagery is not rejected merely because the domain gate is uncertain.
[x] Astronomy-related imagery continues to evidence routing.
[x] Exoplanet visualization is not falsely claimed as an exoplanet observation.
[x] Black-hole visualization is not falsely claimed as a detected black hole.
[x] Point sources reach Gaia/SDSS evidence routing when coordinates are available.
[x] Missing external evidence results in ambiguity, not rejection.
[x] Galaxy Zoo does not force every astronomy image to GALAXY.
[x] Known exoplanet classification requires authoritative catalog evidence.
[x] External APIs remain asynchronous.
[x] Backend tests pass (104/104).
[x] Frontend build passes.
[x] 0 forbidden ML/data/model/triage changes.
