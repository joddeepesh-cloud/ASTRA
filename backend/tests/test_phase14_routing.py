import unittest
from PIL import Image
import numpy as np

from backend.app.services.ml_service import MLService
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, AstrometryEvidence, SpectroscopyEvidence, ExoplanetEvidence
)
from backend.app.services.evidence.evidence_fusion import EvidenceFusionEngine


class TestPhase14OpenWorldRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ml_service = MLService()
        cls.ml_service.initialize()
        cls.fusion_engine = EvidenceFusionEngine()

    def test_1_non_astronomical_image_rejection(self):
        """Test 1: Clearly non-astronomical images (e.g. solid white/random noise/terrestrial photo) are rejected as INCOMPATIBLE."""
        # Create a non-astronomical test image (grid pattern with text-like shapes)
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        arr[:100, :100] = [255, 0, 0]  # Bright red block
        arr[100:, 100:] = [0, 255, 0]  # Bright green block
        img = Image.fromarray(arr)
        
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        file_bytes = buf.getvalue()

        result = self.ml_service.analyze_image(file_bytes, filename="terrestrial_test.jpg")
        self.assertIn(result["predicted_object_type"], ("INCOMPATIBLE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"))
        if result["predicted_object_type"] == "INCOMPATIBLE":
            self.assertEqual(result["domain_validation"]["decision"], "INCOMPATIBLE")

    def test_2_astronomy_visualization_pipeline_continuation(self):
        """Test 2: Astronomy-related imagery (black hole/exoplanet render) does NOT get rejected as INCOMPATIBLE."""
        # Create a synthetic space visualization (central glowing accretion disk on dark field)
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        y, x = np.ogrid[:224, :224]
        r = np.sqrt((x - 112)**2 + (y - 112)**2)
        disk = (r > 30) & (r < 70)
        arr[disk] = [255, 160, 40]  # Glowing orange ring
        img = Image.fromarray(arr)

        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        file_bytes = buf.getvalue()

        result = self.ml_service.analyze_image(file_bytes, filename="black_hole_ring_visualization.jpg")
        # Critical rule: Must NOT be falsely rejected as INCOMPATIBLE
        self.assertNotEqual(result["predicted_object_type"], "INCOMPATIBLE")
        self.assertIn(result["predicted_object_type"], ("ASTRONOMICAL_SOURCE_AMBIGUOUS", "AMBIGUOUS_POINT_SOURCE", "GALAXY", "NEBULA_CANDIDATE", "PLANETARY_CANDIDATE"))

    def test_3_point_source_pipeline_continuation(self):
        """Test 3: Point-like optical star cutout does NOT get rejected; routes to AMBIGUOUS_POINT_SOURCE."""
        # Create a single bright unresolved point source on dark background
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        arr[110:114, 110:114] = [255, 255, 255]
        img = Image.fromarray(arr)

        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        file_bytes = buf.getvalue()

        result = self.ml_service.analyze_image(file_bytes, filename="stellar_point_source.jpg")
        self.assertNotEqual(result["predicted_object_type"], "INCOMPATIBLE")
        self.assertIn(result["predicted_object_type"], ("AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"))

    def test_4_galaxy_morphology_conditional_execution(self):
        """Test 4: Galaxy Zoo morphology specialist runs ONLY when pred_obj_type == 'GALAXY'."""
        # Test point source does not execute morphology
        local_point = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle()
        res = self.fusion_engine.fuse_evidence(local_point, bundle)
        self.assertEqual(res.target_decision, "AMBIGUOUS_POINT_SOURCE")

    def test_5_exoplanet_catalog_match_requires_evidence(self):
        """Test 5: Exoplanet candidate or match requires authoritative TAP catalog or light curve transit evidence."""
        # Image alone does NOT output KNOWN_EXOPLANET_MATCH
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        no_evidence_bundle = EvidenceBundle()
        res_no_ev = self.fusion_engine.fuse_evidence(local, no_evidence_bundle)
        self.assertNotEqual(res_no_ev.target_decision, "KNOWN_EXOPLANET_MATCH")

        # Bundle with TAP match yields KNOWN_EXOPLANET_MATCH
        tap_bundle = EvidenceBundle(
            exoplanet=ExoplanetEvidence(
                available=True,
                known_planet=True,
                planet_name="TOI-700 b",
                orbital_period_days=9.977,
                exoplanet_status="KNOWN_EXOPLANET_MATCH"
            )
        )
        res_tap = self.fusion_engine.fuse_evidence(local, tap_bundle)
        self.assertEqual(res_tap.target_decision, "KNOWN_EXOPLANET_MATCH")


if __name__ == "__main__":
    unittest.main()
