# ASTRA Phase 12A — Real Evidence Connectivity Report

## Executive Summary
This document records the results of Phase 12A: Real Evidence Connectivity Proof. We executed real external TAP (Table Access Protocol) queries against ESA Gaia DR3, SDSS DR16, ALLWISE, MAST TESS, and the NASA Exoplanet Archive for 9 deterministic astronomical target coordinates extracted from `merged_zoo_data.csv.gz`.

The connectivity sweep successfully demonstrated that external multi-modal catalog evidence can be queried, structured, and serialized into `EvidenceBundle` instances with full scientific provenance without modifying local ML models (`ml/models/`), datasets (`ml/data/`), or core triage logic (`ml/src/triage.py`).

---

## 1. Selected Real Test Targets

| Target ID | Equatorial Coordinates ($RA, DEC$) | Category | Description |
| :--- | :--- | :--- | :--- |
| `GALAXY-ZOO-20027` | $RA = 181.341640^\circ, DEC = 3.537008^\circ$ | GALAXY | Known SDSS Galaxy Zoo 2 galaxy cutout (`asset_id` 20027) |
| `GALAXY-ZOO-261146` | $RA = 233.038940^\circ, DEC = 23.283297^\circ$ | GALAXY | Known SDSS Galaxy Zoo 2 galaxy cutout (`asset_id` 261146) |
| `GALAXY-ZOO-66345` | $RA = 246.607600^\circ, DEC = 34.280483^\circ$ | GALAXY | Known SDSS Galaxy Zoo 2 galaxy cutout (`asset_id` 66345) |
| `STELLAR-CANDIDATE-587738...` | $RA = 149.084990^\circ, DEC = 69.700100^\circ$ | STAR_CANDIDATE | Compact point-source cutout with high star vote fraction ($0.42$) |
| `STELLAR-CANDIDATE-588017...` | $RA = 187.698140^\circ, DEC = 12.388354^\circ$ | STAR_CANDIDATE | Compact point-source cutout with star vote fraction ($0.45$) |
| `STELLAR-CANDIDATE-588017...` | $RA = 187.435440^\circ, DEC = 8.008245^\circ$ | STAR_CANDIDATE | Compact point-source cutout with star vote fraction ($0.41$) |
| `SURVEY-TARGET-227418` | $RA = 144.804230^\circ, DEC = 32.682613^\circ$ | DIVERSE_SURVEY_TARGET | Diverse survey cutout (`asset_id` 227418) |
| `SURVEY-TARGET-59289` | $RA = 173.300310^\circ, DEC = 6.424842^\circ$ | DIVERSE_SURVEY_TARGET | Diverse survey cutout (`asset_id` 59289) |
| `SURVEY-TARGET-7212` | $RA = 128.399900^\circ, DEC = 50.648518^\circ$ | DIVERSE_SURVEY_TARGET | Diverse survey cutout (`asset_id` 7212) |

