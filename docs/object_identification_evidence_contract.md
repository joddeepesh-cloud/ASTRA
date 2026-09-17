# ASTRA Scientific Evidence Fusion Contract

## Executive Summary
This contract defines the explicit evidence threshold rules governing ASTRA's target object classification taxonomy. Under no circumstances should ASTRA force or manufacture a definitive object classification (`STAR`, `QUASAR`, `NEBULA`, `GALAXY`) when supporting evidence is ambiguous or insufficient.

---

## Target Decision Contracts

```mermaid
flowchart TD
    A["Input Observation"] --> B{"Stage 1 & 2 Domain Gate"}
    B -->|Non-Astronomical| C["INCOMPATIBLE — IMAGE REJECTED"]
    B -->|Astronomical| D{"Pixel Structural Analysis"}

    D -->|Extended Profile + Galaxy Morphology| E{"Galaxy Zoo / Visual Model"}
    E -->|Strong Extended Light Distribution| F["GALAXY"]

    D -->|Diffuse Cloud Profile| G{"Nebula Catalog / Emission Evidence"}
    G -->|Diffuse Profile + H-alpha / IR Dust Match| H["NEBULA_CANDIDATE"]
    G -->|Diffuse Profile Alone (No Catalog/Line Evidence)| I["ASTRONOMICAL_SOURCE_AMBIGUOUS"]

    D -->|Unresolved Point Source| J{"Gaia Astrometry / SDSS Spectroscopy"}
    J -->|Parallax > 0 OR Proper Motion > 0| K["STAR"]
    J -->|Redshift z > 0.1 OR Broad Lines OR W1-W2 > 0.8| L["QUASAR CANDIDATE"]
    J -->|No Spectroscopic / Astrometric Cross-Match| M["AMBIGUOUS POINT SOURCE"]

    D -->|Low SNR / Weak Feature Profile| I
```

---

### 1. `GALAXY`
- **Required Evidence**:
  - Image Structural Analysis: Extended astronomical light profile ($ext\_score \ge 0.35$, $FWHM \ge 16.0\text{px}$, $extent\_px \ge 8000$, non-point-source).
  - OpenCLIP Zero-Shot / Supervised Galaxy Model: High similarity to galaxy prompt ensemble ($top\_score \ge 0.25$, $margin \ge 0.10$).
- **Secondary Specialist Execution**:
  - **If and only if** `GALAXY` is established, Galaxy Zoo morphology triage executes to determine `SMOOTH`, `FEATURED_DISK`, `EDGE_ON`, or `SPIRAL`. Galaxy Zoo morphology outputs **never** infer galaxy status independently.

---

### 2. `NEBULA_CANDIDATE`
- **Required Evidence**:
  - Image Structural Analysis: Diffuse extended emission ($diff\_score \ge 0.40$, $extent\_px \ge 100$, $concentration < 0.42$).
  - Multi-Modal Supporting Evidence: SIMBAD catalog match ($PN / HII$), $H\alpha$ emission line detection, or ALLWISE infrared dust color excess ($W3 - W4 > 2.0$).
- **Fallback Rule**: Diffuse structure **without** catalog emission line evidence resolves to `ASTRONOMICAL_SOURCE_AMBIGUOUS`.

---

### 3. `STAR`
- **Required Evidence**:
  - Image Structural Analysis: Unresolved compact point source ($FWHM \le 14\text{px}$, $compactness \ge 0.05$, $pt\_score \ge 0.55$).
  - Multi-Modal Supporting Evidence: Gaia DR3 astrometric parallax ($\varpi > 0$) **OR** significant proper motion ($\sqrt{\mu_{\alpha}^{*2} + \mu_{\delta}^2} > 3.0\text{ mas/yr}$) **OR** stellar spectrographic match.
- **Fallback Rule**: Point sources without astrometric parallax/proper motion or spectroscopy **must not** be called `STAR`. They resolve to `AMBIGUOUS_POINT_SOURCE`.

---

### 4. `QUASAR CANDIDATE`
- **Required Evidence**:
  - Image Structural Analysis: Compact point-like core ($FWHM \le 16\text{px}$).
  - Multi-Modal Supporting Evidence: SDSS spectroscopic redshift ($z > 0.1$) **OR** broad emission lines ($Mg II, C IV$) **OR** DR16Q catalog membership **OR** ALLWISE infrared color excess ($W1 - W2 > 0.8$).
- **Fallback Rule**: OpenCLIP predicting "quasar" on a single-band optical image **never** produces `QUASAR CANDIDATE` without catalog/spectroscopic evidence. Unresolved point sources without spectroscopy resolve to `AMBIGUOUS_POINT_SOURCE`.

---

### 5. `AMBIGUOUS POINT SOURCE`
- **Required Evidence**:
  - Image Structural Analysis: Confirmed unresolved compact point source ($FWHM \le 14\text{px}$, $is\_point\_source = True$).
  - Catalog Status: No Gaia DR3 parallax/proper motion match **AND** no SDSS spectroscopic redshift match available.
- **Scientific Integrity Principle**: This is a scientifically correct, honest result acknowledging optical resolution limits.

---

### 6. `ASTRONOMICAL SOURCE AMBIGUOUS`
- **Required Evidence**:
  - Image Domain: Confirmed astronomical observation by Domain Gate V2.
  - Image Structure: Low SNR, featureless image, weak diffuse light without nebular line evidence, or ambiguous margin between competing hypotheses ($margin < 0.10$).

---

### 7. `INCOMPATIBLE — IMAGE REJECTED`
- **Required Evidence**:
  - Universal Semantic Gate status `SEMANTIC_INCOMPATIBLE` **OR** Domain Gate V2 decision `INCOMPATIBLE`.
  - Content: Terrestrial scenes, maps, equipment, artwork, software screenshots, satellite imagery. No astronomical classification performed.
