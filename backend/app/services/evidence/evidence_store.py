import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("astra.evidence_store")

class EvidenceStore:
    """
    Lightweight, persistent in-memory evidence store backed by a local JSON file.
    Stores evidence enrichment records keyed by observation_id.
    """
    def __init__(self, storage_filepath: Optional[str] = None):
        if storage_filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            storage_filepath = os.path.join(base_dir, "docs", "evidence_store.json")

        self.storage_filepath = storage_filepath
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        """Load records from local JSON file if present."""
        if os.path.exists(self.storage_filepath):
            try:
                with open(self.storage_filepath, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
                logger.info(f"Loaded {len(self._store)} evidence records from {self.storage_filepath}")
            except Exception as e:
                logger.warning(f"Failed to load evidence store file {self.storage_filepath}: {e}")
                self._store = {}
        else:
            self._store = {}

    def _save(self):
        """Flush store to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.storage_filepath), exist_ok=True)
            with open(self.storage_filepath, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save evidence store to {self.storage_filepath}: {e}")

    def get_evidence(self, observation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored evidence record for observation_id."""
        return self._store.get(observation_id)

    def set_evidence(self, observation_id: str, record: Dict[str, Any]):
        """Store or update evidence record for observation_id."""
        record["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._store[observation_id] = record
        self._save()

    def set_status(self, observation_id: str, status: str, explanation: str = "", ra: Optional[float] = None, dec: Optional[float] = None):
        """Set initial status record for observation_id."""
        rec = self._store.get(observation_id, {
            "observation_id": observation_id,
            "evidence_status": status,
            "ra": ra,
            "dec": dec,
            "fused_object_type": None,
            "evidence_level": "NONE",
            "match_quality": "UNAVAILABLE" if ra is None or dec is None else "NO_MATCH",
            "catalog_sources_queried": ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
            "contributing_catalogs": [],
            "explanation": explanation,
            "provenance": [],
            "conflicts": [],
            "fused_result": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        })
        rec["evidence_status"] = status
        if explanation:
            rec["explanation"] = explanation
        if ra is not None:
            rec["ra"] = ra
        if dec is not None:
            rec["dec"] = dec
        self.set_evidence(observation_id, rec)

# Global singleton instance
evidence_store = EvidenceStore()
