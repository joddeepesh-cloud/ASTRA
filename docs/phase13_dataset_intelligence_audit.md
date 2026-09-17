# ASTRA Phase 13 — Dataset Intelligence Audit Report

## 1. Executive Summary & Dataset Acquisition Status

- **Dataset Source**: Google Drive archive (`1CR6Vk577Vggh0iuDhkkFZWKcKsFJyKE1`)
- **Local Download Path**: `data/phase13/dataset.zip` (487,032,642 bytes / ~487 MB)
- **Unpacked Path**: `data/phase13/unpacked/space images/`
- **Total Files Audited**: 1,107 JPEG image files (`.jpg`)
- **Total Subdirectories**: 6 category folders
- **Tabular / Catalog Files Count**: **0** (No `.csv`, `.tsv`, `.parquet`, `.json`, or `.fits` tabular catalog files were included in this Drive package)
- **Time-Series / Light Curve Files Count**: **0** (No time-series flux arrays or FITS time-series tables)
- **Spectroscopic Files Count**: **0** (No 1D wavelength/flux spectra or redshift tables)

---

## 2. Directory Structure & File-by-File Inventory

The downloaded Google Drive package contains 1,107 images scraped from Google Image search queries organized into 6 category folders:

| Folder Name | Relative Path | File Format | File Count | Width Range (px) | Height Range (px) | Avg Resolution (px) | Purpose Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **galaxies** | `space images/galaxies - Google Search/` | JPEG (`.jpg`) | 237 | 300 – 3600 | 150 – 3362 | $1222.9 \times 846.8$ | `UNAUTHENTICATED_WEB_IMAGES` |
| **constellation** | `space images/constellation - Google Search/` | JPEG (`.jpg`) | 183 | 291 – 4639 | 180 – 4767 | $1118.5 \times 836.0$ | `UNAUTHENTICATED_WEB_IMAGES` |
| **stars** | `space images/stars - Google Search/` | JPEG (`.jpg`) | 175 | 220 – 5472 | 146 – 5834 | $1323.9 \times 941.2$ | `UNAUTHENTICATED_WEB_IMAGES` |
| **planets** | `space images/planets - Google Search/` | JPEG (`.jpg`) | 176 | 360 – 8000 | 222 – 4500 | $1301.6 \times 843.9$ | `UNAUTHENTICATED_WEB_IMAGES` |
| **nebula** | `space images/nebula - Google Search/` | JPEG (`.jpg`) | 170 | 220 – 7680 | 262 – 4990 | $1599.7 \times 1154.2$ | `UNAUTHENTICATED_WEB_IMAGES` |
| **cosmos space** | `space images/cosmos space - Google Search/` | JPEG (`.jpg`) | 166 | 289 – 6016 | 180 – 4800 | $1344.6 \times 976.4$ | `UNAUTHENTICATED_WEB_IMAGES` |

---

## 3. Dataset Purpose & Scientific Feasibility Classification

| Dataset Component | Scientific Classification | Production Usability Status | Architectural Action |
| :--- | :--- | :--- | :--- |
| `galaxies` | `IMAGE_REFERENCE` | **Reference / Demonstration Only** | Do NOT use to retrain Galaxy Zoo morphology model |
| `constellation` | `NON_ASTRONOMICAL_GRAPHICS` | **Reject / Exclude** | Contains drawn constellation line diagrams and star maps |
| `stars` | `IMAGE_CANDIDATE` | **Reference Only** | Lacks Gaia astrometry/parallax metadata |
| `planets` | `ARTIST_IMPRESSIONS` | **Reject / Exclude** | Contains 3D computer renders and sci-fi art of solar system/exoplanets |
| `nebula` | `IMAGE_CANDIDATE` | **Reference Only** | Lacks $H\alpha$ emission spectroscopy or WISE thermal excess data |
| `cosmos space` | `WALLPAPER_ART` | **Reject / Exclude** | Stock wallpapers and composite Hubble/JWST promotional art |

---

## 4. Identifiers, Metadata & Join Key Audit

