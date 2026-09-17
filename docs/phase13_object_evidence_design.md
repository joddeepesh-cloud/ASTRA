# ASTRA Phase 13 — Multi-Modal Object Evidence Architecture Design

## 1. Overview & Conceptual Architecture

Phase 13 establishes a multi-modal, evidence-driven object assessment system that synthesizes local image structural indicators with multi-modal astronomical evidence (Gaia DR3 astrometry, SDSS DR16 spectroscopy, ALLWISE IR photometry, TESS time-series photometry via Lightkurve, NASA Exoplanet Archive TAP queries, and SIMBAD diffuse catalog matches).

```
                        [ INPUT OBSERVATION ]
                       (Image + Target RA/Dec)
                                 │
     ┌───────────────────────────┴───────────────────────────┐
     ▼                                                       ▼
[ Local Inference Path ]                         [ Async Evidence Path ]
 (Fast ~15-40 ms)                                (Non-blocking Background)
 ├─ Stage 1: Semantic Gate                        ├─ Gaia DR3 Astrometry
 ├─ Stage 2: Domain Gate V2                       ├─ SDSS DR16 Spectroscopy
 ├─ Stage 3: Object Router V2                     ├─ ALLWISE Photometry
 └─ Stage 4: Galaxy Zoo (Conditional)             ├─ Lightkurve TESS Time-Series
                                                  ├─ NASA Exoplanet Archive
                                                  └─ SIMBAD Diffuse Catalog
                                                             │
     ┌───────────────────────────────────────────────────────┘
     ▼
[ Evidence Fusion Engine ]
     │
     ├─► Level 0: Image Compatibility Only ───────► ASTRONOMICAL_SOURCE_AMBIGUOUS
     ├─► Level 1: Point Source Structure ────────► AMBIGUOUS_POINT_SOURCE
     ├─► Level 2: Point Source + Gaia ────────────► STAR
     ├─► Level 3: Point Source + SDSS / WISE ─────► QUASAR_CANDIDATE
     ├─► Level 4: Lightkurve / NASA Archive ──────► EXOPLANET_CANDIDATE / KNOWN_EXOPLANET_MATCH
     └─► Opposing Multi-Modal Signals ────────────► CONFLICTING_POINT_SOURCE_EVIDENCE
```

---

## 2. Evidence Hierarchy & Decision Contracts

### Level 0: Image Compatibility Only
- **Trigger**: Image passes Domain Gate V2, but spatial extent and catalog coverage are unavailable.
- **Output Decision**: **`ASTRONOMICAL_SOURCE_AMBIGUOUS`**
- **Evidence Level**: `NONE`

### Level 1: Point Source Visual Structure
- **Trigger**: Point-like visual light profile without catalog cross-matches within search radius.
- **Output Decision**: **`AMBIGUOUS_POINT_SOURCE`**
- **Evidence Level**: `NONE` / `WEAK`

### Level 2: Point Source + Independent Stellar Astrometry
- **Trigger**: Point-like visual light profile AND (Gaia DR3 parallax $\varpi > 3\sigma_{\varpi}$ OR proper motion $\mu > 5\sigma_{\mu}$ OR SDSS stellar spectroscopy).
- **Output Decision**: **`STAR`**
- **Evidence Level**: `DECISIVE` (Parallax/Spectroscopy) / `STRONG` (Proper Motion)

### Level 3: Point Source + Independent Quasar Evidence
- **Trigger**: Point-like visual light profile AND (SDSS spectroscopic redshift $z > 0.05$ / `class == QSO` OR WISE color $W1-W2 \ge 0.8$).
- **Output Decision**: **`QUASAR_CANDIDATE`**
- **Evidence Level**: `DECISIVE` (SDSS Spectroscopy) / `STRONG` (WISE IR Excess)

### Level 4: Time-Series / Exoplanet Evidence
- **Trigger**: Point-like optical star AND (NASA Exoplanet Archive host match within $r \le 1.0''$ OR TESS transit signature $p < 0.01$).
- **Output Decision**: **`KNOWN_EXOPLANET_MATCH`** (Archive match) / **`EXOPLANET_CANDIDATE`** (Transit signature)
- **Evidence Level**: `DECISIVE`

