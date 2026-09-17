import logging
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import PhotometryEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.wise")

class WiseAdapter:
    """
    Adapter for ALLWISE infrared photometry evidence acquisition (W1, W2, W3, W4).
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 3.0
    ) -> Tuple[PhotometryEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute lookup for ALLWISE infrared magnitude colors (W1, W2, W3, W4).
        """
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return PhotometryEvidence(available=False), prov_items, None

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to WISE adapter: RA={ra}, DEC={dec}")
            return PhotometryEvidence(available=False), prov_items, None

        if self.offline_mode:
            return PhotometryEvidence(
                available=False,
                source="ALLWISE"
            ), prov_items, None

        try:
            return PhotometryEvidence(available=False), prov_items, None
        except Exception as e:
            logger.error(f"Error executing ALLWISE lookup: {e}")
            return PhotometryEvidence(available=False), prov_items, None
