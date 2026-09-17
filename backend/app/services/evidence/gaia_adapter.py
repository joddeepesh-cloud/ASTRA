import logging
import time
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import AstrometryEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.gaia")

class GaiaAdapter:
    """
    Adapter for Gaia DR3 astrometric & photometric evidence acquisition.
    Provides safe, offline-first coordinate cone-search abstraction.
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 3.0
    ) -> Tuple[AstrometryEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute cone-search lookup for Gaia DR3 astrometric evidence.
        """
        t0 = time.perf_counter()
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return AstrometryEvidence(available=False), prov_items, None

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to Gaia adapter: RA={ra}, DEC={dec}")
            return AstrometryEvidence(available=False), prov_items, None

        if self.offline_mode:
            # Offline / local fallback mode
            return AstrometryEvidence(
                available=False,
                source="Gaia DR3",
                quality_indicators={"status": "OFFLINE_UNAVAILABLE"}
            ), prov_items, None

        # Network lookup stub (raises timeout / connection handling in real network mode)
        try:
            # Placeholder for external TAP / astroquery lookup
            return AstrometryEvidence(available=False), prov_items, None
        except Exception as e:
            logger.error(f"Error executing Gaia DR3 lookup: {e}")
            return AstrometryEvidence(available=False), prov_items, None