### Conflicting Multi-Modal Signals
- **Trigger**: Gaia astrometry indicates stellar parallax/PM ($\varpi > 3\sigma$), but SDSS/WISE indicates quasar redshift ($z > 0.1$) or extragalactic nature.
- **Output Decision**: **`CONFLICTING_POINT_SOURCE_EVIDENCE`**
- **Evidence Level**: `WEAK`

---

## 3. Lightkurve Time-Series Photometry Integration Design

The Lightkurve time-series pipeline retrieves TESS / Kepler light curves asynchronously via MAST:

```
[ Target RA / DEC ]
       │
       ▼
[ Lightkurve / MAST Search ]
       │
       ├──► No Target Light Curve Found ────────► status: NO_TIME_SERIES_AVAILABLE
       │
       └──► Target Light Curve Available ───────► status: TIME_SERIES_FOUND
                 │
                 ▼
     [ Light Curve Analysis ]
     ├─ Periodicity Search (BLS / Lomb-Scargle)
     ├─ Flux Dip Detection (Transit depth & duration)
     └─ Signal-to-Noise Ratio (SNR)
                 │
                 ├──► Transit Dip Detected (SNR > 3.0, Depth > 0.05%) ──► TRANSIT_LIKE_SIGNAL
                 └──► Variable / Non-transit flux ───────────────────────► VARIABLE_STAR_SIGNAL
```

### Time-Series Evidence Schema (`TimeSeriesEvidence`):
- `time_series_status`: `NO_TIME_SERIES_AVAILABLE` | `TIME_SERIES_FOUND` | `TRANSIT_LIKE_SIGNAL` | `VARIABLE_STAR_SIGNAL` | `UNAVAILABLE`
- `observation_count`: Integer count of photometric cadence points
- `baseline_duration_days`: Duration of light curve observation window
- `period_days`: Candidate orbital/variability period
- `transit_depth`: Fraction of flux dip ($|\Delta F / F|$)
- `transit_duration_hours`: Duration of flux dip
- `transit_snr`: Signal-to-noise ratio of periodic transit signal

---

## 4. NASA Exoplanet Archive TAP Query Integration

Programmatic queries execute against the NASA Exoplanet Archive TAP service (`https://exoplanetarchive.ipac.caltech.edu/TAP/sync`):

```sql
SELECT pl_name, hostname, ra, dec, pl_orbper, pl_trandep, discoverymethod, disc_facility
FROM pscomppars
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, 0.000833)) = 1
```

### Exoplanet Evidence Schema (`ExoplanetEvidence`):
- `exoplanet_status`: `NO_CATALOG_MATCH` | `KNOWN_EXOPLANET_MATCH` | `KNOWN_HOST_STAR` | `CANDIDATE_HOST`
- `planet_name`: Confirmed exoplanet designation (e.g. `TOI-700 d`)
- `hostname`: Host star designation (e.g. `TOI-700`)
- `discovery_method`: E.g. `Transit`, `Radial Velocity`
- `orbital_period_days`: Candidate/confirmed orbital period

---

## 5. Black Hole Evidence Pathway Design

> **Rule**: Black holes MUST NEVER be classified directly from an optical image alone.

For Phase 13, direct black hole classification is explicitly set to `BLACK_HOLE_DIRECT_CLASSIFICATION = NOT_SUPPORTED`.

Future multi-modal pathway:
```
[ Optical Image ] + [ SDSS Spectroscopy (Broad Balmer/Fe lines) ] + [ X-Ray / Radio Catalog Match ] + [ Host Galaxy Nucleus Centroid ]
  └─────────────► BLACK_HOLE_RELATED_CANDIDATE (Active Galactic Nucleus / Quasar Core)
```

---

## 6. Provenance Tracking & Conflict Handling

Every evidence item logs:
- `source`: E.g. `Gaia DR3`, `SDSS DR16`, `ALLWISE`, `Lightkurve / TESS`, `NASA Exoplanet Archive`
- `evidence_type`: E.g. `ASTROMETRIC_PARALLAX`, `SPECTROSCOPIC_REDSHIFT`, `TIME_SERIES_TRANSIT`, `EXOPLANET_HOST_MATCH`
- `match_distance_arcsec`: Angular separation from target coordinates
- `provenance_chain`: Structured list of provenances attached to the observation dossier
