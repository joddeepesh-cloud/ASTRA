from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class EvidenceProvenance(BaseModel):
    """Scientific provenance metadata for individual evidence attributes."""
    source: str = Field(..., description="Originating catalog/mission (e.g., 'Gaia DR3', 'SDSS DR16Q')")
    field: str = Field(..., description="Target attribute name (e.g., 'parallax', 'redshift')")
    value: Optional[Any] = Field(default=None, description="Raw evidence value")
    unit: Optional[str] = Field(default=None, description="Physical unit (e.g., 'mas', 'mas/yr')")
    match_distance_arcsec: Optional[float] = Field(default=None, description="Angular separation in arcseconds")
    provenance: str = Field(default="external_catalog", description="Data provenance type ('external_catalog', 'image_structure', 'offline_stub')")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp of acquisition")
    quality_indicator: Optional[str] = Field(default=None, description="Quality or confidence flag from source provider")

class CatalogMatch(BaseModel):
    """Represents a cross-matched source entry from an external astronomical catalog."""
    catalog_name: str
    source_id: str
    ra: float
    dec: float
    match_distance_arcsec: float
    quality_flag: Optional[str] = None

class AstrometryEvidence(BaseModel):
    """Gaia DR3 astrometry and stellar magnitude evidence."""
    available: bool = False
    source: str = "Gaia DR3"
    source_id: Optional[str] = None
    parallax_mas: Optional[float] = None
    proper_motion_ra_mas_yr: Optional[float] = None
    proper_motion_dec_mas_yr: Optional[float] = None
    g_magnitude: Optional[float] = None
    bp_rp_color: Optional[float] = None
    match_distance_arcsec: Optional[float] = None
    quality_indicators: Dict[str, Any] = Field(default_factory=dict)
    stellar_evidence_score: Optional[float] = None

class SpectroscopyEvidence(BaseModel):
    """SDSS spectroscopic and quasar catalog evidence."""
    available: bool = False
    source: str = "SDSS DR16"
    source_id: Optional[str] = None
    redshift: Optional[float] = None
    spectral_class: Optional[str] = None
    is_quasar_catalog_member: bool = False
    broad_emission_lines_detected: bool = False
    match_distance_arcsec: Optional[float] = None
    quasar_evidence_score: Optional[float] = None

class PhotometryEvidence(BaseModel):
    """WISE infrared photometry evidence."""
    available: bool = False
    source: str = "ALLWISE"
    source_id: Optional[str] = None
    wise_w1: Optional[float] = None
    wise_w2: Optional[float] = None
    wise_w3: Optional[float] = None
    wise_w4: Optional[float] = None
    w1_minus_w2: Optional[float] = None
    quality_flags: Optional[str] = None
    match_distance_arcsec: Optional[float] = None

class TimeSeriesEvidence(BaseModel):
    """TESS / Kepler light curve time-series evidence."""
    available: bool = False
    mission: Optional[str] = None
    sector: Optional[int] = None
    time: List[float] = Field(default_factory=list)
    flux: List[float] = Field(default_factory=list)
    quality: List[int] = Field(default_factory=list)
    source_id: Optional[str] = None
    status: str = Field(default="NO_LIGHT_CURVE_AVAILABLE", description="'NO_LIGHT_CURVE_AVAILABLE', 'LIGHT_CURVE_AVAILABLE', 'LIGHT_CURVE_ANALYSIS_COMPLETED'")
    signal_hint: str = Field(default="INSUFFICIENT_DATA", description="'TRANSIT_LIKE_SIGNAL', 'PERIODIC_VARIABILITY', 'TRANSIENT_LIKE_VARIATION', 'NO_SIGNIFICANT_PERIODIC_SIGNAL', 'INSUFFICIENT_DATA'")

class ExoplanetEvidence(BaseModel):
    """NASA Exoplanet Archive host and transit evidence."""
    available: bool = False
    known_host: bool = False
    known_planet: bool = False
    candidate: bool = False
    planet_name: Optional[str] = None
    orbital_period_days: Optional[float] = None
    transit_depth_ppm: Optional[float] = None
    catalog_identifiers: Dict[str, str] = Field(default_factory=dict)
    match_distance_arcsec: Optional[float] = None

class NebulaEvidence(BaseModel):
    """Diffuse nebula / emission line catalog evidence."""
    available: bool = False
    is_catalog_nebula: bool = False
    catalog_name: Optional[str] = None
    nebula_type: Optional[str] = None
    h_alpha_emission_detected: bool = False
    match_distance_arcsec: Optional[float] = None

