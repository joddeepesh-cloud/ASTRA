import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.evidence.evidence_store import evidence_store
from backend.app.services.evidence.evidence_fusion import evidence_fusion_engine
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, AstrometryEvidence, SpectroscopyEvidence, PhotometryEvidence,
    ExoplanetEvidence, NebulaEvidence, CatalogMatch
)


client = TestClient(app)

def create_test_image_bytes():
    """Generate simple valid JPEG bytes for test upload."""
    img = Image.new("RGB", (224, 224), color=(30, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_scenario_a_galaxy_with_valid_catalog_evidence():
    """Scenario A: Extended morphology + Galaxy Zoo support -> GALAXY."""
    image_evidence = {
        "predicted_object_type": "GALAXY",
        "visual_similarity_score": 0.88,
        "object_margin": 0.65,
        "morphology_label": "SPIRAL",
        "morphology_confidence": 0.85
    }
    catalog_bundle = EvidenceBundle(target_ra=177.07, target_dec=-3.11)
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "GALAXY"
    assert res.evidence_level in ("MODERATE", "STRONG", "DECISIVE")

def test_scenario_b_point_source_with_gaia_stellar_evidence():
    """Scenario B: Point source + Gaia DR3 high parallax -> STAR."""
    image_evidence = {
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "visual_similarity_score": 0.45,
        "object_margin": 0.05
    }

    catalog_bundle = EvidenceBundle(
        target_ra=180.0,
        target_dec=15.0,
        catalog_matches=[CatalogMatch(catalog_name="Gaia DR3", source_id="GAIA-1", ra=180.0, dec=15.0, match_distance_arcsec=0.2)],
        astrometry=AstrometryEvidence(
            available=True,
            source_id="GAIA-DR3-12345678",
            parallax_mas=12.5,
            parallax_error_mas=0.2, # >60 sigma
            proper_motion_ra_mas_yr=45.0,
            proper_motion_dec_mas_yr=12.0,
            match_distance_arcsec=0.2
        )
    )
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "STAR"
    assert res.evidence_level == "DECISIVE"

def test_scenario_c_point_source_with_sdss_quasar_evidence():
    """Scenario C: Point source + SDSS spectroscopic redshift z=1.42 -> QUASAR_CANDIDATE."""
    image_evidence = {
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "visual_similarity_score": 0.40,
        "object_margin": 0.02
    }
    catalog_bundle = EvidenceBundle(
        target_ra=185.0,
        target_dec=20.0,
        catalog_matches=[CatalogMatch(catalog_name="SDSS DR16", source_id="SDSS-1", ra=185.0, dec=20.0, match_distance_arcsec=0.3)],
        spectroscopy=SpectroscopyEvidence(
            available=True,
            spec_obj_id="SDSS-SPEC-987654",
            redshift=1.42,
            redshift_err=0.001,
            spectral_class="QSO",
            is_sdss_dr16q=True,
            match_distance_arcsec=0.3
        )
    )
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "QUASAR_CANDIDATE"
    assert res.evidence_level == "DECISIVE"

def test_scenario_d_diffuse_source_without_nebula_evidence():
    """Scenario D: Diffuse visual appearance without WISE/SIMBAD nebula excess -> NOT automatically NEBULA."""
    image_evidence = {
        "predicted_object_type": "ASTRONOMICAL_SOURCE_AMBIGUOUS",
        "visual_similarity_score": 0.50,
        "object_margin": 0.02,
        "evidence": ["diffuse_visual_profile"]
    }
    catalog_bundle = EvidenceBundle(target_ra=200.0, target_dec=30.0)
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type != "NEBULA_CANDIDATE"
    assert res.fused_object_type in ("ASTRONOMICAL_SOURCE_AMBIGUOUS", "AMBIGUOUS_POINT_SOURCE")

def test_scenario_e_exoplanet_image_without_catalog_evidence():
    """Scenario E: Normal image without NASA Exoplanet Archive record -> NOT EXOPLANET_CANDIDATE."""
    image_evidence = {
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "visual_similarity_score": 0.55
    }
    catalog_bundle = EvidenceBundle(target_ra=210.0, target_dec=40.0)
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type != "EXOPLANET_CANDIDATE"

def test_scenario_f_point_source_without_resolving_evidence():
    """Scenario F: Isolated point source without catalog match -> AMBIGUOUS_POINT_SOURCE."""
    image_evidence = {
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "visual_similarity_score": 0.42
    }
    catalog_bundle = EvidenceBundle(target_ra=220.0, target_dec=50.0)
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "AMBIGUOUS_POINT_SOURCE"
    assert res.evidence_level == "NONE"

def test_scenario_g_conflicting_point_source_evidence():
    """Scenario G: Gaia stellar parallax vs SDSS quasar redshift -> CONFLICTING_POINT_SOURCE_EVIDENCE."""
    image_evidence = {
        "predicted_object_type": "AMBIGUOUS_POINT_SOURCE",
        "visual_similarity_score": 0.45
    }
    catalog_bundle = EvidenceBundle(
        target_ra=230.0,
        target_dec=60.0,
        catalog_matches=[
            CatalogMatch(catalog_name="Gaia DR3", source_id="GAIA-CONF", ra=230.0, dec=60.0, match_distance_arcsec=0.2),
            CatalogMatch(catalog_name="SDSS DR16", source_id="SDSS-CONF", ra=230.0, dec=60.0, match_distance_arcsec=0.2)
        ],
        astrometry=AstrometryEvidence(
            available=True,
            source_id="GAIA-DR3-CONFLICT",
            parallax_mas=15.0,
            parallax_error_mas=0.3,
            match_distance_arcsec=0.2
        ),
        spectroscopy=SpectroscopyEvidence(
            available=True,
            spec_obj_id="SDSS-SPEC-CONFLICT",
            redshift=2.1,
            spectral_class="QSO",
            match_distance_arcsec=0.2
        )
    )
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "CONFLICTING_POINT_SOURCE_EVIDENCE"



def test_scenario_h_non_astronomical_image_incompatible():
    """Scenario H: Non-astronomical image payload -> INCOMPATIBLE."""
    image_evidence = {
        "predicted_object_type": "INCOMPATIBLE"
    }
    catalog_bundle = EvidenceBundle(target_ra=10.0, target_dec=10.0)
    res = evidence_fusion_engine.fuse_evidence(image_evidence, catalog_bundle)
    assert res.fused_object_type == "INCOMPATIBLE"

def test_scenario_i_missing_ra_dec_enrichment_unavailable():
    """Scenario I: Uploaded image without RA/Dec -> evidence status UNAVAILABLE."""
    img_bytes = create_test_image_bytes()
    response = client.post(
        "/api/v1/triage",
        files={"file": ("test_upload.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "observation_id" in data
    obs_id = data["observation_id"]

    # Verify initial triage response returned immediately
    assert data["evidence_status"] == "UNAVAILABLE"

    # Fetch evidence endpoint
    ev_res = client.get(f"/api/v1/observations/{obs_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["evidence_status"] == "UNAVAILABLE"
    assert "no trusted celestial coordinates" in ev_data["explanation"].lower()

def test_scenario_j_external_api_failure_graceful_handling():
    """Scenario J: External catalog adapter failure/timeout -> handled gracefully."""
    catalog_bundle = EvidenceBundle(
        target_ra=240.0,
        target_dec=70.0,
        notes=["Gaia adapter connection error"]
    )
    res = evidence_fusion_engine.fuse_evidence(None, catalog_bundle)
    assert res.fused_object_type in ("AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS")

def test_scenario_k_triage_returns_without_waiting_for_external_enrichment():
    """Scenario K: /triage returns immediately (fast path) with status PENDING when RA/Dec supplied."""
    img_bytes = create_test_image_bytes()
    response = client.post(
        "/api/v1/triage",
        files={"file": ("target_coords.jpg", img_bytes, "image/jpeg")},
        data={"ra": "177.07516", "dec": "-3.11701"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evidence_status"] == "PENDING"
    assert data["ra"] == 177.07516
    assert data["dec"] == -3.11701
    assert "observation_id" in data

def test_scenario_l_frontend_can_retrieve_completed_evidence():
    """Scenario L: Frontend retrieves completed evidence via GET /api/v1/observations/{observation_id}/evidence."""
    obs_id = "TEST-LIB-000001"
    evidence_store.set_evidence(obs_id, {
        "observation_id": obs_id,
        "evidence_status": "COMPLETE",
        "ra": 177.07516,
        "dec": -3.11701,
        "fused_object_type": "GALAXY",
        "evidence_level": "MODERATE",
        "match_quality": "HIGH_QUALITY_MATCH",
        "catalog_sources_queried": ["Gaia DR3", "SDSS DR16", "ALLWISE"],
        "contributing_catalogs": ["Galaxy Zoo 2", "SDSS DR16"],
        "explanation": "Extended spatial light profile matches galaxy morphology.",
        "provenance": ["Galaxy Zoo 2 Morphology Specialist"],
        "conflicts": [],
        "fused_result": None,
        "updated_at": "2026-09-16T23:00:00Z"
    })

    res = client.get(f"/api/v1/observations/{obs_id}/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["evidence_status"] == "COMPLETE"
    assert data["fused_object_type"] == "GALAXY"
    assert data["evidence_level"] == "MODERATE"

def test_scenario_m_no_fake_evidence_emitted():
    """Scenario M: Unmatched targets emit empty contributing catalogs and no fake parallaxes/redshifts."""
    catalog_bundle = EvidenceBundle(target_ra=250.0, target_dec=80.0)
    res = evidence_fusion_engine.fuse_evidence(None, catalog_bundle)
    assert res.contributing_catalogs == []
    assert res.conflicts == []
    assert res.fused_object_type == "ASTRONOMICAL_SOURCE_AMBIGUOUS"

