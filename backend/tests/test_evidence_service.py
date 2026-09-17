import pytest
from unittest.mock import MagicMock

from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, AstrometryEvidence, SpectroscopyEvidence, PhotometryEvidence,
    TimeSeriesEvidence, ExoplanetEvidence, NebulaEvidence, CatalogMatch, EvidenceProvenance
)
from backend.app.services.evidence.evidence_service import EvidenceService
from backend.app.services.evidence.gaia_adapter import GaiaAdapter
from backend.app.services.evidence.sdss_adapter import SdssAdapter
from backend.app.services.evidence.wise_adapter import WiseAdapter
from backend.app.services.evidence.tess_adapter import TessAdapter
from backend.app.services.evidence.exoplanet_archive_adapter import ExoplanetArchiveAdapter
from backend.app.services.evidence.nebula_adapter import NebulaAdapter

def test_1_no_catalog_match():
    """Verify lookup with valid coordinates but no catalog matches returns clean empty bundle."""
    svc = EvidenceService(offline_mode=True)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.target_coordinates.ra == 180.0
    assert bundle.target_coordinates.dec == 45.0
    assert len(bundle.catalog_matches) == 0
    assert bundle.astrometry.available is False

def test_2_gaia_match():
    """Verify Gaia DR3 match returns astrometric evidence."""
    mock_gaia = MagicMock(spec=GaiaAdapter)
    mock_gaia.lookup.return_value = (
        AstrometryEvidence(
            available=True,
            source="Gaia DR3",
            source_id="Gaia-DR3-587726",
            parallax_mas=4.12,
            proper_motion_ra_mas_yr=-12.4,
            proper_motion_dec_mas_yr=8.1,
            g_magnitude=14.2,
            bp_rp_color=1.15,
            match_distance_arcsec=0.25,
            stellar_evidence_score=0.92
        ),
        [EvidenceProvenance(source="Gaia DR3", field="parallax", value=4.12, unit="mas")],
        CatalogMatch(catalog_name="Gaia DR3", source_id="Gaia-DR3-587726", ra=180.0, dec=45.0, match_distance_arcsec=0.25)
    )
    svc = EvidenceService(offline_mode=True, gaia_adapter=mock_gaia)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.astrometry.available is True
    assert bundle.astrometry.parallax_mas == 4.12
    assert bundle.astrometry.g_magnitude == 14.2
    assert len(bundle.catalog_matches) == 1
    assert bundle.catalog_matches[0].catalog_name == "Gaia DR3"

def test_3_sdss_match():
    """Verify SDSS spectroscopy match returns redshift and quasar catalog membership."""
    mock_sdss = MagicMock(spec=SdssAdapter)
    mock_sdss.lookup.return_value = (
        SpectroscopyEvidence(
            available=True,
            source="SDSS DR16",
            source_id="SDSS-J1200+4500",
            redshift=1.452,
            spectral_class="QSO",
            is_quasar_catalog_member=True,
            broad_emission_lines_detected=True,
            match_distance_arcsec=0.18,
            quasar_evidence_score=0.98
        ),
        [EvidenceProvenance(source="SDSS DR16", field="redshift", value=1.452)],
        CatalogMatch(catalog_name="SDSS DR16Q", source_id="SDSS-J1200+4500", ra=180.0, dec=45.0, match_distance_arcsec=0.18)
    )
    svc = EvidenceService(offline_mode=True, sdss_adapter=mock_sdss)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.spectroscopy.available is True
    assert bundle.spectroscopy.redshift == 1.452
    assert bundle.spectroscopy.is_quasar_catalog_member is True

def test_4_wise_match():
    """Verify WISE infrared photometry match returns W1-W4 magnitudes."""
    mock_wise = MagicMock(spec=WiseAdapter)
    mock_wise.lookup.return_value = (
        PhotometryEvidence(
            available=True,
            source="ALLWISE",
            source_id="WISE-J1200+4500",
            wise_w1=13.1,
            wise_w2=12.2,
            w1_minus_w2=0.9,
            match_distance_arcsec=0.3
        ),
        [EvidenceProvenance(source="ALLWISE", field="w1_minus_w2", value=0.9)],
        CatalogMatch(catalog_name="ALLWISE", source_id="WISE-J1200+4500", ra=180.0, dec=45.0, match_distance_arcsec=0.3)
    )
    svc = EvidenceService(offline_mode=True, wise_adapter=mock_wise)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.photometry.available is True
    assert bundle.photometry.w1_minus_w2 == 0.9

def test_5_tess_unavailable():
    """Verify TESS lookup returns available=False when no light curve exists."""
    svc = EvidenceService(offline_mode=True)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.time_series.available is False
    assert bundle.time_series.time_series_status == "NO_TIME_SERIES_AVAILABLE"
    assert bundle.time_series.signal_hint in ("INSUFFICIENT_DATA", "OFFLINE_MODE")

