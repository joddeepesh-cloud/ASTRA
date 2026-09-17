import logging
import time
from typing import Optional, Dict, Any

from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, TargetCoordinates, CatalogMatch, EvidenceProvenance,
    AstrometryEvidence, SpectroscopyEvidence, PhotometryEvidence,
    TimeSeriesEvidence, ExoplanetEvidence, NebulaEvidence
)
from backend.app.services.evidence.gaia_adapter import GaiaAdapter
from backend.app.services.evidence.sdss_adapter import SdssAdapter
from backend.app.services.evidence.wise_adapter import WiseAdapter
from backend.app.services.evidence.tess_adapter import TessAdapter
from backend.app.services.evidence.exoplanet_archive_adapter import ExoplanetArchiveAdapter
from backend.app.services.evidence.nebula_adapter import NebulaAdapter

logger = logging.getLogger("astra.evidence.service")

class EvidenceService:
    """
    ASTRA Multi-Modal Astronomical Evidence Service Orchestrator.
    Manages external catalog evidence adapters with offline-first guarantees,
    timeout handling, error isolation, and scientific provenance tracking.
    """
    def __init__(
        self,
        offline_mode: bool = True,
        timeout_sec: float = 2.0,
        gaia_adapter: Optional[GaiaAdapter] = None,
        sdss_adapter: Optional[SdssAdapter] = None,
        wise_adapter: Optional[WiseAdapter] = None,
        tess_adapter: Optional[TessAdapter] = None,
        exoplanet_adapter: Optional[ExoplanetArchiveAdapter] = None,
        nebula_adapter: Optional[NebulaAdapter] = None
    ):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

        self.gaia_adapter = gaia_adapter or GaiaAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)
        self.sdss_adapter = sdss_adapter or SdssAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)
        self.wise_adapter = wise_adapter or WiseAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)
        self.tess_adapter = tess_adapter or TessAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)
        self.exoplanet_adapter = exoplanet_adapter or ExoplanetArchiveAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)
        self.nebula_adapter = nebula_adapter or NebulaAdapter(offline_mode=offline_mode, timeout_sec=timeout_sec)

    def fetch_evidence_bundle(
        self,
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        target_id: Optional[str] = None
    ) -> EvidenceBundle:
        """
        Assemble unified Multi-Modal Evidence Bundle for a celestial target coordinate/ID.
        Fully isolated and safe: network errors or missing coordinates return clean offline bundles.
        """
        t0 = time.perf_counter()

        matches = []
        provenance = []

        # 1. Gaia DR3 Astrometry
        try:
            astrom, g_prov, g_match = self.gaia_adapter.lookup(ra, dec)
            provenance.extend(g_prov)
            if g_match:
                matches.append(g_match)
        except Exception as e:
            logger.error(f"Gaia adapter exception: {e}")
            astrom = AstrometryEvidence(available=False, source="Gaia DR3")

        # 2. SDSS Spectroscopy & Quasar Catalog
        try:
            spectro, s_prov, s_match = self.sdss_adapter.lookup(ra, dec)
            provenance.extend(s_prov)
            if s_match:
                matches.append(s_match)
        except Exception as e:
            logger.error(f"SDSS adapter exception: {e}")
            spectro = SpectroscopyEvidence(available=False, source="SDSS DR16")

        # 3. ALLWISE Infrared Photometry
        try:
            photo, w_prov, w_match = self.wise_adapter.lookup(ra, dec)
            provenance.extend(w_prov)
            if w_match:
                matches.append(w_match)
        except Exception as e:
            logger.error(f"WISE adapter exception: {e}")
            photo = PhotometryEvidence(available=False, source="ALLWISE")

        # 4. TESS / Light Curve Time Series
        try:
            ts, t_prov = self.tess_adapter.lookup(ra, dec, target_id=target_id)
            provenance.extend(t_prov)
        except Exception as e:
            logger.error(f"TESS adapter exception: {e}")
            ts = TimeSeriesEvidence(available=False, status="NO_LIGHT_CURVE_AVAILABLE", signal_hint="INSUFFICIENT_DATA")

        # 5. NASA Exoplanet Archive
        try:
            exo, e_prov, e_match = self.exoplanet_adapter.lookup(ra, dec)
            provenance.extend(e_prov)
            if e_match:
                matches.append(e_match)
        except Exception as e:
            logger.error(f"Exoplanet adapter exception: {e}")
            exo = ExoplanetEvidence(available=False)

        # 6. Nebula Catalog
        try:
            neb, n_prov, n_match = self.nebula_adapter.lookup(ra, dec)
            provenance.extend(n_prov)
            if n_match:
                matches.append(n_match)
        except Exception as e:
            logger.error(f"Nebula adapter exception: {e}")
            neb = NebulaEvidence(available=False)

        t1 = time.perf_counter()
        latency_ms = round((t1 - t0) * 1000.0, 2)

        availability = {
            "astrometry": astrom.available,
            "spectroscopy": spectro.available,
            "photometry": photo.available,
            "time_series": ts.available,
            "exoplanet": exo.available,
            "nebula": neb.available
        }

        return EvidenceBundle(
            target_coordinates=TargetCoordinates(ra=ra, dec=dec),
            catalog_matches=matches,
            astrometry=astrom,
            spectroscopy=spectro,
            photometry=photo,
            time_series=ts,
            exoplanet=exo,
            nebula=neb,
            provenance_items=provenance,
            availability_summary=availability,
            latency_ms=latency_ms
        )

# Global singleton evidence service instance
evidence_service = EvidenceService(offline_mode=True)
