import unittest
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, TargetCoordinates, AstrometryEvidence, SpectroscopyEvidence,
    PhotometryEvidence, TimeSeriesEvidence, ExoplanetEvidence, CatalogMatch
)
from backend.app.services.evidence.evidence_fusion import EvidenceFusionEngine
from backend.app.services.evidence.evidence_service import EvidenceService
from backend.app.services.evidence.exoplanet_archive_adapter import ExoplanetArchiveAdapter
from backend.app.services.evidence.tess_adapter import TessAdapter


class TestPhase13EvidenceFramework(unittest.TestCase):
    def setUp(self):
        self.fusion_engine = EvidenceFusionEngine()

    def test_scenario_a_galaxy(self):
        """Scenario A: Extended galaxy visual structure -> GALAXY."""
        local = {"predicted_object_type": "GALAXY", "morphology": "SPIRAL"}
        bundle = EvidenceBundle()
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "GALAXY")

    def test_scenario_b_non_astronomical(self):
        """Scenario B: Non-astronomical image -> INCOMPATIBLE."""
        local = {"predicted_object_type": "INCOMPATIBLE", "domain_validation": {"decision": "INCOMPATIBLE"}}
        bundle = EvidenceBundle()
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "INCOMPATIBLE")

    def test_scenario_c_ambiguous_astronomical(self):
        """Scenario C: Ambiguous astronomical image -> ASTRONOMICAL_SOURCE_AMBIGUOUS."""
        local = {"predicted_object_type": "ASTRONOMICAL_SOURCE_AMBIGUOUS"}
        bundle = EvidenceBundle()
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "ASTRONOMICAL_SOURCE_AMBIGUOUS")

    def test_scenario_d_point_source_no_evidence(self):
        """Scenario D: Point source without catalog evidence -> AMBIGUOUS_POINT_SOURCE."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle()
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "AMBIGUOUS_POINT_SOURCE")

    def test_scenario_e_star(self):
        """Scenario E: Point source + Gaia stellar evidence -> STAR."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            astrometry=AstrometryEvidence(
                available=True,
                parallax_mas=12.4,
                proper_motion_ra_mas_yr=45.2,
                match_distance_arcsec=0.2
            )
        )
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "STAR")

    def test_scenario_f_quasar(self):
        """Scenario F: Point source + spectroscopic quasar evidence -> QUASAR_CANDIDATE."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            spectroscopy=SpectroscopyEvidence(
                available=True,
                redshift=1.85,
                spectral_class="QSO",
                is_quasar_catalog_member=True,
                match_distance_arcsec=0.3
            )
        )
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "QUASAR_CANDIDATE")

    def test_scenario_g_conflicting_evidence(self):
        """Scenario G: Point source + conflicting stellar/quasar evidence -> CONFLICTING_POINT_SOURCE_EVIDENCE."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            astrometry=AstrometryEvidence(
                available=True,
                parallax_mas=15.1,
                proper_motion_ra_mas_yr=32.0,
                match_distance_arcsec=0.2
            ),
            spectroscopy=SpectroscopyEvidence(
                available=True,
                redshift=2.1,
                spectral_class="QSO",
                is_quasar_catalog_member=True,
                match_distance_arcsec=0.3
            )
        )
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "CONFLICTING_POINT_SOURCE_EVIDENCE")
        self.assertTrue(res.is_conflicting)

    def test_scenario_h_known_exoplanet_match(self):
        """Scenario H: Target with confirmed exoplanet catalog match -> KNOWN_EXOPLANET_MATCH."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            exoplanet=ExoplanetEvidence(
                available=True,
                known_planet=True,
                planet_name="TOI-700 b",
                hostname="TOI-700",
                orbital_period_days=9.977,
                exoplanet_status="KNOWN_EXOPLANET_MATCH"
            )
        )
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "KNOWN_EXOPLANET_MATCH")

    def test_scenario_i_exoplanet_candidate(self):
        """Scenario I: Light curve transit-like signal -> EXOPLANET_CANDIDATE."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            time_series=TimeSeriesEvidence(
                available=True,
                time_series_status="TRANSIT_LIKE_SIGNAL",
                period_days=3.52,
                transit_depth=0.015,
                transit_snr=5.2
            )
        )
        res = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(res.target_decision, "EXOPLANET_CANDIDATE")

    def test_scenario_j_no_light_curve(self):
        """Scenario J: No light curve available."""
        adapter = TessAdapter(offline_mode=True)
        ts, prov = adapter.lookup(ra=0.0, dec=0.0)
        self.assertFalse(ts.available)
        self.assertEqual(ts.time_series_status, "NO_TIME_SERIES_AVAILABLE")

    def test_scenario_k_no_catalog_match(self):
        """Scenario K: Target coordinates with no catalog matches within search radius."""
        adapter = ExoplanetArchiveAdapter(offline_mode=True)
        exo, prov, match = adapter.lookup(ra=0.0, dec=0.0)
        self.assertFalse(exo.known_planet)
        self.assertIsNone(match)

    def test_scenario_l_service_unavailable_fallback(self):
        """Scenario L: Network or service exception during evidence lookup triggers safe fallback."""
        service = EvidenceService(offline_mode=True)
        bundle = service.fetch_evidence_bundle(ra=None, dec=None)
        self.assertIsNotNone(bundle)
        self.assertFalse(bundle.astrometry.available)
        self.assertFalse(bundle.exoplanet.available)


if __name__ == "__main__":
    unittest.main()
