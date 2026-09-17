import pytest
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, AstrometryEvidence, SpectroscopyEvidence, PhotometryEvidence,
    ExoplanetEvidence, NebulaEvidence, CatalogMatch
)
from backend.app.services.evidence.evidence_fusion import EvidenceFusionEngine

@pytest.fixture
def fusion_engine():
    return EvidenceFusionEngine()

def test_scenario_a_strong_galaxy_evidence(fusion_engine):
    """Scenario A: Extended image profile + Galaxy Zoo morphology -> GALAXY."""
    local_res = {
        "predicted_object_type": "GALAXY",
        "predicted_class": "FEATURED_DISK",
        "morphology": "FEATURED_DISK"
    }
    bundle = EvidenceBundle()
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "GALAXY"
    assert res.evidence_level == "STRONG"
    assert res.is_conflicting is False

def test_scenario_b_point_source_strong_gaia_stellar_evidence(fusion_engine):
    """Scenario B: Point source + strong Gaia stellar parallax -> STAR."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        astrometry=AstrometryEvidence(
            available=True,
            source_id="Gaia-587726",
            parallax_mas=5.21,
            proper_motion_ra_mas_yr=-14.2,
            match_distance_arcsec=0.15
        ),
        catalog_matches=[CatalogMatch(catalog_name="Gaia DR3", source_id="Gaia-587726", ra=180.0, dec=45.0, match_distance_arcsec=0.15)]
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "STAR"
    assert res.stellar_evidence_strength in ["STRONG", "DECISIVE"]
    assert res.match_quality == "HIGH_QUALITY_MATCH"
    assert res.is_conflicting is False

def test_scenario_c_point_source_strong_sdss_quasar_evidence(fusion_engine):
    """Scenario C: Point source + strong SDSS spectroscopic redshift -> QUASAR_CANDIDATE."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        spectroscopy=SpectroscopyEvidence(
            available=True,
            source_id="SDSS-J1200",
            redshift=1.85,
            spectral_class="QSO",
            is_quasar_catalog_member=True,
            match_distance_arcsec=0.22
        ),
        catalog_matches=[CatalogMatch(catalog_name="SDSS DR16Q", source_id="SDSS-J1200", ra=180.0, dec=45.0, match_distance_arcsec=0.22)]
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "QUASAR_CANDIDATE"
    assert res.quasar_evidence_strength in ["STRONG", "DECISIVE"]
    assert res.is_conflicting is False

def test_scenario_d_point_source_no_decisive_evidence(fusion_engine):
    """Scenario D: Point source + no decisive evidence -> AMBIGUOUS_POINT_SOURCE."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle()
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "AMBIGUOUS_POINT_SOURCE"
    assert res.evidence_level == "NONE"
    assert "Multi-modal evidence is insufficient" in res.primary_rationale

def test_scenario_e_diffuse_source_without_nebula_evidence(fusion_engine):
    """Scenario E: Diffuse source without catalog/emission line evidence -> ASTRONOMICAL_SOURCE_AMBIGUOUS."""
    local_res = {"predicted_object_type": "NEBULA_CANDIDATE"}
    bundle = EvidenceBundle()
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "ASTRONOMICAL_SOURCE_AMBIGUOUS"
    assert res.nebula_evidence_strength == "WEAK"
    assert "supporting emission-line" in res.primary_rationale

def test_scenario_f_non_astronomical_input(fusion_engine):
    """Scenario F: Non-astronomical input -> INCOMPATIBLE."""
    local_res = {
        "predicted_object_type": "INCOMPATIBLE",
        "domain_validation": {"decision": "INCOMPATIBLE"}
    }
    bundle = EvidenceBundle()
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "INCOMPATIBLE"
    assert res.evidence_level == "NONE"

def test_scenario_g_gaia_quasar_evidence_conflict(fusion_engine):
    """Scenario G: Gaia parallax AND SDSS quasar redshift present -> CONFLICTING_POINT_SOURCE_EVIDENCE."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        astrometry=AstrometryEvidence(
            available=True,
            parallax_mas=4.5,
            proper_motion_ra_mas_yr=10.0,
            match_distance_arcsec=0.2
        ),
        spectroscopy=SpectroscopyEvidence(
            available=True,
            redshift=1.92,
            spectral_class="QSO",
            is_quasar_catalog_member=True,
            match_distance_arcsec=0.3
        ),
        catalog_matches=[
            CatalogMatch(catalog_name="Gaia DR3", source_id="Gaia-1", ra=180.0, dec=45.0, match_distance_arcsec=0.2),
            CatalogMatch(catalog_name="SDSS DR16", source_id="SDSS-1", ra=180.0, dec=45.0, match_distance_arcsec=0.3)
        ]
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "CONFLICTING_POINT_SOURCE_EVIDENCE"
    assert res.is_conflicting is True
    assert "Conflicting multi-modal evidence" in res.primary_rationale

def test_scenario_h_catalog_api_unavailable(fusion_engine):
    """Scenario H: Catalog lookup unavailable does not crash or downgrade incorrectly."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        astrometry=AstrometryEvidence(available=False),
        spectroscopy=SpectroscopyEvidence(available=False)
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "AMBIGUOUS_POINT_SOURCE"
    assert res.match_quality == "UNAVAILABLE"

def test_scenario_i_nearby_poor_angular_match(fusion_engine):
    """Scenario I: Match distance 2.8 arcsec is WEAK_MATCH and does not force decision."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        astrometry=AstrometryEvidence(
            available=True,
            parallax_mas=0.01,
            match_distance_arcsec=2.8
        ),
        catalog_matches=[CatalogMatch(catalog_name="Gaia DR3", source_id="Gaia-Far", ra=180.0, dec=45.0, match_distance_arcsec=2.8)]
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "AMBIGUOUS_POINT_SOURCE"
    assert res.match_quality == "WEAK_MATCH"

def test_scenario_j_exoplanet_catalog_match(fusion_engine):
    """Scenario J: Known exoplanet archive match attaches catalog metadata, NOT direct image discovery."""
    local_res = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
    bundle = EvidenceBundle(
        astrometry=AstrometryEvidence(
            available=True,
            parallax_mas=8.5,
            proper_motion_ra_mas_yr=-20.0,
            match_distance_arcsec=0.1
        ),
        exoplanet=ExoplanetEvidence(
            available=True,
            known_host=True,
            known_planet=True,
            planet_name="Kepler-186 f"
        )
    )
    res = fusion_engine.fuse_evidence(local_res, bundle)
    assert res.target_decision == "STAR"
    assert "KNOWN_CATALOG_PLANET" in res.exoplanet_evidence_status
    assert res.scientific_disclaimer is not None
