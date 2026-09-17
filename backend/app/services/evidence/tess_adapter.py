import logging
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import TimeSeriesEvidence, EvidenceProvenance

logger = logging.getLogger("astra.evidence.tess")

class TessAdapter:
    """
    Adapter for TESS time-series photometric light curve evidence acquisition via Lightkurve / MAST.
    """
    def __init__(self, offline_mode: bool = False, timeout_sec: float = 3.0):
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
                time_series_status="NO_TIME_SERIES_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items

        if not (-360.0 <= ra <= 360.0 and -90.0 <= dec <= 90.0):
            logger.warning(f"Invalid coordinates passed to TESS adapter: RA={ra}, DEC={dec}")
            return TimeSeriesEvidence(
                available=False,
                time_series_status="NO_TIME_SERIES_AVAILABLE",
                signal_hint="INSUFFICIENT_DATA"
            ), prov_items

        if self.offline_mode:
            return TimeSeriesEvidence(
                available=False,
                mission="TESS",
                time_series_status="NO_TIME_SERIES_AVAILABLE",
                signal_hint="OFFLINE_MODE"
            ), prov_items

        try:
            import lightkurve as lk

            query_target = target_id or f"{ra:.4f}, {dec:.4f}"
            search = lk.search_lightcurve(query_target, mission="TESS", limit=3)

            if len(search) == 0:
                return TimeSeriesEvidence(
                    available=False,
                    mission="TESS",
                    time_series_status="NO_TIME_SERIES_AVAILABLE",
                    signal_hint="NO_MAST_LIGHTCURVE"
                ), prov_items

            t_name = search.target_name[0] if len(search.target_name) > 0 else f"TIC {query_target}"
            author = search.author[0] if len(search.author) > 0 else "SPOC"
            exptime = float(search.exptime[0].value) if hasattr(search.exptime[0], 'value') else 120.0

            prov_items.append(EvidenceProvenance(
                source="Lightkurve / TESS MAST",
                field="light_curve",
                value=f"{t_name} ({len(search)} sectors/files)",
                unit=f"cadence: {exptime}s",
                provenance="external_time_series",
                interpretation=f"TESS photometric time-series light curve located via MAST (Author: {author})"
            ))

            return TimeSeriesEvidence(
                available=True,
                mission="TESS",
                time_series_status="TIME_SERIES_FOUND",
                target_name=str(t_name),
                observation_count=len(search),
                baseline_duration_days=27.4,
                signal_hint="LIGHT_CURVE_AVAILABLE"
            ), prov_items

        except Exception as e:
            logger.warning(f"Lightkurve query notice for RA={ra}, DEC={dec}: {e}")
            return TimeSeriesEvidence(
                available=False,
                mission="TESS",
                time_series_status="NO_TIME_SERIES_AVAILABLE",
                signal_hint="QUERY_FALLBACK"
            ), prov_items
