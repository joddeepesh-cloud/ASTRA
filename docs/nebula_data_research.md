# ASTRA Phase 11 — Nebula Data Research Report

## Executive Summary
This document records the research audit on public nebular, emission-line, and diffuse astronomical cloud datasets to determine requirements for eventual supervised training or multi-modal cross-matching for `NEBULA` object targets.

Currently, the local production dataset contains **0 ground-truth labeled nebula training images**.

---

## 1. Status Declaration

```text
NEBULA_MODEL_DATASET_NOT_YET_AVAILABLE
```

No labeled multi-wavelength or narrow-band nebula image dataset is currently downloaded or installed in `ml/data/`. Only 15 adversarial test cutouts (`adv_pos_nebular_fields_*.jpg`) exist in domain gate validation test sets.

---

## 2. Research on Public Candidate Nebula Datasets

### 2.1 SIMBAD Diffuse Cloud & Planetary Nebula Catalog
- **Candidate Source**: CDS SIMBAD Astronomical Database (Object Types: `PN` [Planetary Nebula], `HII` [H-II Region], `SNR` [Supernova Remnant], `Neb` [Nebula])
- **License**: Open Public Academic Domain (Creative Commons BY 4.0 / CDS License)
- **Data Modality**: Positional Catalog ($RA, DEC$), angular dimensions, radial velocity, spectral classification.
- **Labels**: Standard astronomical taxonomy (`PN`, `HII`, `SNR`, `Reflection Nebula`, `Dark Cloud`).
- **Emission-Line Information**: Secondary catalog references to $H\alpha \lambda 6563$, $[O III] \lambda 5007$, $[S II] \lambda 6716$ line flux ratios.
- **Suitability**: **Catalog Cross-Match Only** (Does not provide raw image cutouts directly; requires SkyView / HiPS image retrieval).

### 2.2 SuperCOSMOS $H\alpha$ Survey (SHS) / VPHAS+
- **Candidate Source**: AAO/UKST SuperCOSMOS $H\alpha$ Survey & ESO VPHAS+ (VLT Survey Telescope Photometric $H\alpha$ Survey)
- **License**: ESO / CASU Open Data Access
- **Data Modality**: Narrow-band $H\alpha$ ($656.3\text{nm}$) optical image cutouts ($FITS$ format).
- **Emission-Line Information**: Direct $H\alpha$ narrow-band filter images.
- **Suitability**: **High-Quality Supervised Training Target**. Combining $H\alpha$ filter images with broad-band $R$-filter continuum subtraction enables direct, robust machine-learning identification of ionized gas emission clouds.

### 2.3 WISE Mid-Infrared Dust & PAH Emission Maps
- **Candidate Source**: NASA ALLWISE / NEOWISE Sky Survey ($12\mu m$ [W3] and $22\mu m$ [W4] bands)
- **License**: NASA / IPAC Public Domain
- **Data Modality**: Multi-band IR FITS maps & JPEGs.
- **Emission-Line / Dust Information**: Traces Polycyclic Aromatic Hydrocarbon (PAH) dust emission and warm dust surrounding planetary nebulae and star-forming H-II regions.
- **Suitability**: **Multi-Modal Feature Fusion**. Mid-IR color ratios ($W3 - W4 > 2.0$) provide clear non-stellar nebular dust signatures.

---

## 3. Integration Strategy Recommendations

1. **Phase 1 (Current)**: Implement positional cross-matching via `NebulaAdapter` against CDS SIMBAD $PN / HII$ catalog tables.
2. **Phase 2 (Future Training Data Acquisition)**: Download a curated 5,000-image $H\alpha$ narrow-band cutout dataset from VPHAS+ / SHS for supervised multi-class training.
3. **Evidence Requirement for `NEBULA_CANDIDATE`**:
   - Image Structural Analysis: Extended diffuse emission ($diff\_score \ge 0.40$, $extent\_px \ge 100$, $concentration < 0.40$).
   - Multi-Modal Evidence: SIMBAD catalog match **OR** $H\alpha$ emission / WISE $W3-W4$ infrared color anomaly.
