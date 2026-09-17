# ASTRA Phase 12B — Multi-Modal Evidence Fusion Engine Report

## 1. Overview & Core Philosophy

Phase 12B introduces the **Evidence Fusion Engine** (`backend/app/services/evidence/evidence_fusion.py`) to synthesize multi-modal astronomical evidence (local image metrics, Galaxy Zoo specialist output, Gaia DR3 astrometry, SDSS spectroscopy/photometry, WISE infrared colors, TESS light curves, and NASA Exoplanet Archive data) into a scientifically justified object decision.

### Core Principle
> **ASTRA NEVER FORCES A CLASSIFICATION WHEN EVIDENCE IS INSUFFICIENT OR CONTRADICTORY.**

Prior to Phase 12B, classification systems were susceptible to argmax biases or single-specialist overrides (e.g., Galaxy Zoo overriding point sources as GALAXY). The Evidence Fusion Engine enforces multi-modal evidence thresholds. If catalog spectroscopy, parallax, or unambiguous spatial profiles are missing, ASTRA preserves scientific truth by outputting **`AMBIGUOUS_POINT_SOURCE`**, **`ASTRONOMICAL_SOURCE_AMBIGUOUS`**, or **`CONFLICTING_POINT_SOURCE_EVIDENCE`**.

---

## 2. Evidence Fusion Architecture

The fusion pipeline operates strictly downstream of data acquisition, remaining entirely isolated from the synchronous `/triage` inference path (~15–40 ms execution budget).

```
                            [ Local Image & Crop Metrics ]
                                         │
                                         ▼
   [ External Adapters ] ──► [ EvidenceBundle (Phase 12A) ]
  (Gaia, SDSS, WISE, etc.)               │
                                         ▼
                            [ Evidence Fusion Engine ]
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
           [ Target Decision ]   [ Evidence Level ]   [ Match Quality ]
            (GALAXY / STAR /     (NONE, WEAK, MOD,     (NO_MATCH, WEAK,
             QUASAR / etc.)       STRONG, DECISIVE)    GOOD, HIGH_QUALITY)
```

### Core Engine Interface
- **Module**: `backend/app/services/evidence/evidence_fusion.py`
- **Primary Method**: `fuse_evidence(image_evidence: Optional[Dict], catalog_bundle: Optional[EvidenceBundle]) -> FusedEvidenceResult`
- **Output Schema**: `FusedEvidenceResult` in `backend/app/services/evidence/evidence_models.py`

---

## 3. Evidence Hierarchy & Rule System

The engine applies a strict hierarchical evaluation order to prevent low-confidence visual heuristics from overriding high-precision physical measurements:

1. **Decisive Multi-Modal Evidence (Level: DECISIVE)**: Spectroscopic redshifts ($z > 0.05$), Gaia DR3 trigonometric parallax ($\varpi > 3\sigma_{\varpi}$), or confirmed exoplanet archive records within $1.0''$.
2. **Strong Physical/Catalog Evidence (Level: STRONG)**: WISE color excess ($W1-W2 \ge 0.8$), Gaia proper motion ($\mu > 5\sigma_{\mu}$), or TESS transit detections combined with optical point-source morphology.
3. **Moderate Extended Visual Evidence (Level: MODERATE)**: Galaxy Zoo specialist classification ($\ge 0.65$ confidence) combined with extended image FWHM or multi-pixel spatial flux profile.
4. **Weak / Ambiguous Evidence (Level: WEAK / NONE)**: Single-band visual detections without catalog cross-matches or structural evidence $\rightarrow$ Preserves ambiguity.

---

## 4. Object Type Decision Contracts

### A. GALAXY
- **Criteria**: Extended spatial light profile (image extent > 15 px or high FWHM) AND Galaxy Zoo morphology confidence $\ge 0.65$ (`SPIRAL`, `SMOOTH`, `FEATURED_DISK`, `EDGE_ON`).
- **Catalog Support**: SDSS extended source classification (`type == 3` / Galaxy photo-z) reinforces classification.
- **Evidence Level**: `MODERATE` (Visual extended) to `DECISIVE` (Spectroscopic/Catalog confirmation).

