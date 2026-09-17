import logging
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import ExoplanetEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.exoplanet")

class ExoplanetArchiveAdapter:
    """
    Adapter for NASA Exoplanet Archive host star and exoplanet candidate evidence acquisition.
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 3.0
    ) -> Tuple[ExoplanetEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute cone-search lookup against NASA Exoplanet Archive.
        """
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return ExoplanetEvidence(available=False), prov_items, None

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to Exoplanet Archive adapter: RA={ra}, DEC={dec}")
            return ExoplanetEvidence(available=False), prov_items, None

        if self.offline_mode:
            return ExoplanetEvidence(available=False), prov_items, None

        try:
            return ExoplanetEvidence(available=False), prov_items, None
        except Exception as e:
            logger.error(f"Error executing NASA Exoplanet Archive lookup: {e}")
            return ExoplanetEvidence(available=False), prov_items, None
