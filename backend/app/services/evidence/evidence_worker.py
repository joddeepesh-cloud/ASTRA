import logging
from typing import Optional, Dict, Any
from datetime import datetime

from backend.app.services.evidence.evidence_service import evidence_service
from backend.app.services.evidence.evidence_fusion import evidence_fusion_engine
from backend.app.services.evidence.evidence_store import evidence_store

logger = logging.getLogger("astra.evidence_worker")

async def run_background_evidence_enrichment(
    observation_id: str,
    ra: Optional[float],
    dec: Optional[float],
    image_evidence: Optional[Dict[str, Any]] = None
):
    """
    Background worker function called via FastAPI BackgroundTasks.
    Coordinates external evidence retrieval, fusion, and persistence.
    """
    logger.info(f"Starting background evidence enrichment for observation '{observation_id}' (RA: {ra}, DEC: {dec})")

    if ra is None or dec is None:
        logger.info(f"Observation '{observation_id}' has no trusted celestial coordinates; setting status to UNAVAILABLE.")
        evidence_store.set_status(
            observation_id=observation_id,
            status="UNAVAILABLE",
            explanation="Catalog enrichment unavailable — no trusted celestial coordinates were supplied.",
            ra=None,
            dec=None
        )
        return

    # Update status to PENDING
    evidence_store.set_status(
        observation_id=observation_id,
        status="PENDING",
        explanation="Multi-modal catalog evidence retrieval and fusion in progress...",
        ra=ra,
        dec=dec
    )

    try:
        # 1. Asynchronously retrieve catalog evidence bundle from external adapters
        bundle = await evidence_service.get_evidence_bundle(ra=ra, dec=dec)

        # 2. Execute EvidenceFusionEngine on image evidence + catalog bundle
        fused_result = evidence_fusion_engine.fuse_evidence(
            image_evidence=image_evidence,
            catalog_bundle=bundle
        )

        # 3. Construct record and update store
        record = {
            "observation_id": observation_id,
            "evidence_status": "COMPLETE",
            "ra": ra,
            "dec": dec,
            "fused_object_type": fused_result.fused_object_type.value,
            "evidence_level": fused_result.evidence_level.value,
            "match_quality": fused_result.match_quality.value,
            "catalog_sources_queried": ["Gaia DR3", "SDSS DR16", "ALLWISE", "TESS", "NASA Exoplanet Archive", "SIMBAD"],
            "contributing_catalogs": fused_result.contributing_catalogs,
            "explanation": fused_result.scientific_justification,
            "provenance": fused_result.provenance,
            "conflicts": fused_result.conflicts,
            "fused_result": fused_result.to_dict(),
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }

        evidence_store.set_evidence(observation_id, record)
        logger.info(
            f"Successfully completed background evidence enrichment for '{observation_id}': "
            f"Result={fused_result.fused_object_type.value} [Level={fused_result.evidence_level.value}, Quality={fused_result.match_quality.value}]"
        )

    except Exception as e:
        logger.error(f"Error executing background evidence enrichment for '{observation_id}': {e}", exc_info=True)
        evidence_store.set_status(
            observation_id=observation_id,
            status="ERROR",
            explanation=f"Evidence enrichment failed: {str(e)}",
            ra=ra,
            dec=dec
        )
