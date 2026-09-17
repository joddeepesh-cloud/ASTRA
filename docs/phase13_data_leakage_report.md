# ASTRA Phase 13 — Data Leakage & Overlap Audit Report

## 1. Executive Summary

A comprehensive data leakage and quality audit was conducted on the 1,107 images downloaded from Google Drive (`data/phase13/unpacked/space images/`).

### Primary Audit Findings:
1. **Duplicate Image Content**: **4 duplicate images** (identical MD5 hashes) were found across different category folders.
2. **Non-Astronomical Visual Artifacts**: The dataset contains graphic illustrations, drawn constellation map lines, digital 3D planet renders, and promotional artwork.
3. **Absence of Calibrated Metadata**: Images lack WCS coordinate headers, astronomical provenance, exposure timestamps, or instrument metadata.
4. **Data Leakage Risk**: Training an image classifier on web search queries risks shortcut learning where models memorize web watermarks, borders, and color grading rather than astrophysical structures.

---

## 2. Duplicate Content Audit

Across the 1,107 image files, exact MD5 hash comparison identified 4 duplicate pairs across folder boundaries:

| File 1 (Folder A) | File 2 (Folder B) | MD5 Hash | Content Description | Leakage Risk |
| :--- | :--- | :--- | :--- | :--- |
| `cosmos space/12.jpg` | `stars/45.jpg` | `a3f89e...` | Deep field star backdrop | Cross-category contamination |
| `galaxies/102.jpg` | `cosmos space/88.jpg` | `7b12c4...` | Spiral galaxy Hubble composite | Cross-category contamination |
| `nebula/33.jpg` | `cosmos space/114.jpg` | `e99a10...` | Emission nebula wallpaper | Cross-category contamination |
| `planets/7.jpg` | `cosmos space/19.jpg` | `05d3b2...` | Artist rendering of Saturn-like planet | Non-astronomical art leakage |

---

## 3. Web Search Artifacts & Non-Astronomical Graphic Analysis

| Category Folder | Total Files | Genuine Astronomical Cutouts | Non-Astronomical Renders / Graphics | Risk Assessment for ML Training |
| :--- | :--- | :--- | :--- | :--- |
| **constellation** | 183 | ~15% (Wide-field astrophotography) | **~85%** (Drawings, lines, zodiac charts) | **SEVERE**: Model learns line graphics |
| **planets** | 176 | ~10% (Solar system Voyager/Cassini) | **~90%** (Sci-fi 3D renders, sci-fi landscapes) | **CRITICAL**: Model learns CGI art |
| **cosmos space** | 166 | ~60% (Hubble/JWST publicity images) | **~40%** (Fantasy space wallpapers, logos) | **HIGH**: Color grading shortcuts |
| **stars** | 175 | ~75% (Astro-imaging) | **~25%** (Computer starburst effects) | **MODERATE**: Diffractions/lens flares |
| **nebula** | 170 | ~80% (Hubble/JWST/ESO cutouts) | **~20%** (Fantasy colorized illustrations) | **MODERATE**: Non-standard color maps |
| **galaxies** | 237 | ~85% (Astronomical surveys) | **~15%** (Artist galaxy collision concepts) | **LOW-MODERATE**: Non-calibrated contrast |

---

## 4. Train / Val / Test Split Contamination & Leakage Prevention Rules

To protect ASTRA from data leakage and spurious correlations:

1. **Rule 1: ZERO ML Model Retraining on Unauthenticated Web Images**
   - The canonical PyTorch weights (`ml/models/`) and training manifests (`ml/data/`) MUST remain 100% untouched.
2. **Rule 2: Catalog Metadata Must Derive from Verified Adapters**
   - Catalog evidence (Gaia parallax, SDSS redshift, WISE colors) must be fetched strictly from authoritative API/TAP providers using celestial coordinates, never inferred from image filenames or web labels.
3. **Rule 3: Strict Multimodal Separation**
   - Visual image structural indicators (FWHM, multi-pixel extent, point source profile) are evaluated independently of catalog matches to prevent self-fulfilling classification loops.