def test_6_tess_available():
    """Verify TESS lookup returns light curve time-series arrays when available."""
    mock_tess = MagicMock(spec=TessAdapter)
    mock_tess.lookup.return_value = (
        TimeSeriesEvidence(
            available=True,
            mission="TESS",
            sector=14,
            time=[0.0, 0.1, 0.2, 0.3],
            flux=[1.0, 0.98, 0.98, 1.0],
            quality=[0, 0, 0, 0],
            source_id="TIC-12345678",
            status="LIGHT_CURVE_ANALYSIS_COMPLETED",
            signal_hint="TRANSIT_LIKE_SIGNAL"
        ),
        [EvidenceProvenance(source="TESS", field="signal_hint", value="TRANSIT_LIKE_SIGNAL")]
    )
    svc = EvidenceService(offline_mode=True, tess_adapter=mock_tess)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0, target_id="TIC-12345678")
    assert bundle.time_series.available is True
    assert bundle.time_series.signal_hint == "TRANSIT_LIKE_SIGNAL"
    assert len(bundle.time_series.flux) == 4

def test_7_exoplanet_catalog_match():
    """Verify NASA Exoplanet Archive lookup returns host and candidate metadata."""
    mock_exo = MagicMock(spec=ExoplanetArchiveAdapter)
    mock_exo.lookup.return_value = (
        ExoplanetEvidence(
            available=True,
            known_host=True,
            known_planet=True,
            planet_name="Kepler-186 f",
            orbital_period_days=129.9,
            transit_depth_ppm=450.0,
            match_distance_arcsec=0.1
        ),
        [EvidenceProvenance(source="NASA Exoplanet Archive", field="planet_name", value="Kepler-186 f")],
        CatalogMatch(catalog_name="NASA Exoplanet Archive", source_id="Kepler-186 f", ra=180.0, dec=45.0, match_distance_arcsec=0.1)
    )
    svc = EvidenceService(offline_mode=True, exoplanet_adapter=mock_exo)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.exoplanet.available is True
    assert bundle.exoplanet.planet_name == "Kepler-186 f"
    assert bundle.exoplanet.known_planet is True

def test_8_conflicting_evidence():
    """Verify evidence service aggregates conflicting matches without failing."""
    mock_gaia = MagicMock(spec=GaiaAdapter)
    mock_gaia.lookup.return_value = (
        AstrometryEvidence(available=True, parallax_mas=0.01), [], None
    )
    mock_sdss = MagicMock(spec=SdssAdapter)
    mock_sdss.lookup.return_value = (
        SpectroscopyEvidence(available=True, redshift=2.1), [], None
    )
    svc = EvidenceService(offline_mode=True, gaia_adapter=mock_gaia, sdss_adapter=mock_sdss)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert bundle.astrometry.available is True
    assert bundle.spectroscopy.available is True
    assert bundle.astrometry.parallax_mas == 0.01
    assert bundle.spectroscopy.redshift == 2.1

def test_9_missing_coordinates():
    """Verify missing coordinates (ra=None, dec=None) returns clean empty bundle."""
    svc = EvidenceService(offline_mode=True)
    bundle = svc.fetch_evidence_bundle(ra=None, dec=None)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.target_coordinates.ra is None
    assert bundle.target_coordinates.dec is None
    assert bundle.astrometry.available is False
    assert bundle.spectroscopy.available is False

def test_10_external_api_failure():
    """Verify runtime exception inside an adapter is safely caught and returns fallback evidence."""
    mock_gaia = MagicMock(spec=GaiaAdapter)
    mock_gaia.lookup.side_effect = RuntimeError("Network connection error to Gaia TAP service")
    svc = EvidenceService(offline_mode=False, gaia_adapter=mock_gaia)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.astrometry.available is False

def test_11_timeout_handling():
    """Verify adapter timeout is handled safely without throwing exceptions."""
    mock_sdss = MagicMock(spec=SdssAdapter)
    mock_sdss.lookup.side_effect = TimeoutError("SDSS query timed out after 2.0 seconds")
    svc = EvidenceService(offline_mode=False, sdss_adapter=mock_sdss)
    bundle = svc.fetch_evidence_bundle(ra=180.0, dec=45.0)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.spectroscopy.available is False

def test_12_malformed_response():
    """Verify invalid / out-of-bounds coordinate inputs return graceful empty evidence."""
    svc = EvidenceService(offline_mode=True)
    bundle = svc.fetch_evidence_bundle(ra=9999.0, dec=-9999.0)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.astrometry.available is False

def test_13_no_evidence_available():
    """Verify default bundle has all availability flags set to False."""
    svc = EvidenceService(offline_mode=True)
    bundle = svc.fetch_evidence_bundle(ra=10.0, dec=10.0)
    for key, is_avail in bundle.availability_summary.items():
        assert is_avail is False
