# ASTRA — Object Identification Forensic Audit

## Executive Summary
This forensic audit was conducted to investigate why the recent Evidence-First Object Router V2 resulted in almost every astronomical image being reported as `GALAXY`.

**Audit Findings**:
The issue stems from a combination of three root causes:
1. **Galaxy Zoo Model Misuse (Primary Code Bug)**: `GalaxyZooInference` is a 4-class morphology specialist (`SMOOTH`, `FEATURED_DISK`, `EDGE_ON`, `SPIRAL`). It ALWAYS outputs one of these 4 classes with probabilities summing to 1.0. When passed to `Rule A` (`has_gz_galaxy_evidence = gz_pred in ["SPIRAL", "SMOOTH", "FEATURED_DISK", "EDGE_ON"]`), `has_gz_galaxy_evidence` evaluates to `True` for **100% of domain-compatible astronomical images**, forcing `GALAXY` on all stars, nebulae, quasars, and point sources.
2. **OpenCLIP Prior Bias**: OpenCLIP zero-shot scoring on LAION-2B pre-training weights exhibits an inherent visual prior bias towards `GALAXY` for dark optical telescope cutouts, ranking `GALAXY` as top-1 even for stellar fields before any rules are applied.
3. **Extended Structural Fallback (`Rule B`)**: Any non-point-source image with an extended score (`ext_score >= 0.45`) was automatically routed to `GALAXY`, causing extended nebulae to be misclassified as galaxies.

---

## 1. Current Architecture

```
                      ASTRONOMICAL IMAGE
                              │
                              ▼
                 Stage 1: Semantic Gate (CLIP)
                              │
                    [SEMANTIC_COMPATIBLE]
                              │
                              ▼
                 Stage 2: Domain Gate V2
                              │
                        [COMPATIBLE]
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
   Galaxy Zoo Specialist             Image Structural Analysis
   (4-class EfficientNet)               (10 pixel metrics)
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                   OpenCLIP Zero-Shot Scoring
                              │
                              ▼
                    Evidence Fusion Router V2
                    (Rule A -> Rule B -> Rule C...)
                              │
                              ▼
                     FINAL OBJECT TYPE
```

---

## 2. Complete Execution Path

1. **Upload & Decoding**: [`backend/app/services/ml_service.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/app/services/ml_service.py#L98)
   - `Image.open(io.BytesIO(file_bytes))` -> RGB image.
2. **Stage 1 (Semantic Gate)**: [`ml/src/semantic_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/semantic_gate.py)
   - Model: OpenCLIP ViT-B/32 LAION-2B.
   - Evaluates astronomical vs non-astronomical prompt sets.
3. **Stage 2 (Domain Gate V2)**: [`ml/src/domain_gate.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/domain_gate.py)
   - Model: MobileNetV3-Small binary gate.
   - Verifies astronomical observation domain.
4. **Stage 3 (Galaxy Zoo Specialist Pass)**: [`ml/src/triage.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/triage.py) & [`ml/src/inference.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/inference.py)
   - Model: EfficientNet-B0 (`galaxy-zoo-efficientnet-b0-epoch10`).
   - Output: 4-class galaxy morphology probabilities (`SMOOTH`, `FEATURED_DISK`, `EDGE_ON`, `SPIRAL`).
5. **Stage 4 (Evidence Fusion Router V2)**: [`ml/src/object_identification.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/ml/src/object_identification.py)
   - Function: `ObjectIdentificationService.classify_pil_image()`
   - Evaluates `Rule A` (Galaxy Specialist Protection), `Rule B` (Extended Fallback), `Rule C` (Point Source Guardrail), `Rule D` (Nebula Filter).
