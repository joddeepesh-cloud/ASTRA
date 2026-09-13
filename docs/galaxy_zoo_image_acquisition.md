# ASTRA — Galaxy Zoo 10,000 Image Acquisition & Validation Report

**Project**: ASTRA — AI-Based Astronomical Observation Triage System  
**Document Path**: `docs/galaxy_zoo_image_acquisition.md`  
**Output Directory**: `ml/data/processed/galaxy_zoo/images/`  
**Manifest Path**: `ml/data/processed/galaxy_zoo/manifest.csv`  
**Subset CSV Used**: `ml/data/splits/subset_10k_archive_compatible_splits.csv`  
**Date**: September 10, 2026  
**Execution Environment**: `/Users/deepeshjoshi/Desktop/ASTRA/.venv`  

---

## 1. Executive Summary

Exactly **10,000 required original Galaxy Zoo 2 JPEG images** were selectively extracted from `~/Downloads/galaxy-zoo-2-images.zip` into `ml/data/processed/galaxy_zoo/images/`.

All 10,000 images were 100% validated using Pillow ($424 \times 424$ RGB JPEGs) with **zero corrupted files**, zero missing files, and zero extra/unexpected files.

Following successful validation and manifest generation, the 3.06 GB local ZIP archive was permanently deleted, resulting in a tiny net storage footprint of **~161.7 MB** for the entire 10,000 image dataset.

---

## 2. Acquisition & Extraction Metrics

| Metric | Value |
| :--- | :--- |
| **Source Archive Name** | `galaxy-zoo-2-images.zip` |
| **Archive Source Location** | `~/Downloads/galaxy-zoo-2-images.zip` (Local download) |
| **Archive Size** | `3.056 GB` (3,281,862,708 bytes) |
| **Archive Total Members** | `243,438` |
| **Subset CSV Used** | `subset_10k_archive_compatible_splits.csv` |
| **Required Target Images** | `10,000` |
| **Extracted Images** | `10,000` |
| **Valid Images (Pillow Verified)** | `10,000` (100.0%) |
| **Corrupted Images** | `0` |
| **Missing Images** | `0` |
| **Unexpected / Extra Images** | `0` |
| **Image Resolution & Mode** | `424x424 RGB` |
| **Extracted Dataset Size** | `131.01 MB` (~0.1279 GB) |
| **Manifest File** | `ml/data/processed/galaxy_zoo/manifest.csv` (`10,000` rows) |

---

## 3. Disk Space & Storage Impact

| Storage Metric | Value |
| :--- | :--- |
| **Available Disk Space Before Extraction** | `102.97 GB` |
| **Local ZIP Archive Size Deleted** | `3.056 GB` |
| **Extracted Dataset Size Retained** | `131.01 MB` |
| **Available Disk Space After Cleanup** | `105.88 GB` |
| **Net Storage Increase** | `+131.01 MB` |

---

## 4. Final Verification Checklist

- [x] **Selective Extraction**: Extracted ONLY the 10,000 required JPEGs; remaining ~233k images were NOT extracted.
- [x] **Zero Content Modification**: Images preserved in original $424 \times 424$ resolution with zero cropping, resizing, or recompression.
- [x] **File Count Integrity**: Exactly 10,000 JPG files present in `ml/data/processed/galaxy_zoo/images/`.
- [x] **Pillow Header Verification**: All 10,000 JPEGs opened cleanly with non-zero dimensions and valid RGB modes.
- [x] **Manifest Synchronization**: 10,000 manifest rows match physical image properties 1-to-1.
- [x] **Local ZIP Cleanup**: `~/Downloads/galaxy-zoo-2-images.zip` verified deleted.
- [x] **Raw Datasets Intact**: All raw metadata files in `ml/data/raw/galaxy_zoo/` and `ml/data/splits/` remain 100% untouched.
