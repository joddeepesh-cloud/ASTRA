import logging
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import TimeSeriesEvidence, EvidenceProvenance

logger = logging.getLogger("astra.evidence.tess")

class TessAdapter:
    """
    Adapter for TESS time-series photometric evidence acquisition.
    """
    def __init__(self, offline_mode: bool = True, timeout_sec: float = 2.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        target_id: Optional[str] = None
    ) -> Tuple[TimeSeriesEvidence, List[EvidenceProvenance]]:
        """
        Execute lookup for TESS high-cadence light curve time-series evidence.
        """
        prov_items: List[EvidenceProvenance] = []

        if ra is None or dec is None:
            return TimeSeriesEvidence(
                available=False,
                status="NO_LIGHT_CURVE_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to TESS adapter: RA={ra}, DEC={dec}")
            return TimeSeriesEvidence(
                available=False,
                status="NO_LIGHT_CURVE_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items

        if self.offline_mode:
            return TimeSeriesEvidence(
                available=False,
                mission="TESS",
                status="NO_LIGHT_CURVE_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items

        try:
            return TimeSeriesEvidence(
                available=False,
                mission="TESS",
                status="NO_LIGHT_CURVE_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items
        except Exception as e:
            logger.error(f"Error executing TESS light curve lookup: {e}")
            return TimeSeriesEvidence(
                available=False,
                status="NO_LIGHT_CURVE_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items