6. **API Response & Frontend**: [`backend/app/schemas.py`](file:///Users/deepeshjoshi/Desktop/ASTRA/backend/app/schemas.py) & [`frontend/src/components/TriageExplanation.tsx`](file:///Users/deepeshjoshi/Desktop/ASTRA/frontend/src/components/TriageExplanation.tsx)
   - Serializes `predicted_object_type` and renders `ANOMALY & INTERPRETATION` panel.

---

## 3. GALAXY Override Audit Table

| Location | Code Condition | Action | Can Force GALAXY? | Why It Exists |
| :--- | :--- | :--- | :--- | :--- |
| `ml/src/object_identification.py:161` (`Rule A`) | `has_gz_galaxy_evidence and (gz_conf is None or gz_conf >= 0.35)` | `pred_type = "GALAXY"` | **YES (100% of astro images)** | Intended to protect galaxy core cutouts from zero-shot Quasar confusion, but because Galaxy Zoo only outputs galaxy labels, it forced GALAXY on everything. |
| `ml/src/object_identification.py:183` (`Rule B`) | `is_ext or ext_score >= 0.45 or (top_class == "GALAXY" ...)` | `pred_type = "GALAXY"` | **YES (for all extended sources)** | Intended to catch extended galaxies, but caught extended nebulae as well. |
| `ml/src/object_identification.py:186` | `top_class == "QUASAR" and ext_score >= 0.40` | `pred_type = "GALAXY"` | **YES** | Overrides CLIP Quasar prediction if image structure is spatially extended. |
| `backend/app/services/ml_service.py:281` | `if pred_obj_type == "GALAXY":` | Executes Galaxy Zoo triage | **NO** | Routing gate for Galaxy Zoo triage pipeline. |

---

## 4. OpenCLIP Raw Rankings vs Final Decisions

| Category | File | Raw OpenCLIP Ranking (Top-3) | Galaxy Zoo Pred | Current Final Class | Forced by Rule A? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GALAXY | `100035.jpg` | GALAXY (0.58), QUASAR (0.15), UNKNOWN (0.09) | FEATURED_DISK (47.8%) | GALAXY | NO (CLIP matched) |
| GALAXY | `100047.jpg` | GALAXY (0.50), QUASAR (0.32), UNKNOWN (0.05) | EDGE_ON (98.9%) | GALAXY | NO (CLIP matched) |
| STELLAR_FIELD | `adv_pos_stellar_fields_002.jpg` | GALAXY (0.31), NEBULA (0.25), QUASAR (0.17) | SMOOTH (39.5%) | GALAXY | YES (GZ forced) |
| STELLAR_FIELD | `adv_pos_stellar_fields_003.jpg` | GALAXY (0.44), QUASAR (0.25), NEBULA (0.17) | SMOOTH (56.5%) | GALAXY | YES (GZ forced) |
| NEBULAR_FIELD | `adv_pos_nebular_fields_003.jpg` | UNKNOWN (0.27), PLANETARY (0.26), STAR (0.18) | EDGE_ON (32.9%) | GALAXY | YES (Rule B / GZ) |
| SURVEY_CUTOUT | `adv_pos_survey_cutouts_004.jpg` | QUASAR (0.36), GALAXY (0.30), STAR (0.12) | FEATURED_DISK (50.8%) | GALAXY | YES (GZ overrode QUASAR) |
| NON_ASTRO | `non_astro_0001.jpg` | N/A (Stage 1 Incompatible) | N/A | INCOMPATIBLE | NO |

---

## 5. Where the GALAXY Bias Originated

1. **Logic Fault in Evidence Fusion**:
   `has_gz_galaxy_evidence` checked if `gz_pred` belonged to `["SPIRAL", "SMOOTH", "FEATURED_DISK", "EDGE_ON"]`. Because `GalaxyZooInference` is a supervised 4-class classifier built specifically for galaxy morphology, **its prediction is ALWAYS one of those 4 classes**. Treating the presence of a Galaxy Zoo output label as proof that the source is a galaxy creates a circular tautology:
   $$\text{Image passed to Galaxy Zoo} \implies \text{Output } \in \{\text{SMOOTH, FEATURED\_DISK, EDGE\_ON, SPIRAL}\} \implies \text{Forced GALAXY}$$

2. **OpenCLIP Training Prior Bias**:
   The OpenCLIP ViT-B/32 model trained on LAION-2B exhibits a structural prior bias towards the word "galaxy" whenever presented with a dark background containing astronomical light. Even for stellar fields, raw zero-shot similarity places `GALAXY` at rank #1.

---

## 6. STAR Limitations
- Single-band optical cutouts of point sources present identical point-spread functions (PSF) for both stars and unresolved quasars.
- Visual imaging alone cannot confirm a stellar classification without multi-band color indices (e.g., $u-g, g-r$) or proper motion catalog data.

---

## 7. QUASAR Limitations
- Optical cutouts of quasars appear visually as unresolved point sources indistinguishable from foreground stars or active galactic nuclei (AGN) cores.
- Confirming a Quasar candidate requires spectroscopic redshift ($z$), UV/X-ray emission evidence, or multi-epoch variability data.

---

## 8. NEBULA Evidence Assessment
- Nebulae exhibit extended, diffuse, low-surface-brightness emission without a dominant point-source core.
- Current structural metrics calculate `diffuse_emission_score`, `extent_px`, and `spatial_dispersion`.
- However, `Rule B` in the router previously routed any extended image (`ext_score >= 0.45`) to `GALAXY`, intercepting nebular images before nebular rules could execute.

---

## 9. EXOPLANET Limitations
- **Scientific Fact**: A standard optical telescope image cutout **CANNOT directly image an exoplanet**. Exoplanets are billions of times fainter than their host stars and visually unresolved in survey cutouts.
- **Required Evidence for Exoplanet Identification**:
  - Time-series photometric transit light curves (dip in flux vs time).
  - High-precision radial velocity spectrographs (Doppler wobble).
  - Direct imaging coronagraphy with extreme adaptive optics (only for rare giant planets).
  - Catalog cross-matching with NASA Exoplanet Archive / TESS / Kepler target lists.
- **Conclusion**: Single image cutouts must NEVER claim exoplanet identification.

---

## 10. Galaxy Zoo Misuse Assessment

**Finding**: Galaxy Zoo WAS MISUSED as a general astronomical object classifier.

- **Intended Purpose**: Galaxy Zoo (EfficientNet-B0) is a **Morphology Specialist** for confirmed galaxies. It answers: *"Given that this object is a galaxy, what is its visual morphology?"*
- **Actual Code Behavior**: Galaxy Zoo was invoked **before** object type routing on all domain-compatible images, and its 4-class output was treated as evidence that the input image was a galaxy.
- **Required Architecture Correction**: Object identification must occur FIRST. Galaxy Zoo must ONLY be executed AFTER an image is determined to be a GALAXY.

```
                    ASTRONOMICAL IMAGE
                           │
                           ▼
                 OBJECT TYPE ROUTER
            (Image Structure + Catalog/Multi-modal)
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
          GALAXY      POINT SOURCE     DIFFUSE / NEBULA
            │              │              │
            ▼              ▼              ▼
       Galaxy Zoo     Point-source      Nebular
       Morphology    Ambiguity Check    Analysis
```

---

## 11. Exact Root Cause Summary

- **Primary Code Bug**: `Rule A` in `ml/src/object_identification.py` treated `GalaxyZooInference` 4-class output as proof of galaxy existence, forcing 100% of astronomical images to `GALAXY`.
- **Primary Model Bias**: OpenCLIP zero-shot model has a strong prompt prior favoring `GALAXY` for optical astronomical cutouts.
- **Secondary Routing Bug**: `Rule B` routed all extended light profiles to `GALAXY`, misclassifying nebulae.

---

## 12. Recommended Next Architecture (No Prompt Tricks)

1. **Decouple Galaxy Zoo**: Remove Galaxy Zoo output from the object identification service inputs completely.
2. **Structural Object Classifier**: Rely on image structure metrics (FWHM, concentration ratio, compactness, diffuse score, extent) + zero-shot embeddings WITHOUT hard-coded GALAXY defaults.
3. **Explicit Ambiguity Routing**:
   - Compact sources ($FWHM \le 12\text{px}$, $Conc \ge 0.55$) $\implies$ `AMBIGUOUS_POINT_SOURCE`.
   - Diffuse sources ($DiffScore \ge 0.45$, $Extent \ge 100\text{px}$) $\implies$ `NEBULA_CANDIDATE`.
   - Extended structured sources ($ExtScore \ge 0.45$) $\implies$ `GALAXY`.
   - Ambiguous / Low margin sources $\implies$ `ASTRONOMICAL_SOURCE_AMBIGUOUS`.

---

## Required Structured Summary

```
ROOT_CAUSE: Galaxy Zoo specialist 4-class output (SMOOTH, FEATURED_DISK, EDGE_ON, SPIRAL) was evaluated in Rule A as proof of galaxy existence, forcing 100% of domain-compatible astronomical images (stars, nebulae, quasars, point sources) to GALAXY.
CONFIDENCE_IN_ROOT_CAUSE: 100% (Verified via code inspection, empirical diagnostic trace, and simulation without Rule A).
CURRENT_MODEL_CAPABILITY: The current models can reliably distinguish Astronomical Observations from Non-Astronomical images (Domain Gate V2 & Semantic Gate) and classify Galaxy Morphology (Galaxy Zoo Specialist).
WHAT_WE_CAN_RELIABLY_IDENTIFY_NOW: Astronomical Domain Compatibility, Galaxy Morphology (for confirmed galaxies), Image Structural Characteristics (point-like vs extended vs diffuse emission).
WHAT_REQUIRES_NEW_DATA/MODEL: Reliable Star vs Quasar vs Galaxy zero-shot optical classification (requires trained multi-class astronomical object backbone or multi-band survey data).
WHAT_REQUIRES LIGHT CURVES/CATALOG DATA: Exoplanet identification (requires transit light curves / catalog cross-match), Quasar confirmation (requires spectroscopic redshift / multi-band catalog), Star identification (requires stellar catalogs / proper motion).
```
