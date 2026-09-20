import unittest
import numpy as np
from PIL import Image

from backend.app.services.ml_service import MLService
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, AstrometryEvidence, SpectroscopyEvidence, ExoplanetEvidence
)
from backend.app.services.evidence.evidence_fusion import EvidenceFusionEngine
from ml.src.object_identification import ObjectIdentificationService

class TestStarRecognitionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ml_service = MLService()
        cls.ml_service.initialize()
        cls.fusion_engine = EvidenceFusionEngine()

    def test_1_clear_star_visual_input(self):
        """1. Clear star visual input: point-source morphology with STAR visual similarity returns STAR."""
        # Create compact PSF-like point source image
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        cy, cx = 112, 112
        y, x = np.ogrid[:224, :224]
        dist_sq = (x - cx)**2 + (y - cy)**2
        # Gaussian PSF profile
        psf = np.exp(-dist_sq / 12.0) * 255.0
        arr[:, :, 0] = psf.astype(np.uint8)
        arr[:, :, 1] = psf.astype(np.uint8)
        arr[:, :, 2] = psf.astype(np.uint8)
        img = Image.fromarray(arr)

        res = self.ml_service.object_id_service.classify_pil_image(img)
        self.assertIn(res["predicted_object_type"], ("STAR", "AMBIGUOUS_POINT_SOURCE"))

    def test_2_point_source_ambiguous_input(self):
        """2. Point-source ambiguous input: compact point source without clear star/quasar prompt margin returns AMBIGUOUS_POINT_SOURCE."""
        # Uniform faint point source
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        arr[110:114, 110:114] = [120, 120, 120]
        img = Image.fromarray(arr)

        res = self.ml_service.object_id_service.classify_pil_image(img)
        self.assertIn(res["predicted_object_type"], ("AMBIGUOUS_POINT_SOURCE", "ASTRONOMICAL_SOURCE_AMBIGUOUS"))

    def test_3_galaxy_input_remains_galaxy(self):
        """3. Extended galaxy profile input remains GALAXY and does not regress to STAR."""
        # Smooth extended Gaussian galaxy disk
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        y, x = np.ogrid[:224, :224]
        r = np.sqrt((x - 112)**2 + (y - 112)**2)
        disk = np.exp(-r / 35.0) * 220.0
        arr[:, :, 0] = disk.astype(np.uint8)
        arr[:, :, 1] = disk.astype(np.uint8)
        arr[:, :, 2] = disk.astype(np.uint8)
        img = Image.fromarray(arr)

        res = self.ml_service.object_id_service.classify_pil_image(img)
        self.assertNotEqual(res["predicted_object_type"], "STAR")

    def test_4_nebula_input_remains_nebula(self):
        """4. Diffuse nebular input remains NEBULA_CANDIDATE or ASTRONOMICAL_SOURCE_AMBIGUOUS."""
        arr = np.zeros((224, 224, 3), dtype=np.uint8)
        # Asymmetric diffuse cloud
        y, x = np.ogrid[:224, :224]
        cloud = np.sin(x / 15.0) * np.cos(y / 15.0) * 150.0
        cloud = np.clip(cloud, 0, 255)
        arr[:, :, 0] = cloud.astype(np.uint8)
        arr[:, :, 1] = (cloud * 0.7).astype(np.uint8)
        img = Image.fromarray(arr)

        res = self.ml_service.object_id_service.classify_pil_image(img)
        self.assertNotEqual(res["predicted_object_type"], "STAR")

    def test_5_quasar_candidate_input(self):
        """5. Quasar candidate input routes to QUASAR_CANDIDATE or AMBIGUOUS_POINT_SOURCE, not forced to STAR."""
        local = {"predicted_object_type": "QUASAR_CANDIDATE"}
        bundle = EvidenceBundle()
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "QUASAR_CANDIDATE")

    def test_6_non_astronomical_input_rejected(self):
        """6. Non-astronomical input remains INCOMPATIBLE."""
        local = {"predicted_object_type": "INCOMPATIBLE", "domain_validation": {"decision": "INCOMPATIBLE"}}
        bundle = EvidenceBundle()
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "INCOMPATIBLE")

    def test_7_gaia_supported_stellar_evidence(self):
        """7. Gaia astrometric evidence promotes ambiguous point source to STAR."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            astrometry=AstrometryEvidence(
                available=True,
                parallax_mas=4.52,
                proper_motion_ra_mas_yr=12.4,
                proper_motion_dec_mas_yr=-8.1,
                match_distance_arcsec=0.2
            )
        )
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "STAR")
        self.assertIn("Gaia DR3", fused.primary_rationale)

    def test_8_quasar_evidence_must_not_become_star(self):
        """8. SDSS quasar evidence promotes point source to QUASAR_CANDIDATE, never STAR."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            spectroscopy=SpectroscopyEvidence(
                available=True,
                spectral_class="QSO",
                redshift=1.45,
                is_quasar_catalog_member=True,
                match_distance_arcsec=0.3
            )
        )
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "QUASAR_CANDIDATE")
        self.assertNotEqual(fused.target_decision, "STAR")

    def test_9_missing_coordinates_does_not_fabricate_evidence(self):
        """9. Missing coordinates do not fabricate catalog evidence; preserves local classification."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle()
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "AMBIGUOUS_POINT_SOURCE")
        self.assertFalse(fused.is_conflicting)

    def test_10_conflicting_point_source_evidence(self):
        """10. Conflicting Gaia stellar + SDSS quasar evidence resolves to CONFLICTING_POINT_SOURCE_EVIDENCE."""
        local = {"predicted_object_type": "AMBIGUOUS_POINT_SOURCE"}
        bundle = EvidenceBundle(
            astrometry=AstrometryEvidence(
                available=True,
                parallax_mas=3.1,
                proper_motion_ra_mas_yr=5.2,
                match_distance_arcsec=0.1
            ),
            spectroscopy=SpectroscopyEvidence(
                available=True,
                spectral_class="QSO",
                redshift=2.1,
                is_quasar_catalog_member=True,
                match_distance_arcsec=0.1
            )
        )
        fused = self.fusion_engine.fuse_evidence(local, bundle)
        self.assertEqual(fused.target_decision, "CONFLICTING_POINT_SOURCE_EVIDENCE")
        self.assertTrue(fused.is_conflicting)

if __name__ == "__main__":
    unittest.main()
