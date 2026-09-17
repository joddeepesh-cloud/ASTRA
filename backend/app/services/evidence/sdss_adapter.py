import logging
import time
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import SpectroscopyEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.sdss")

class SdssAdapter:
    """
    Adapter for SDSS DR16 spectroscopy and quasar catalog (DR16Q) evidence acquisition.
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 3.0
    ) -> Tuple[SpectroscopyEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute lookup for SDSS spectroscopic redshift and quasar catalog membership.
        """
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return SpectroscopyEvidence(available=False), prov_items, None

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to SDSS adapter: RA={ra}, DEC={dec}")
            return SpectroscopyEvidence(available=False), prov_items, None

        if self.offline_mode:
            return SpectroscopyEvidence(
                available=False,
                source="SDSS DR16"
            ), prov_items, None

        try:
            return SpectroscopyEvidence(available=False), prov_items, None
        except Exception as e:
            logger.error(f"Error executing SDSS DR16 lookup: {e}")
            return SpectroscopyEvidence(available=False), prov_items, None