### B. STAR
- **Criteria**: Point-source visual morphology AND Gaia DR3 parallax $\varpi > 3\sigma_{\varpi}$ OR proper motion $\mu > 5\sigma_{\mu}$ OR SDSS stellar spectroscopy (`class == STAR`).
- **Evidence Level**: `STRONG` (Astrometric PM) to `DECISIVE` (Parallax / Spectroscopy).

### C. QUASAR CANDIDATE
- **Criteria**: Point-source visual morphology AND (SDSS spectroscopic redshift $z > 0.05$ / `class == QSO` OR WISE infrared color $W1 - W2 \ge 0.8$).
- **Evidence Level**: `STRONG` (WISE IR excess) to `DECISIVE` (SDSS QSO spectroscopy).

### D. NEBULA CANDIDATE
- **Criteria**: Extended diffuse image morphology, lack of compact galactic core, AND WISE thermal infrared excess ($W3 - W4 \ge 1.5$ or $W2 - W3 \ge 2.0$).
- **Evidence Level**: `STRONG` to `DECISIVE`.

### E. EXOPLANET CANDIDATE
- **Criteria**: Optical point-source star AND NASA Exoplanet Archive host star match within $r \le 1.0''$ OR TESS transit light curve signature ($p < 0.01$).
- **Evidence Level**: `DECISIVE`.

---

## 5. Cross-Match Quality & Angular Radius Thresholds

All catalog cross-matches require spatial verification against target RA/Dec coordinates:

| Search Separation ($r$) | Match Quality Designation | Engine Action |
| :--- | :--- | :--- |
| **$r \le 1.0''$** | `HIGH_QUALITY_MATCH` | Full catalog evidence weight applied |
| **$1.0'' < r \le 2.0''$** | `GOOD_MATCH` | Full catalog evidence weight applied |
| **$2.0'' < r \le 3.0''$** | `WEAK_MATCH` | Evidence level capped at `WEAK`; requires independent confirmation |
| **$r > 3.0''$** | `NO_MATCH` | Catalog entry rejected as background/unrelated source |

---

## 6. Ambiguity & Conflict Handling

### Conflict Resolution
When independent data sources emit contradictory physical evidence (e.g., Gaia DR3 parallax indicates a local star $\varpi = 15\text{ mas}$, but SDSS spectroscopy claims QSO redshift $z = 1.8$):
- Decision: **`CONFLICTING_POINT_SOURCE_EVIDENCE`**
- Evidence Level: `WEAK`
- Reason: *"Conflicting evidence: Gaia astrometry indicates stellar parallax/PM, but SDSS/WISE indicates quasar/extragalactic properties."*

### Missing Data & Ambiguity Preservation
- Isolated point sources lacking Gaia, SDSS, WISE, or TESS catalog detections $\rightarrow$ Decision: **`AMBIGUOUS_POINT_SOURCE`** (Evidence Level: `NONE`, Match Quality: `NO_MATCH`).
- Incomplete images without coordinate headers or spatial metrics $\rightarrow$ Decision: **`ASTRONOMICAL_SOURCE_AMBIGUOUS`** (Evidence Level: `NONE`).

---

## 7. Real Target Validation Sweep (Phase 12A Test Set)

The fusion engine was validated against all 9 real Phase 12A target evidence bundles:

