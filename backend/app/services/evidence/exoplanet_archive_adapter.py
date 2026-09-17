import logging
import requests
import urllib.parse
from typing import Tuple, List, Optional
from backend.app.services.evidence.evidence_models import ExoplanetEvidence, EvidenceProvenance, CatalogMatch

logger = logging.getLogger("astra.evidence.exoplanet")

class ExoplanetArchiveAdapter:
    """
    Adapter for NASA Exoplanet Archive TAP service host star and exoplanet evidence acquisition.
    """
    def __init__(self, offline_mode: bool = False, timeout_sec: float = 3.0):
        self.offline_mode = offline_mode
        self.timeout_sec = timeout_sec

    def lookup(
        self,
        ra: Optional[float],
        dec: Optional[float],
        search_radius_arcsec: float = 5.0
    ) -> Tuple[ExoplanetEvidence, List[EvidenceProvenance], Optional[CatalogMatch]]:
        """
        Execute TAP cone-search lookup against NASA Exoplanet Archive pscomppars table.
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
            radius_deg = search_radius_arcsec / 3600.0
            query = (
                f"SELECT pl_name, hostname, ra, dec, pl_orbper, pl_trandep, discoverymethod, disc_facility "
                f"FROM pscomppars WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius_deg})) = 1"
            )
            url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={urllib.parse.quote(query)}&format=json"

            resp = requests.get(url, timeout=self.timeout_sec)
            if resp.status_code != 200:
                logger.warning(f"NASA Exoplanet Archive TAP returned status {resp.status_code}")
                return ExoplanetEvidence(available=False), prov_items, None

            data = resp.json()
            if not data:
                return ExoplanetEvidence(available=False, exoplanet_status="NO_CATALOG_MATCH"), prov_items, None

            match_rec = data[0]
            m_ra = float(match_rec.get("ra", ra))
            m_dec = float(match_rec.get("dec", dec))
            pl_name = match_rec.get("pl_name", "Confirmed Exoplanet")
            hostname = match_rec.get("hostname", "Host Star")
            method = match_rec.get("discoverymethod", "Transit")
            period = float(match_rec["pl_orbper"]) if match_rec.get("pl_orbper") is not None else None
            depth = float(match_rec["pl_trandep"]) if match_rec.get("pl_trandep") is not None else None

            # Calculate approximate separation
            sep_arcsec = round(((ra - m_ra)**2 + (dec - m_dec)**2)**0.5 * 3600.0, 3)

            cat_match = CatalogMatch(
                catalog_name="NASA Exoplanet Archive",
                source_id=pl_name,
                ra=m_ra,
                dec=m_dec,
                match_distance_arcsec=sep_arcsec,
                quality_flag="CONFIRMED_EXOPLANET"
            )

            prov_items.append(EvidenceProvenance(
                source="NASA Exoplanet Archive",
                field="confirmed_planet",
                value=f"{pl_name} (Host: {hostname})",
                unit="discovery_method: " + method,
                match_distance_arcsec=sep_arcsec,
                provenance="external_catalog_tap",
                interpretation=f"Confirmed exoplanet target {pl_name} (Orbital Period: {period} days, Method: {method})"
            ))

            evidence = ExoplanetEvidence(
                available=True,
                known_planet=True,
                known_host=True,
                planet_name=pl_name,
                hostname=hostname,
                discovery_method=method,
                orbital_period_days=period,
                transit_depth=depth,
                disposition="CONFIRMED",
                match_distance_arcsec=sep_arcsec,
                exoplanet_status="KNOWN_EXOPLANET_MATCH"
            )

            return evidence, prov_items, cat_match

        except Exception as e:
            logger.error(f"Error executing NASA Exoplanet Archive TAP lookup: {e}")
            return ExoplanetEvidence(available=False, exoplanet_status="NO_CATALOG_MATCH"), prov_items, None