class TargetCoordinates(BaseModel):
    """Celestial target equatorial coordinates."""
    ra: Optional[float] = None
    dec: Optional[float] = None

class EvidenceBundle(BaseModel):
    """
    Unified ASTRA Multi-Modal Evidence Bundle.
    Aggregates cross-matched evidence from Gaia, SDSS, WISE, TESS, Exoplanet Archive, and Nebula catalogs.
    """
    target_coordinates: TargetCoordinates = Field(default_factory=TargetCoordinates)
    catalog_matches: List[CatalogMatch] = Field(default_factory=list)
    astrometry: AstrometryEvidence = Field(default_factory=AstrometryEvidence)
    spectroscopy: SpectroscopyEvidence = Field(default_factory=SpectroscopyEvidence)
    photometry: PhotometryEvidence = Field(default_factory=PhotometryEvidence)
    time_series: TimeSeriesEvidence = Field(default_factory=TimeSeriesEvidence)
    exoplanet: ExoplanetEvidence = Field(default_factory=ExoplanetEvidence)
    nebula: NebulaEvidence = Field(default_factory=NebulaEvidence)
    provenance_items: List[EvidenceProvenance] = Field(default_factory=list)
    availability_summary: Dict[str, bool] = Field(default_factory=dict)
    latency_ms: float = 0.0

class FusedEvidenceResult(BaseModel):
    """
    Result of synthesizing local image structural evidence with multi-modal external catalog evidence.
    """
    target_decision: str = Field(..., description="Final justified target status ('GALAXY', 'STAR', 'QUASAR_CANDIDATE', 'AMBIGUOUS_POINT_SOURCE', 'ASTRONOMICAL_SOURCE_AMBIGUOUS', 'INCOMPATIBLE', 'CONFLICTING_POINT_SOURCE_EVIDENCE')")
    primary_rationale: str = Field(..., description="Human-readable scientific rationale explaining the decision")
    evidence_level: str = Field(default="NONE", description="Overall evidence strength category ('NONE', 'WEAK', 'MODERATE', 'STRONG', 'DECISIVE')")
    match_quality: str = Field(default="UNAVAILABLE", description="Overall catalog match quality ('NO_MATCH', 'WEAK_MATCH', 'GOOD_MATCH', 'HIGH_QUALITY_MATCH', 'UNAVAILABLE')")
    is_conflicting: bool = Field(default=False, description="True if opposing signals exist across data modalities")
    image_evidence_type: str = Field(default="UNKNOWN", description="Target type from local image structural analysis")
    galaxy_evidence_strength: str = Field(default="NONE")
    stellar_evidence_strength: str = Field(default="NONE")
    quasar_evidence_strength: str = Field(default="NONE")
    nebula_evidence_strength: str = Field(default="NONE")
    exoplanet_evidence_status: str = Field(default="NO_CATALOG_MATCH")
    provenance_chain: List[EvidenceProvenance] = Field(default_factory=list)
    scientific_disclaimer: str = Field(default="Classification based on conservative multi-modal evidence contract.")

    @property
    def fused_object_type(self) -> str:
        return self.target_decision

    @property
    def scientific_justification(self) -> str:
        return self.primary_rationale

    @property
    def contributing_catalogs(self) -> List[str]:
        catalogs = []
        for p in self.provenance_chain:
            if p.source and p.source not in catalogs:
                catalogs.append(p.source)
        return catalogs

    @property
    def provenance(self) -> List[str]:
        return [f"{p.source}: {p.field}={p.value} ({p.interpretation})" for p in self.provenance_chain]

    @property
    def conflicts(self) -> List[str]:
        if self.is_conflicting or self.target_decision == "CONFLICTING_POINT_SOURCE_EVIDENCE":
            return [p.interpretation for p in self.provenance_chain if "conflict" in p.interpretation.lower() or "opposing" in p.interpretation.lower()] or [self.primary_rationale]
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_decision": self.target_decision,
            "fused_object_type": self.target_decision,
            "primary_rationale": self.primary_rationale,
            "scientific_justification": self.primary_rationale,
            "evidence_level": self.evidence_level,
            "match_quality": self.match_quality,
            "is_conflicting": self.is_conflicting,
            "image_evidence_type": self.image_evidence_type,
            "contributing_catalogs": self.contributing_catalogs,
            "provenance": self.provenance,
            "conflicts": self.conflicts,
            "scientific_disclaimer": self.scientific_disclaimer
        }