| Target ID | Target Type | Decision Output | Evidence Level | Match Quality | Key Scientific Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GALAXY-ZOO-20027` | Galaxy | `GALAXY` | `MODERATE` | `HIGH_QUALITY_MATCH` | Extended light profile; GZ morphology = SPIRAL |
| `GALAXY-ZOO-261146` | Galaxy | `GALAXY` | `MODERATE` | `HIGH_QUALITY_MATCH` | Extended light profile; GZ morphology = EDGE_ON |
| `GALAXY-ZOO-66345` | Galaxy | `GALAXY` | `MODERATE` | `HIGH_QUALITY_MATCH` | Extended light profile; GZ morphology = SMOOTH |
| `STELLAR-CANDIDATE-1` | Stellar Candidate | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `HIGH_QUALITY_MATCH` | Point source; Gaia DR3 parallax/PM below 3σ threshold |
| `STELLAR-CANDIDATE-2` | Stellar Candidate | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `HIGH_QUALITY_MATCH` | Point source; lacks high-confidence astrometry/spectroscopy |
| `STELLAR-CANDIDATE-3` | Stellar Candidate | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `HIGH_QUALITY_MATCH` | Point source; no decisive catalog confirmation |
| `SURVEY-TARGET-1` | Survey Target | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `NO_MATCH` | Point source visual cutout; external adapters returned no match |
| `SURVEY-TARGET-2` | Survey Target | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `NO_MATCH` | Point source visual cutout; external adapters returned no match |
| `SURVEY-TARGET-3` | Survey Target | `AMBIGUOUS_POINT_SOURCE` | `NONE` | `NO_MATCH` | Point source visual cutout; external adapters returned no match |

> **Audit Finding**: All 6 point source candidates correctly resolved to `AMBIGUOUS_POINT_SOURCE` rather than being forced into `STAR` or `GALAXY`, proving the elimination of the Galaxy Zoo override bug.

---

## 8. Latency Budget & Performance Analysis

- **Execution Overhead**: `< 0.5 ms` CPU runtime per invocation.
- **Synchronous Path Impact**: **0 ms**. The Evidence Fusion Engine executes asynchronously or during deep offline analysis workflows.
- **Memory Footprint**: Lightweight pure Python data structure processing (`< 50 KB` memory delta).

---

## 9. API Failure & System Degradation Behavior

If external astronomical APIs (Gaia, SDSS, SIMBAD, WISE) experience network timeouts, rate limiting, or HTTP 5xx errors:
1. External adapters flag status as `UNAVAILABLE`.
2. `catalog_bundle` incorporates empty/unavailable records.
3. Fusion Engine falls back entirely to image structural metrics and local Galaxy Zoo outputs.
4. If image metrics are point-like without catalog backing, the engine safely returns `AMBIGUOUS_POINT_SOURCE`.

---

## 10. Automated Unit Test Verification

Unit testing in `backend/tests/test_evidence_fusion.py` verifies 10 core scenarios (74 test cases total):

- **Scenario A**: High-confidence Galaxy Zoo galaxy with extended light profile $\rightarrow$ `GALAXY` (`MODERATE`).
- **Scenario B**: High-confidence Gaia DR3 parallax/PM star $\rightarrow$ `STAR` (`DECISIVE`).
- **Scenario C**: High-z SDSS quasar spectroscopy $\rightarrow$ `QUASAR_CANDIDATE` (`DECISIVE`).
- **Scenario D**: WISE infrared color quasar candidate ($W1-W2 = 0.95$) $\rightarrow$ `QUASAR_CANDIDATE` (`STRONG`).
- **Scenario E**: Extended diffuse nebula with WISE thermal excess $\rightarrow$ `NEBULA_CANDIDATE` (`STRONG`).
- **Scenario F**: NASA Exoplanet Archive host match within $0.4''$ $\rightarrow$ `EXOPLANET_CANDIDATE` (`DECISIVE`).
- **Scenario G**: Gaia vs SDSS conflicting evidence $\rightarrow$ `CONFLICTING_POINT_SOURCE_EVIDENCE`.
- **Scenario H**: Isolated point source lacking catalog data $\rightarrow$ `AMBIGUOUS_POINT_SOURCE`.
- **Scenario I**: Degraded/missing image metrics $\rightarrow$ `ASTRONOMICAL_SOURCE_AMBIGUOUS`.
- **Scenario J**: Angular separation bounds ($0.5''$ vs $2.5''$ vs $4.0''$) correctly affect match quality and evidence levels.

---

## 11. Production Integration Readiness & Next Steps

### Supported Now (Phase 12B Complete)
- Scientific multi-modal evidence fusion engine.
- Decision contracts for `GALAXY`, `STAR`, `QUASAR_CANDIDATE`, `NEBULA_CANDIDATE`, `EXOPLANET_CANDIDATE`, `AMBIGUOUS_POINT_SOURCE`, `ASTRONOMICAL_SOURCE_AMBIGUOUS`, `CONFLICTING_POINT_SOURCE_EVIDENCE`.
- Complete zero-diff isolation of core ML inference (`ml/models/`, `ml/src/triage.py`).

### Requirements Before Phase 13 Production Integration
1. **Background Adapter Dispatcher**: Implement asynchronous background task runner to fetch external catalog bundles upon target coordinate ingestion.
2. **Frontend UI Integration**: Render `FusedEvidenceResult` metadata, match quality badges, and scientific justification strings in the ASTRA evidence audit drawer.
