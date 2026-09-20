import logging
from typing import Dict, Any, Optional, List, Tuple
from backend.app.services.evidence.evidence_models import (
    EvidenceBundle, FusedEvidenceResult, EvidenceProvenance, CatalogMatch
)

logger = logging.getLogger("astra.evidence.fusion")

class EvidenceFusionEngine:
    """
    ASTRA Multi-Modal Evidence Fusion Engine.
    Synthesizes local image structural metrics with external catalog evidence bundles (Gaia, SDSS, WISE, TESS, Exoplanet Archive).
    Operates under strict scientific ambiguity principles: never manufactures or forces predictions when evidence is insufficient or conflicting.
    """
    def fuse_evidence(
        self,
        local_result: Dict[str, Any],
        evidence_bundle: Optional[EvidenceBundle] = None
    ) -> FusedEvidenceResult:
        """
        Synthesize local image classification results with external evidence bundle.
        """
        if local_result is None:
            local_result = {}
        if evidence_bundle is None:
            evidence_bundle = EvidenceBundle()

        local_pred = local_result.get("predicted_object_type", "ASTRONOMICAL_SOURCE_AMBIGUOUS")

        prov_chain: List[EvidenceProvenance] = list(evidence_bundle.provenance_items)

        # 1. Domain Rejection Pass
        if local_pred == "INCOMPATIBLE" or local_result.get("domain_validation", {}).get("decision") == "INCOMPATIBLE":
            return FusedEvidenceResult(
                target_decision="INCOMPATIBLE",
                primary_rationale="Observation fails astronomical domain validation. Outside ASTRA domain.",
                evidence_level="NONE",
                match_quality="UNAVAILABLE",
                is_conflicting=False,
                image_evidence_type="INCOMPATIBLE",
                provenance_chain=prov_chain,
                scientific_disclaimer="Non-astronomical input rejected by domain validation gates."
            )

        # 2. Evaluate Match Quality
        match_quality = self._evaluate_overall_match_quality(evidence_bundle)

        # 3. Handle GALAXY targets
        if local_pred == "GALAXY":
            gz_morph = local_result.get("morphology") or local_result.get("predicted_class")
            morph_str = f" (Morphology: {gz_morph})" if gz_morph else ""
            
            # Check for chance alignment foreground star
            g_astrom = evidence_bundle.astrometry
            if g_astrom.available and g_astrom.match_distance_arcsec is not None and g_astrom.match_distance_arcsec > 1.5:
                prov_chain.append(EvidenceProvenance(
                    source="Gaia DR3",
                    field="spatial_match",
                    value=f"Offset {g_astrom.match_distance_arcsec:.2f} arcsec",
                    provenance="spatial_analysis",
                    interpretation="Nearby stellar match is a projected foreground/background source, not host galaxy identity"
                ))

            return FusedEvidenceResult(
                target_decision="GALAXY",
                primary_rationale=f"Image structural analysis confirms extended astronomical light distribution{morph_str}.",
                evidence_level="STRONG" if gz_morph else "MODERATE",
                match_quality=match_quality,
                is_conflicting=False,
                image_evidence_type="GALAXY",
                galaxy_evidence_strength="STRONG" if gz_morph else "MODERATE",
                provenance_chain=prov_chain,
                scientific_disclaimer="Extended galaxy evidence established independently by image structural analysis."
            )

        # 4. Handle Point Sources (STAR vs QUASAR vs AMBIGUOUS vs CONFLICT)
        if local_pred in ("AMBIGUOUS_POINT_SOURCE", "STAR", "QUASAR", "QUASAR_CANDIDATE"):
            return self._fuse_point_source(local_result, evidence_bundle, match_quality, prov_chain)

        # 5. Handle Diffuse Sources / NEBULA
        if local_pred in ("NEBULA_CANDIDATE", "NEBULA"):
            neb_ev = evidence_bundle.nebula
            if neb_ev.available and neb_ev.is_catalog_nebula and (neb_ev.match_distance_arcsec is None or neb_ev.match_distance_arcsec <= 3.0):
                return FusedEvidenceResult(
                    target_decision="NEBULA_CANDIDATE",
                    primary_rationale=f"Diffuse emission structure matched with catalog nebula {neb_ev.catalog_name} ({neb_ev.nebula_type or 'nebula'}).",
                    evidence_level="STRONG",
                    match_quality=match_quality,
                    is_conflicting=False,
                    image_evidence_type="DIFFUSE",
                    nebula_evidence_strength="STRONG",
                    provenance_chain=prov_chain,
                    scientific_disclaimer="Nebula classification supported by diffuse emission and catalog evidence."
                )
            else:
                return FusedEvidenceResult(
                    target_decision="ASTRONOMICAL_SOURCE_AMBIGUOUS",
                    primary_rationale="Diffuse astronomical structure detected, but supporting emission-line or infrared dust catalog evidence is unavailable.",
                    evidence_level="WEAK",
                    match_quality=match_quality,
                    is_conflicting=False,
                    image_evidence_type="DIFFUSE",
                    nebula_evidence_strength="WEAK",
                    provenance_chain=prov_chain,
                    scientific_disclaimer="Diffuse structures without emission-line or catalog proof resolve to ambiguous astronomical source."
                )

        # 6. Default Fallback for Ambiguous / Low Confidence Astronomical Targets
        return FusedEvidenceResult(
            target_decision="ASTRONOMICAL_SOURCE_AMBIGUOUS",
            primary_rationale="Astronomical light profile detected, but multi-modal evidence is weak or insufficient to establish definitive classification.",
            evidence_level="WEAK",
            match_quality=match_quality,
            is_conflicting=False,
            image_evidence_type=local_pred,
            provenance_chain=prov_chain,
            scientific_disclaimer="Preserved in conservative ambiguous state pending higher-resolution multi-band or spectroscopic data."
        )

    def _fuse_point_source(
        self,
        local_result: Dict[str, Any],
        bundle: EvidenceBundle,
        match_quality: str,
        prov_chain: List[EvidenceProvenance]
    ) -> FusedEvidenceResult:
        """
        Evaluate multi-modal evidence for compact unresolved point sources.
        """
        g_astrom = bundle.astrometry
        s_spectro = bundle.spectroscopy
        w_photo = bundle.photometry
        exo_ev = bundle.exoplanet
        ts_ev = bundle.time_series
        local_pred = local_result.get("predicted_object_type", "AMBIGUOUS_POINT_SOURCE")

        # Stellar evidence strength evaluation
        has_strong_star = False
        star_strength = "NONE"
        if g_astrom.available and (g_astrom.match_distance_arcsec is None or g_astrom.match_distance_arcsec <= 2.0):
            has_parallax = g_astrom.parallax_mas is not None and g_astrom.parallax_mas > 0.0
            has_pm = (g_astrom.proper_motion_ra_mas_yr is not None and abs(g_astrom.proper_motion_ra_mas_yr) >= 3.0) or \
                     (g_astrom.proper_motion_dec_mas_yr is not None and abs(g_astrom.proper_motion_dec_mas_yr) >= 3.0)
            if has_parallax or has_pm:
                has_strong_star = True
                star_strength = "DECISIVE" if (has_parallax and has_pm) else "STRONG"

        # Quasar evidence strength evaluation
        has_strong_quasar = False
        quasar_strength = "NONE"
        if s_spectro.available and (s_spectro.match_distance_arcsec is None or s_spectro.match_distance_arcsec <= 2.0):
            has_redshift = s_spectro.redshift is not None and s_spectro.redshift > 0.05
            is_qso_class = s_spectro.spectral_class in ("QSO", "QUASAR") or s_spectro.is_quasar_catalog_member
            if has_redshift or is_qso_class:
                has_strong_quasar = True
                quasar_strength = "DECISIVE" if (has_redshift and is_qso_class) else "STRONG"

        # Photometric supporting evidence (WISE color W1 - W2 > 0.8)
        has_wise_quasar_color = False
        if w_photo.available and w_photo.w1_minus_w2 is not None and w_photo.w1_minus_w2 >= 0.8 and (w_photo.match_distance_arcsec is None or w_photo.match_distance_arcsec <= 2.0):
            has_wise_quasar_color = True
            if quasar_strength == "NONE":
                quasar_strength = "MODERATE"

        # Exoplanet catalog status
        exo_status = exo_ev.exoplanet_status if exo_ev.available else "NO_CATALOG_MATCH"
        if exo_ev.available:
            if exo_ev.known_planet:
                exo_status = f"KNOWN_CATALOG_PLANET ({exo_ev.planet_name or 'Exoplanet'})"
            elif exo_ev.known_host:
                exo_status = "KNOWN_CATALOG_HOST_STAR"
            elif exo_ev.candidate:
                exo_status = "CANDIDATE_HOST"

        # Check for confirmed exoplanet match from NASA Exoplanet Archive
        is_known_exoplanet = exo_ev.available and (exo_ev.known_planet or exo_ev.exoplanet_status in ("KNOWN_EXOPLANET_MATCH", "CONFIRMED"))
        
        # Check for exoplanet candidate (TOI/Kepler candidate or transit-like light curve signal)
        is_exoplanet_candidate = (
            (exo_ev.available and (exo_ev.candidate or exo_ev.exoplanet_status == "CANDIDATE")) or
            (ts_ev.available and ts_ev.time_series_status == "TRANSIT_LIKE_SIGNAL")
        )

        # 1. KNOWN EXOPLANET MATCH DECISION
        if is_known_exoplanet:
            planet_info = f" ({exo_ev.planet_name})" if exo_ev.planet_name else ""
            period_info = f", Period: {exo_ev.orbital_period_days:.2f} d" if exo_ev.orbital_period_days else ""
            return FusedEvidenceResult(
                target_decision="KNOWN_EXOPLANET_MATCH",
                primary_rationale=f"Target cross-matched with confirmed exoplanet record in NASA Exoplanet Archive{planet_info}{period_info}.",
                evidence_level="DECISIVE",
                match_quality=match_quality,
                is_conflicting=False,
                image_evidence_type="POINT_SOURCE",
                stellar_evidence_strength=star_strength if has_strong_star else "STRONG",
                quasar_evidence_strength="NONE",
                exoplanet_evidence_status=f"KNOWN_EXOPLANET_MATCH ({exo_ev.planet_name or 'Confirmed Planet'})",
                provenance_chain=prov_chain,
                scientific_disclaimer="Confirmed exoplanet cross-match from NASA Exoplanet Archive TAP service."
            )

        # 2. EXOPLANET CANDIDATE DECISION
        if is_exoplanet_candidate and not has_strong_quasar:
            cand_info = f" ({exo_ev.planet_name})" if exo_ev.planet_name else ""
            depth_info = f", Transit Depth: {ts_ev.transit_depth:.4f}%" if ts_ev.transit_depth else ""
            return FusedEvidenceResult(
                target_decision="EXOPLANET_CANDIDATE",
                primary_rationale=f"Point source associated with planetary candidate or photometric transit-like light curve signal{cand_info}{depth_info}.",
                evidence_level="STRONG" if (ts_ev.transit_depth or exo_ev.candidate) else "MODERATE",
                match_quality=match_quality,
                is_conflicting=False,
                image_evidence_type="POINT_SOURCE",
                stellar_evidence_strength=star_strength if has_strong_star else "STRONG",
                quasar_evidence_strength="NONE",
                exoplanet_evidence_status="EXOPLANET_CANDIDATE",
                provenance_chain=prov_chain,
                scientific_disclaimer="Exoplanet candidate signal requires further high-cadence spectroscopic or transit follow-up."
            )

        # 3. CONFLICT DETECTION: Both decisive stellar and decisive quasar evidence exist
        if has_strong_star and has_strong_quasar:
            return FusedEvidenceResult(
                target_decision="CONFLICTING_POINT_SOURCE_EVIDENCE",
                primary_rationale="Conflicting multi-modal evidence: Gaia DR3 indicates stellar parallax/proper motion while SDSS spectroscopy indicates quasar redshift.",
                evidence_level="STRONG",
                match_quality=match_quality,
                is_conflicting=True,
                image_evidence_type="POINT_SOURCE",
                stellar_evidence_strength=star_strength,
                quasar_evidence_strength=quasar_strength,
                exoplanet_evidence_status=exo_status,
                provenance_chain=prov_chain,
                scientific_disclaimer="Preserved in conservative conflicting state. Requires manual expert review."
            )

        # 4. STAR DECISION: Strong stellar catalog evidence OR local visual STAR prediction without quasar conflict
        if (has_strong_star or local_pred == "STAR") and not has_strong_quasar:
            has_both_pm = g_astrom.proper_motion_ra_mas_yr is not None and g_astrom.proper_motion_dec_mas_yr is not None
            pm_str = f" (Proper Motion: RA {g_astrom.proper_motion_ra_mas_yr:.1f}, DEC {g_astrom.proper_motion_dec_mas_yr:.1f} mas/yr)" if has_both_pm else ""
            plx_str = f" (Parallax: {g_astrom.parallax_mas:.2f} mas)" if g_astrom.parallax_mas is not None else ""
            rationale = f"Point source light profile supported by Gaia DR3 astrometric evidence{plx_str}{pm_str}." if has_strong_star else "Point source light profile supported by OpenCLIP zero-shot visual similarity and compact PSF structural analysis."
            return FusedEvidenceResult(
                target_decision="STAR",
                primary_rationale=rationale,
                evidence_level=star_strength if has_strong_star else "MODERATE",
                match_quality=match_quality,
                is_conflicting=False,
                image_evidence_type="POINT_SOURCE",
                stellar_evidence_strength=star_strength if has_strong_star else "MODERATE",
                quasar_evidence_strength="NONE",
                exoplanet_evidence_status=exo_status,
                provenance_chain=prov_chain,
                scientific_disclaimer="Classification supported by unresolved point-source imaging and Gaia DR3 astrometry." if has_strong_star else "Classification supported by unresolved point-source visual imaging."
            )

        # 5. QUASAR CANDIDATE DECISION: Strong quasar catalog evidence OR local visual QUASAR candidate prediction without stellar conflict
        if (has_strong_quasar or local_pred == "QUASAR_CANDIDATE") and not has_strong_star:
            z_str = f" (Redshift z = {s_spectro.redshift:.3f})" if s_spectro.redshift else ""
            rationale = f"Point source light profile supported by SDSS spectroscopic quasar evidence{z_str}." if has_strong_quasar else "Point source light profile supported by OpenCLIP zero-shot visual similarity and compact AGN structural analysis."
            return FusedEvidenceResult(
                target_decision="QUASAR_CANDIDATE",
                primary_rationale=rationale,
                evidence_level=quasar_strength if has_strong_quasar else "MODERATE",
                match_quality=match_quality,
                is_conflicting=False,
                image_evidence_type="POINT_SOURCE",
                stellar_evidence_strength="NONE",
                quasar_evidence_strength=quasar_strength if has_strong_quasar else "MODERATE",
                exoplanet_evidence_status=exo_status,
                provenance_chain=prov_chain,
                scientific_disclaimer="Classification supported by point-source imaging and SDSS spectroscopic evidence." if has_strong_quasar else "Classification supported by point-source visual imaging."
            )

        # 6. AMBIGUOUS POINT SOURCE (Default conservative decision)
        reason = "Unresolved compact point source. Multi-modal evidence is insufficient to reliably separate stellar and quasar interpretations without spectroscopy or astrometry."
        if has_wise_quasar_color:
            reason += f" (WISE W1-W2={w_photo.w1_minus_w2:.2f} mag suggests IR excess, but spectroscopy/astrometry is required)."

        return FusedEvidenceResult(
            target_decision="AMBIGUOUS_POINT_SOURCE",
            primary_rationale=reason,
            evidence_level="WEAK" if has_wise_quasar_color else "NONE",
            match_quality=match_quality,
            is_conflicting=False,
            image_evidence_type="POINT_SOURCE",
            stellar_evidence_strength=star_strength,
            quasar_evidence_strength=quasar_strength,
            exoplanet_evidence_status=exo_status,
            provenance_chain=prov_chain,
            scientific_disclaimer="Optical imaging alone cannot resolve star vs quasar ambiguity. Preserved as Ambiguous Point Source."
        )

    def _evaluate_overall_match_quality(self, bundle: EvidenceBundle) -> str:
        """
        Evaluates best angular separation match quality across catalog matches.
        """
        if not bundle.catalog_matches:
            return "NO_MATCH" if bundle.target_coordinates.ra is not None else "UNAVAILABLE"

        min_dist = min((m.match_distance_arcsec for m in bundle.catalog_matches if m.match_distance_arcsec is not None), default=999.0)

        if min_dist <= 1.0:
            return "HIGH_QUALITY_MATCH"
        elif min_dist <= 2.0:
            return "GOOD_MATCH"
        elif min_dist <= 3.0:
            return "WEAK_MATCH"
        else:
            return "NO_MATCH"

# Global singleton evidence fusion engine instance
evidence_fusion_engine = EvidenceFusionEngine()