Full target specifications stored in [`docs/phase12_real_evidence_targets.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/docs/phase12_real_evidence_targets.json).

---

## 2. Real Query Results & Adapter Connectivity

### 2.1 Gaia DR3 Astrometry Results (`gaia_adapter.py`)
- **Status**: **100% Match Rate (9/9 targets returned real matches)**
- **Sample Real Values**:
  - `STELLAR-CANDIDATE-587738067813924971`: Source ID `1070573856125478016`, $G_{mag} = 21.34$, $BP - RP = 1.31$, match distance $= 20.3\text{ arcsec}$.
  - `STELLAR-CANDIDATE-588017703470628953`: Source ID `3907709443748318976`, $G_{mag} = 20.27$, $BP - RP = 1.37$, match distance $= 16.2\text{ arcsec}$.
  - `GALAXY-ZOO-20027`: Source ID `3892985986620412544`, $G_{mag} = 20.16$, $BP - RP = 1.32$, match distance $= 0.06\text{ arcsec}$.

### 2.2 ALLWISE Infrared Photometry Results (`wise_adapter.py`)
- **Status**: **66.7% Match Rate (6/9 targets returned real matches)**
- **Sample Real Values**:
  - `GALAXY-ZOO-20027`: AllWISE ID `J120521.99+033213.2`, $W1 = 13.570$, $W2 = 13.311$, $W3 = 9.613$, $W4 = 8.044$, $W1 - W2 = 0.259\text{ mag}$, match distance $= 0.03\text{ arcsec}$.
  - `SURVEY-TARGET-227418`: AllWISE ID `J093913.01+324057.4`, $W1 = 14.120$, $W2 = 13.980$, $W1 - W2 = 0.140\text{ mag}$, match distance $= 0.01\text{ arcsec}$.

### 2.3 SDSS DR16, TESS, and NASA Exoplanet Archive
- **SDSS DR16**: Returned `UNAVAILABLE` (network query failure on public API endpoint). Handled gracefully as `spectroscopy.available = False`.
- **TESS**: Returned `NO_LIGHT_CURVE_AVAILABLE` / `UNAVAILABLE`. Handled gracefully as `time_series.available = False`.
- **NASA Exoplanet Archive**: Returned `NO_MATCH` for non-exoplanet host coordinates. Handled gracefully as `exoplanet.available = False`.

---

## 3. Latency Distribution Summary

| Service / Adapter | Mean Latency | Median Latency | P95 Latency | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Gaia DR3** | **1,648.62 ms** | **1,751.16 ms** | **2,279.63 ms** | **COMPLETED (Real Data)** |
| **ALLWISE** | **1,536.46 ms** | **1,213.72 ms** | **2,569.25 ms** | **COMPLETED (Real Data)** |
| **SDSS DR16** | 1,979.37 ms | 2,239.97 ms | 2,491.12 ms | Handled (Fallback) |
| **TESS** | 1,075.49 ms | 1,141.57 ms | 1,746.37 ms | Handled (Fallback) |
| **NASA Exoplanet Archive** | 3,212.50 ms | 2,966.58 ms | 4,378.45 ms | Handled (Fallback) |

*Note: Out-of-band evidence lookups take ~1.5–3.2 seconds total, proving why they MUST run asynchronously without blocking local image inference (~15–40 ms).*

---

## 4. Scientific Field Classification Matrix

Every attribute in `EvidenceBundle` is strictly classified into one of four scientific evidence categories:

| Attribute / Field | Source Provider | Scientific Category | Rationale |
| :--- | :--- | :--- | :--- |
| `parallax_mas`, `proper_motion` | Gaia DR3 | `DIRECT_CATALOG_EVIDENCE` | Direct astrometric measurement from space telescope |
| `g_magnitude`, `bp_rp_color` | Gaia DR3 | `DIRECT_CATALOG_EVIDENCE` | Direct optical band flux measurement |
| `w1_mag`, `w2_mag`, `w3_mag`, `w4_mag` | ALLWISE | `DIRECT_CATALOG_EVIDENCE` | Direct mid-infrared band flux measurement |
| `w1_minus_w2` | ALLWISE | `DERIVED_FROM_CATALOG` | Derived color index ($W1 - W2$) tracing AGN IR excess |
| `redshift`, `spectral_class` | SDSS DR16 | `DIRECT_CATALOG_EVIDENCE` | Direct spectroscopic fit measurement |
| `fwhm_proxy_px`, `extent_px` | ASTRA Image Engine | `IMAGE_EVIDENCE` | Image-derived pixel structural measurement |
| `is_extended_like`, `point_source_score` | ASTRA Image Engine | `IMAGE_EVIDENCE` | Image-derived light distribution metric |
| `tess_light_curve` | TESS | `UNAVAILABLE` | Time-series data currently unavailable |

---

## 5. Failure & Exception Isolation
- **Network Failures**: Network query timeouts and HTTP 400/500 errors were caught cleanly by adapter `try...except` blocks.
- **Null Safety**: Targets with zero catalog matches returned `status = "NO_MATCH"` with `available = False` without raising exceptions.
- **Scientific Integrity**: API failures resolve to `EVIDENCE_UNAVAILABLE`, **never** triggering false predictions or defaults.

---

## 6. Future Evidence Requirements for Target Taxonomy

1. **Sufficient Evidence for Future `STAR`**:
   - Compact unresolved point source ($FWHM \le 14\text{px}$, $is\_point\_source = True$) **PLUS** Gaia DR3 parallax ($\varpi > 0$) or proper motion ($\mu > 3\text{ mas/yr}$).
2. **Sufficient Evidence for Future `QUASAR CANDIDATE`**:
   - Compact unresolved point source ($FWHM \le 16\text{px}$) **PLUS** spectroscopic redshift ($z > 0.1$) or ALLWISE color excess ($W1 - W2 > 0.8\text{ mag}$).
3. **Current Supported Status**:
   - `GALAXY`, `AMBIGUOUS POINT SOURCE`, `ASTRONOMICAL SOURCE AMBIGUOUS`, and `INCOMPATIBLE` remain the **only** active decisions. Catalog matches are stored in `EvidenceBundle` as enhancement data and do **not** force production object decisions yet.

---

## 7. Results Serialization
Full serialized evidence bundles with scientific provenance for all 9 real targets are saved to [`docs/phase12_real_evidence_results.json`](file:///Users/deepeshjoshi/Desktop/ASTRA/docs/phase12_real_evidence_results.json).