- **Equatorial Coordinates (RA / DEC)**: **NONE**. The web search images do not contain FITS headers or EXIF celestial coordinates.
- **Astronomical Catalog IDs**: **NONE**. No Gaia Source IDs, SDSS `objid`/`specobjid`, TIC IDs, KIC IDs, or NASA Exoplanet Archive host IDs are present.
- **Image Identifiers**: Generic numerical filenames (`1.jpg`, `2.jpg`, ..., `237.jpg`).
- **Join Capability**: Because celestial coordinates and catalog IDs are absent, these images **cannot** be directly joined with Gaia DR3, SDSS DR16, ALLWISE, TESS, or NASA Exoplanet Archive tables.

---

## 5. Domain Specific Audits

### A. Exoplanet Data Audit
- **Files Found**: `space images/planets - Google Search/` (176 images).
- **Time-Series / Light Curves**: **0**.
- **Confirmed Exoplanets**: Unverifiable (images consist of solar system planet photographs and 3D digital art concepts).
- **Transit Depth / Period / Duration**: **None**.
- **Conclusion**: Optical 2D images cannot establish exoplanet transit signatures. Exoplanet candidate status requires time-series photometry (TESS/Kepler) or NASA Exoplanet Archive TAP host matches.

### B. Star Data Audit
- **Files Found**: `space images/stars - Google Search/` (175 images).
- **Gaia DR3 Astrometry**: **None**.
- **Parallax ($\varpi$) / Proper Motion ($\mu$)**: **None**.
- **Ground Truth**: Classified as `POINT_SOURCE_ONLY` / `UNAUTHENTICATED_VISUAL_CANDIDATE`.
- **Conclusion**: Ground-truth stellar identification requires Gaia parallax $\varpi > 3\sigma_{\varpi}$, proper motion $\mu > 5\sigma_{\mu}$, or stellar spectroscopy.

### C. Quasar Data Audit
- **Files Found**: 0 explicit quasar folders.
- **Spectroscopic Redshift ($z$)**: **None**.
- **SDSS DR16Q Membership**: **None**.
- **Conclusion**: Quasar candidate classification requires SDSS spectroscopic redshift ($z > 0.05$), $QSO$ spectral class, or qualifying WISE IR colors ($W1-W2 \ge 0.8$).

---

## 6. Image vs. Time-Series vs. Catalog Separation

```
                       [ Input Data Stream ]
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
[ Optical Image ]        [ Catalog Metadata ]       [ Time-Series Flux ]
 2D Pixel Cutouts         RA / DEC / Gaia / SDSS     TESS / Kepler Light Curves
     │                           │                           │
     ▼                           ▼                           ▼
Local Structural          Catalog Adapter            Lightkurve Transit
  Analysis                 Cross-Match                 Search Pipeline
     │                           │                           │
     └───────────────────────────┼───────────────────────────┘
                                 ▼
                    [ Evidence Fusion Engine ]
                                 │
                                 ▼
                     Scientifically Justified
                        Object Decision
```

---

## 7. Conclusions & Recommended Action Plan

1. **Do NOT retrain existing ML models (`ml/models/`, `ml/src/triage.py`)**: Web-scraped images from Google Search contain artist renders, stock graphics, and constellation line diagrams that would degrade model calibration.
2. **Preserve existing canonical ML models**: EfficientNet-B0 Galaxy Zoo morphology model, MobileNetV3 Domain Gate V2, and OpenCLIP Semantic Gate remain 100% untouched.
3. **Build Phase 13 Multi-Modal Evidence Pipeline**:
   - Implement `Lightkurve` time-series evidence adapter (`backend/app/services/evidence/lightkurve_adapter.py`) to search TESS/Kepler light curves for transit signatures and flux variability.
   - Integrate NASA Exoplanet Archive TAP queries for host star cross-matching.
   - Enforce Level 0 to Level 4 Evidence Hierarchy in `EvidenceFusionEngine` to resolve `STAR`, `QUASAR_CANDIDATE`, `EXOPLANET_CANDIDATE`, `NEBULA_CANDIDATE`, and `AMBIGUOUS_POINT_SOURCE`.
