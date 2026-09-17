import logging
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import NebulaEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.nebula")

class NebulaAdapter:
    """
    Adapter for SIMBAD / H-alpha diffuse nebula catalog cross-matching.
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 10.0
    ) -> Tuple[NebulaEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute cone-search lookup against diffuse nebula and emission-line catalogs.
        """
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return NebulaEvidence(available=False), prov_items, None

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to Nebula adapter: RA={ra}, DEC={dec}")
            return NebulaEvidence(available=False), prov_items, None

        if self.offline_mode:
            return NebulaEvidence(available=False), prov_items, None

        try:
            return NebulaEvidence(available=False), prov_items, None
        except Exception as e:
            logger.error(f"Error executing Nebula catalog lookup: {e}")
            return NebulaEvidence(available=False), prov_items, None
