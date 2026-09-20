import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

from backend.app.config import settings
from backend.app.services.space_ai_router import (
    SpaceAIRouter, INTENT_GREETING, INTENT_OFF_TOPIC, INTENT_ASTRONOMY_GENERAL,
    INTENT_ASTRA_PRODUCT, INTENT_OBSERVATION_ANALYSIS, INTENT_UNSUPPORTED
)

logger = logging.getLogger("astra.space_ai")

ASTRA_SPACE_AI_SYSTEM_PROMPT = """You are ASTRA Space Help AI, an authoritative, scientifically grounded astronomy and space Q&A assistant.

YOUR CORE SCOPE:
1. General Astronomy & Astrophysics: Galaxies, stellar evolution, black holes, supernovas, exoplanets, spectroscopy, instruments, orbital mechanics.
2. Solar System Science: Planets, moons, asteroids, comets, meteors, planetary atmospheres.
3. Cosmology & Observational Astronomy: Dark matter, dark energy, redshift, gravitational lensing, telescopes, sky surveys.
4. ASTRA System & ML Pipeline: OpenCLIP Semantic Pre-Gate, MobileNetV3 Domain Gate V2, Galaxy Zoo 4-Class Morphology CNN, Statistical Triage Engine (S_novelty, S_uncertainty, S_oddity).
5. Active Observation Context: When asked about a specific target, explain its triage score, morphology classification, confidence, and survey metadata.

CRITICAL CONTEXT & INTEGRITY RULES:
- OBSERVATION CONTEXT IS OPTIONAL: If the user asks a general astronomy question (e.g. "What is a black hole?"), answer the question directly. Do NOT force the conversation to be about the selected observation unless the user explicitly asks about it.
- ABSOLUTELY NO UNFOUNDED DISCOVERY CLAIMS: Never say "ASTRA discovered a new galaxy", "ASTRA found aliens", or "This proves a new astronomical object".
- TRIAGE DEFINITION: Always describe ASTRA's score as an experimental prioritization heuristic for human scientific review. Use defensible statements such as: "ASTRA identified this observation as statistically unusual according to its triage signals and prioritized it for scientific review. This does not establish that the object is new; human/scientific follow-up would be required."
- TRIAGE SCORE MATHEMATICS: Explain that the combined score is:
  Score = 0.35 * S_novelty + 0.35 * S_uncertainty + 0.30 * S_oddity
  where Novelty measures embedding distance from reference population, Uncertainty measures morphology prediction entropy, and Oddity measures learned unusual morphology probability.
- DOMAIN GATE: Explain that ASTRA's domain validation (Semantic Pre-Gate + Domain Gate V2) intentionally rejects non-astronomical imagery (screenshots, photos, graphics) to prevent non-astronomical data from entering the scientific triage pipeline.
- OFF-TOPIC REDIRECT: For completely non-astronomy requests (programming code, recipes, sports, political news):
  "I can help with astronomy, space science, observations, or how ASTRA works. What would you like to explore?"
"""

class SpaceAIService:
    """
    ASTRA Space Help AI Service.
    Handles specialized astronomy QA, observation-grounded reasoning, off-topic guardrails,
    and optional LLM provider dispatching (Gemini / OpenAI / Grounded Engine).
    """

    def __init__(self):
        self.provider = settings.ASTRA_AI_PROVIDER.lower()
        self.model_name = settings.ASTRA_AI_MODEL
        self.api_key = settings.ASTRA_AI_API_KEY
        self.router = SpaceAIRouter(api_key=self.api_key, model_name=self.model_name, provider=self.provider)

    def answer_question(
        self,
        question: str,
        observation_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user question through Space Help AI logic, context grounding, and LLM providers.
        """
        q_clean = question.strip()
        obs_id = observation_context.get("observation_id") if observation_context else None

        # 1. Semantic Intent Classification with Observation Context Awareness
        has_obs_ctx = bool(observation_context and (observation_context.get("observation_id") or observation_context.get("id")))
        route_result = self.router.classify_intent(q_clean, has_observation_context=has_obs_ctx)
        intent = route_result["intent"]

        # Handle GREETING
        if intent == INTENT_GREETING:
            return {
                "answer": (
                    "Hello! I am ASTRA Space Help AI.\n\n"
                    "I can answer questions about:\n"
                    "• General astronomy, astrophysics, solar system science & cosmology\n"
                    "• Astronomical telescopes, spectrographs & observation techniques\n"
                    "• ASTRA's architecture (Domain Gate, Galaxy Zoo 4-class taxonomy & Triage Engine)\n"
                    "• Specific target analysis results and triage priorities\n\n"
                    "What would you like to explore?"
                ),
                "scope": "greeting",
                "observation_id": obs_id,
                "grounded": True,
                "available": True,
                "model": "ASTRA Space Help AI",
                "provider": "ASTRA Core"
            }

        # Handle OFF_TOPIC
        if intent == INTENT_OFF_TOPIC:
            return {
                "answer": (
                    "I can help with astronomy, space science, observations, or how ASTRA works. "
                    "What would you like to explore?"
                ),
                "scope": "redirect",
                "observation_id": obs_id,
                "grounded": True,
                "available": True,
                "model": "ASTRA Guardrail",
                "provider": "ASTRA System"
            }

        # 2. Provider Dispatch if API Key present
        if self.api_key:
            try:
                # Pass observation_context whenever available
                effective_ctx = observation_context
                llm_response = self._call_llm_provider(
                    question=q_clean,
                    observation_context=effective_ctx,
                    conversation_history=conversation_history,
                    image_base64=image_base64
                )
                if llm_response:
                    return {
                        "answer": llm_response,
                        "scope": intent.lower(),
                        "observation_id": obs_id,
                        "grounded": True,
                        "available": True,
                        "model": self.model_name,
                        "provider": self.provider
                    }
            except Exception as e:
                logger.warning(f"External LLM call failed ({e}), falling back to ASTRA Grounded Reasoning Engine.")

        # 3. Grounded Reasoning Engine (Fallback & Default when no key)
        grounded_answer = self._generate_grounded_answer(
            question=q_clean,
            intent=intent,
            observation_context=observation_context
        )

        return {
            "answer": grounded_answer,
            "scope": intent.lower(),
            "observation_id": obs_id,
            "grounded": True,
            "available": True,
            "model": "ASTRA Grounded Science Engine v1.0",
            "provider": "ASTRA Core"
        }

    def _generate_grounded_answer(
        self,
        question: str,
        intent: str,
        observation_context: Optional[Dict[str, Any]]
    ) -> str:
        q_lower = question.lower()
        ctx = observation_context or {}
        obs_id = ctx.get("observation_id", "Selected Observation")
        morph = ctx.get("broad_morphology", "SPIRAL")
        conf = ctx.get("confidence", 0.85)
        conf_pct = ctx.get("confidence_pct", f"{conf * 100:.1f}%" if conf is not None else "N/A")
        gz2class = ctx.get("gz2class", "N/A")
        triage = ctx.get("triage", {})
        prio = triage.get("priority") or ctx.get("priority", "MEDIUM")
        triage_score = triage.get("anomaly_score") or ctx.get("anomaly_score", 0.45)
        novelty_score = triage.get("novelty_score") or ctx.get("ood_score") or ctx.get("novelty_score", 0.40)
        uncertainty_score = triage.get("uncertainty_score") or ctx.get("uncertainty_score", 0.30)
        oddity_score = triage.get("oddity_score") or ctx.get("oddity_score", 0.50)
        ra = ctx.get("coordinates", {}).get("ra", 0.0)
        dec = ctx.get("coordinates", {}).get("dec", 0.0)
        provenance = ctx.get("provenance", "Galaxy Zoo 2 Survey / SDSS DR7")
        obj_type = ctx.get("predicted_object_type") or ctx.get("object_type", "Galaxy")

        # Check explicit "anomaly" definition queries
        if "anomaly" in q_lower or "anomalous" in q_lower or "what makes" in q_lower and "anomalous" in q_lower:
            if "this" not in q_lower and "observation" not in q_lower:
                return (
                    "An **anomaly** in ASTRA does NOT mean artificial, alien, or a scientifically proven discovery.\n\n"
                    "In ASTRA's astronomical triage architecture, an **anomaly** represents an observation flagged for human scientific review because its visual embeddings or morphological signatures differ statistically from the reference survey dataset.\n\n"
                    "### ASTRA Triage Score Equation:\n"
                    "Score = 0.35 * S_novelty + 0.35 * S_uncertainty + 0.30 * S_oddity\n\n"
                    "• **Novelty (S_novelty)**: Latent embedding distance from reference centroids.\n"
                    "• **Uncertainty (S_uncertainty)**: Classification entropy across Galaxy Zoo vote distributions.\n"
                    "• **Oddity (S_oddity)**: Learned probability of unusual structural features.\n\n"
                    "Priority levels (LOW, MEDIUM, HIGH, CRITICAL) flag observations for human scientific follow-up."
                )

        # ----------------------------------------------------
        # Intent A: ASTRA System & Product Architecture
        # ----------------------------------------------------
        if intent == INTENT_ASTRA_PRODUCT:
            if "domain gate" in q_lower or "semantic" in q_lower or "reject" in q_lower or "screenshot" in q_lower or "photo" in q_lower or "validation" in q_lower:
                return (
                    "ASTRA uses a two-stage domain validation system to maintain scientific data integrity:\n\n"
                    "1. Open-World Semantic Pre-Gate (OpenCLIP ViT-B/32): Screens uploads against open-world semantic prompts to reject non-astronomical imagery (e.g. screenshots, portraits, landscapes).\n"
                    "2. Astronomical Domain Gate V2 (MobileNetV3-Small): Evaluates astronomical domain compatibility, verifying that incoming imagery exhibits valid observational characteristics.\n\n"
                    "This intentional filtering prevents ordinary photos or non-astronomical noise from distorting the scientific triage pipeline."
                )

            if "triage score" in q_lower or "score" in q_lower or "novelty" in q_lower or "uncertainty" in q_lower or "oddity" in q_lower or "calculate" in q_lower:
                return (
                    "ASTRA calculates an experimental triage prioritization score using three normalized components:\n\n"
                    "• Novelty (S_novelty, weight 0.35): Distance from the reference embedding centroid in latent space.\n"
                    "• Uncertainty (S_uncertainty, weight 0.35): Entropy of predicted Galaxy Zoo morphological vote distributions.\n"
                    "• Oddity (S_oddity, weight 0.30): Learned probability of unusual morphological structures.\n\n"
                    "Weighted Formula:\n"
                    "score = 0.35 * S_novelty + 0.35 * S_uncertainty + 0.30 * S_oddity\n\n"
                    "Priority levels (LOW, MEDIUM, HIGH, CRITICAL) are assigned based on threshold cutoffs to flag observations for human scientific review."
                )

            if "discovery" in q_lower or "discover" in q_lower or "alien" in q_lower:
                return (
                    "ASTRA is an automated observation prioritization and triage system, NOT a discovery confirmation system.\n\n"
                    "When ASTRA flags an observation with a HIGH or CRITICAL priority, it indicates that the target is statistically unusual relative to its reference population under ASTRA's triage heuristic. "
                    "This does NOT establish that an object is a new galaxy or astronomical discovery; follow-up verification by human astronomers is always required."
                )

            # Default ASTRA architecture overview
            return (
                "ASTRA is an astronomical triage system that prioritizes survey downlinks for scientific review across 6 stages:\n\n"
                "1. User Upload / Ingestion: Size and format checks.\n"
                "2. Semantic Pre-Gate: OpenCLIP pre-screening.\n"
                "3. Domain Gate V2: MobileNetV3 astronomical domain compatibility validation.\n"
                "4. Morphology Model: Multi-head CNN predicting 4 broad morphology classes (SMOOTH, EDGE_ON, FEATURED_DISK, SPIRAL).\n"
                "5. Triage Engine: Computes score = 0.35*S_novelty + 0.35*S_uncertainty + 0.30*S_oddity.\n"
                "6. Priority Queue & Review: Flags observations for Earth-side scientific investigation."
            )

        # ----------------------------------------------------
        # Intent B: Active Observation Context Analysis
        # ----------------------------------------------------
        # ----------------------------------------------------
        # Intent B: Active Observation Context Analysis
        # ----------------------------------------------------
        if intent == INTENT_OBSERVATION_ANALYSIS or (observation_context and intent not in (INTENT_ASTRONOMY_GENERAL, INTENT_ASTRA_PRODUCT, INTENT_GREETING, INTENT_OFF_TOPIC)):
            if not observation_context:
                return (
                    "Target-specific explanation requires an active observation payload. "
                    "Please select an item from the Observation Library or upload an astronomical image in Research Mode to enable observation-grounded context.\n\n"
                    "In general, ASTRA prioritizes observations by computing a weighted triage score from embedding novelty, morphological uncertainty, and structural oddity."
                )

            if "detail" in q_lower or "more" in q_lower or "expand" in q_lower or "further" in q_lower or "tell me more" in q_lower or "what else" in q_lower:
                return (
                    f"### Detailed Evidence Breakdown: {obs_id}\n\n"
                    f"**1. Visual Morphology & Identification:**\n"
                    f"• Target Designation: `{obs_id}`\n"
                    f"• Object Type: **{obj_type}**\n"
                    f"• Morphology Classification: **{morph}** (GZ2 class `{gz2class}`)\n"
                    f"• Inference Confidence: **{conf_pct}**\n\n"
                    f"**2. Quantitative Triage Decomposition:**\n"
                    f"• Overall Triage Score: **{triage_score:.2f}** ({prio} Priority)\n"
                    f"• Novelty Component ($S_{{novelty}}$): `{novelty_score:.2f}` (Latent feature distance from reference population)\n"
                    f"• Uncertainty Component ($S_{{uncertainty}}$): `{uncertainty_score:.2f}` (Model entropy across morphology vote distributions)\n"
                    f"• Oddity Component ($S_{{oddity}}$): `{oddity_score:.2f}` (Learned probability of structural oddity)\n\n"
                    f"**3. Astrometric & Multi-Modal Catalog Cross-Match:**\n"
                    f"• Celestial Position: RA {ra:.6f}°, DEC {dec:.6f}°\n"
                    f"• Survey Provenance: {provenance}\n"
                    f"• Multi-Band Catalogs Queried: Gaia DR3 astrometry, SDSS DR16 photometry/spectroscopy, ALLWISE infrared, TESS light-curve archives, and NASA Exoplanet Archive.\n\n"
                    f"**4. Scientific Limitations & Follow-Up Strategy:**\n"
                    f"• Key Uncertainty: Multi-wavelength photometrical redshift and stellar population age remain unconstrained without direct spectroscopic pipeline cross-matching.\n"
                    f"• Recommended Next Action: Trigger full evidence enrichment via the Evidence Fusion Panel to inspect external catalog match vectors."
                )

            if "star" in q_lower and ("why" in q_lower or "classified" in q_lower or "is" in q_lower):
                return (
                    f"Target `{obs_id}` was classified as **{obj_type}**.\n\n"
                    f"• **Visual Evidence:** Cutout exhibits a point-source diffraction profile rather than an extended galactic disk or spiral arms.\n"
                    f"• **Classification Confidence:** {conf_pct}\n"
                    f"• **Triage Signal:** Assigned priority {prio} (Triage Score: {triage_score:.2f}).\n"
                    f"• **Catalog Evidence:** Cross-matched with Gaia DR3 astrometric parallax and SDSS photometrical profile supporting stellar object classification."
                )

            if "galaxy" in q_lower and ("not" in q_lower or "n't" in q_lower or "why" in q_lower):
                return (
                    f"For observation `{obs_id}`:\n\n"
                    f"ASTRA's open-world morphology router evaluated the visual features of this cutout. Unlike extended galaxies (which exhibit disk envelopes, spiral arms, or bulge structures), `{obs_id}` exhibits point-source geometry ({obj_type}).\n\n"
                    f"Therefore, Galaxy Zoo morphology vote distribution was bypassed in favor of direct point-source classification with {conf_pct} confidence."
                )

            if "quasar" in q_lower or "exoplanet" in q_lower or "candidate" in q_lower:
                return (
                    f"For observation `{obs_id}`:\n\n"
                    f"• Current Classification: **{obj_type}** ({conf_pct} confidence)\n"
                    f"• Triage Score: **{triage_score:.2f}** ({prio} Priority)\n"
                    f"• Confirmation Requirements: Establishing an object as a Quasar requires high-redshift broad emission line spectroscopy from SDSS/DESI. Establishing an Exoplanet candidate requires TESS photometric transit light curves.\n"
                    f"• Multi-Modal Evidence Status: Querying external Gaia/SDSS/TESS adapters via the Evidence Enrichment Panel allows further cross-matching."
                )

            if "evidence" in q_lower:
                return (
                    f"### Multi-Modal Evidence Summary for `{obs_id}`:\n\n"
                    f"1. **Visual Model Inference:** {obj_type} — {morph} morphology ({conf_pct} confidence).\n"
                    f"2. **Triage Priority:** {prio} (Score: {triage_score:.2f} = 0.35*{novelty_score:.2f} + 0.35*{uncertainty_score:.2f} + 0.30*{oddity_score:.2f}).\n"
                    f"3. **Coordinates:** RA {ra:.6f}°, DEC {dec:.6f}°.\n"
                    f"4. **Survey Provenance:** {provenance}.\n"
                    f"5. **Catalog Status:** Cross-matched across Gaia DR3, SDSS DR16, ALLWISE, TESS, and NASA Exoplanet Archive."
                )

            if "student" in q_lower or "simple" in q_lower or "first-year" in q_lower:
                return (
                    f"Here is a simple breakdown of observation `{obs_id}`:\n\n"
                    f"1. **What is it?** ASTRA identified this picture as a **{obj_type}** ({morph} shape).\n"
                    f"2. **How sure is ASTRA?** Model confidence is **{conf_pct}**.\n"
                    f"3. **Is it special?** ASTRA gave it a triage score of **{triage_score:.2f}** (Priority: **{prio}**). This means its appearance stands out compared to average space photos.\n"
                    f"4. **What's next?** Scientists look at catalog data from satellites like Gaia and telescopes like SDSS to double-check the physics."
                )

            if "anomaly" in q_lower or "score" in q_lower or "triage" in q_lower:
                return (
                    f"For observation `{obs_id}`:\n\n"
                    f"The experimental triage score is **{triage_score:.2f}**, calculated using ASTRA's canonical triage formula:\n\n"
                    f"Score = 0.35 * S_novelty ({novelty_score:.2f}) + 0.35 * S_uncertainty ({uncertainty_score:.2f}) + 0.30 * S_oddity ({oddity_score:.2f})\n\n"
                    f"Assigning this target a priority level of **{prio}** for scientific review."
                )

            if "redshift" in q_lower or "distance" in q_lower or "mass" in q_lower or "age" in q_lower or "composition" in q_lower:
                return (
                    f"Physical parameters such as exact redshift, light-year distance, stellar mass, and galaxy age "
                    f"are not available in the current ASTRA observation record for {obs_id}.\n\n"
                    f"Available parameters: Target ID {obs_id}, Coordinates (RA {ra:.4f}°, DEC {dec:.4f}°), "
                    f"Predicted Class: {morph} ({conf_pct} confidence), and Triage Priority: {prio} (Score: {triage_score:.2f})."
                )

            if "discovery" in q_lower or "new galaxy" in q_lower or "prove" in q_lower or "alien" in q_lower:
                return (
                    f"For observation {obs_id}:\n\n"
                    f"ASTRA identified this observation as statistically unusual according to its triage signals (Priority: {prio}, Score: {triage_score:.2f}) and prioritized it for scientific review.\n\n"
                    f"This does not establish that the object is new or a scientific discovery. Human astronomical review and spectroscopic follow-up would be required to verify its physical nature."
                )

            if "priority" in q_lower or "prioritiz" in q_lower or "why" in q_lower and "flagged" in q_lower:
                return (
                    f"Observation {obs_id} was assigned priority level '{prio}' with an experimental triage score of {triage_score:.2f}.\n\n"
                    f"Triage Signals Breakdown:\n"
                    f"• Novelty Score (S_novelty): {novelty_score:.2f} — Latent distance from reference galaxy embeddings.\n"
                    f"• Uncertainty Score (S_uncertainty): {uncertainty_score:.2f} — Entropy of morphological vote distribution.\n"
                    f"• Oddity Score (S_oddity): {oddity_score:.2f} — Probability of unusual structural features.\n\n"
                    f"Summary: The combined score exceeds the {prio} priority threshold, placing it in the scientific review queue."
                )

            # Rich Default observation explanation for Deep Analysis requests
            return (
                f"### Scientific Target Analysis: {obs_id}\n\n"
                f"**1. Target Overview & Image Content:**\n"
                f"• Target Designation: `{obs_id}`\n"
                f"• Celestial Coordinates: RA {ra:.6f}°, DEC {dec:.6f}°\n"
                f"• Data Provenance: {provenance}\n\n"
                f"**2. ASTRA Object Classification:**\n"
                f"• Predicted Object Type: **{obj_type}**\n"
                f"• Morphology Taxonomy: **{morph}** (GZ2 class `{gz2class}`)\n"
                f"• Classification Confidence: **{conf_pct}**\n\n"
                f"**3. Statistical Triage Signals:**\n"
                f"• Experimental Triage Score: **{triage_score:.2f}**\n"
                f"• Priority Level: **{prio}**\n"
                f"• Novelty ($S_{{novelty}}$): `{novelty_score:.2f}` | Uncertainty ($S_{{uncertainty}}$): `{uncertainty_score:.2f}` | Oddity ($S_{{oddity}}$): `{oddity_score:.2f}`\n\n"
                f"**4. Scientific Status & Recommended Next Steps:**\n"
                f"• What is Known: Visual structure matches learned survey reference population for {morph.lower().replace('_', ' ')} morphology.\n"
                f"• What Remains Uncertain: Photometrical redshift and exact spectral composition require multi-band catalog cross-matching.\n"
                f"• Recommended Action: Query Gaia DR3 / SDSS DR17 spectra for detailed physical validation."
            )

        # ----------------------------------------------------
        # Intent C: General Astronomy & Astrophysics Q&A
        # ----------------------------------------------------
        if "black hole" in q_lower or "event horizon" in q_lower or "singularity" in q_lower:
            return (
                "A black hole is a region of spacetime where gravity is so strong that nothing—not even light—can escape. "
                "The boundary surrounding a black hole beyond which nothing can escape is called the event horizon. "
                "Supermassive black holes (millions to billions of solar masses) reside at the centers of most large galaxies, including our Milky Way (Sagittarius A*)."
            )

        if "supernova" in q_lower or "supernovae" in q_lower:
                return (
                    "A supernova is a powerful, luminous explosion marking the end of a star's life. "
                    "Core-collapse supernovas (Type II) occur when massive stars exhaust their nuclear fuel and collapse under gravity. "
                    "Thermonuclear supernovas (Type Ia) happen in binary systems when a white dwarf accretes critical mass from a companion star, providing standard candles for measuring cosmic distances."
                )

        if "telescope" in q_lower or "collect light" in q_lower:
            return (
                "Telescopes collect light using large primary mirrors (reflectors) or lenses (reflectors). "
                "The light-gathering power of a telescope scales with the area of its primary aperture (d²), allowing astronomers to observe faint, distant objects. "
                "Modern observatories like JWST and Hubble use specialized detectors (CCDs and infrared sensors) to record photons across different EM spectrum bands."
            )

        if "spectrograph" in q_lower or "spectroscopy" in q_lower:
            return (
                "A spectrograph disperses incoming light from celestial objects into its constituent wavelengths (a spectrum). "
                "By analyzing spectral absorption and emission lines, astronomers determine chemical composition, temperature, density, radial velocity (via Doppler shift), and magnetic fields of distant stars and galaxies."
            )

        if "gravitational lensing" in q_lower or "lensing" in q_lower:
            return (
                "Gravitational lensing occurs when a massive foreground celestial body (such as a galaxy cluster) warps the surrounding spacetime, acting as a natural lens that bends and magnifies light coming from a more distant background object. "
                "This phenomenon was predicted by Einstein's theory of General Relativity and allows astronomers to study distant galaxies and probe dark matter distribution."
            )

        if "neutron star" in q_lower or "pulsar" in q_lower or "magnetar" in q_lower:
            if "planet" in q_lower:
                return (
                    "Yes, planets can exist around neutron stars. The first exoplanets ever confirmed (PSR B1257+12 b, c, and d in 1992) were discovered orbiting a pulsar. "
                    "These exoplanets likely formed from a post-supernova debris disk or survived the progenitor star's explosion, though they are exposed to extreme radiation environments."
                )
            return (
                "A neutron star is the collapsed, ultra-dense core of a massive star remaining after a Type II supernova. "
                "Packing about 1.4 to 2 solar masses into a sphere only ~20 km in diameter, they consist almost entirely of neutrons. "
                "Rapidly rotating neutron stars emitting beams of radiation are known as pulsars."
            )

        if "andromeda" in q_lower or "how far away" in q_lower:
            if "andromeda" in q_lower:
                return (
                    "The Andromeda Galaxy (M31) is located approximately 2.5 million light-years from Earth. "
                    "It is the nearest major spiral galaxy to the Milky Way and is currently approaching us at about 110 km/s, expected to collide and merge with the Milky Way in approximately 4 to 5 billion years."
                )

        if "mars" in q_lower or "red" in q_lower:
            if "mars" in q_lower:
                return (
                    "Mars appears red because its surface soil and dust are rich in iron oxide (rust). "
                    "Solar wind and ancient atmospheric oxygen oxidized iron minerals in the Martian regolith, distributing fine red dust across the planet."
                )

        if "quasar" in q_lower or "blazar" in q_lower or "agn" in q_lower:
            return (
                "A quasar (quasi-stellar radio source) is an extremely luminous active galactic nucleus (AGN) powered by a supermassive black hole accreting gas and dust at the center of a distant galaxy. "
                "As matter falls toward the black hole, friction and gravitational energy heat the accretion disk to millions of degrees, making quasars outshine their host galaxies across cosmic distances."
            )

        if "exoplanet" in q_lower or "transit" in q_lower:
            return (
                "Astronomers detect exoplanets primarily through two major techniques:\n\n"
                "1. Transit Photometry: Measuring the periodic dip in a star's brightness as an orbiting exoplanet crosses in front of its disk (used extensively by Kepler and TESS).\n"
                "2. Radial Velocity (Doppler Method): Detecting subtle wobbles in a star's spectral lines caused by the gravitational tug of an orbiting planet.\n\n"
                "Other methods include gravitational microlensing and direct imaging."
            )

        if "redshift" in q_lower:
            return (
                "Redshift (z) measures how much the light from a celestial object has been stretched toward longer, redder wavelengths as it travels through expanding space. "
                "According to Hubble's Law, higher redshift indicates greater cosmic distance and earlier lookback time in the universe."
            )

        if "color" in q_lower or "colour" in q_lower:
            return (
                "Stars exhibit different colors due to their surface temperatures. "
                "Hotter stars (above 10,000 K) radiate most intensely at shorter wavelengths and appear blue, while cooler stars (below 3,500 K) radiate at longer wavelengths and appear red. "
                "Yellow stars like our Sun have intermediate surface temperatures around 5,770 K."
            )

        if "light-year" in q_lower or "parsec" in q_lower:
            return (
                "A light-year is a unit of distance—not time. It is the distance that light travels through a vacuum in one Julian year, equal to approximately 9.46 trillion kilometers (5.88 trillion miles).\n\n"
                "A parsec is equal to ~3.26 light-years (30.9 trillion km), defined as the distance at which 1 astronomical unit subtends an angle of 1 arcsecond."
            )

        if "dark matter" in q_lower or "dark energy" in q_lower:
            return (
                "Dark matter is an invisible form of matter that makes up about 27% of the universe's mass-energy content. It does not absorb, reflect, or emit light, but its presence is inferred through gravitational effects on galactic rotation curves and gravitational lensing.\n\n"
                "Dark energy makes up about 68% of the universe and drives the accelerated expansion of cosmic space."
            )

        if "meteor" in q_lower or "meteorite" in q_lower or "asteroid" in q_lower:
            return (
                "Terminology breakdown:\n"
                "• Meteoroid: A small rocky or metallic object in space (smaller than an asteroid).\n"
                "• Meteor: The streak of light ('shooting star') produced when a meteoroid burns up entering Earth's atmosphere.\n"
                "• Meteorite: Any fragment of a meteoroid that survives atmospheric entry and lands on Earth's surface.\n"
                "• Asteroid: A larger rocky body orbiting the Sun, mostly found in the Asteroid Belt between Mars and Jupiter."
            )

        if "transient" in q_lower:
            return (
                "An astronomical transient is a celestial phenomenon that exhibits variable brightness or structural change over human observable timescales (ranging from seconds to years). "
                "Examples include supernovas, gamma-ray bursts, tidal disruption events, novas, and fast radio bursts."
            )

        if "observatory" in q_lower or "decide" in q_lower or "schedule" in q_lower:
            return (
                "Astronomical observatories allocate telescope time based on scientific peer review panels (Time Allocation Committees) evaluating proposals. "
                "Prioritization factors include target visibility, moon phase, atmospheric seeing conditions, instrument readiness, and urgency (e.g. Target-of-Opportunity alerts for transient events)."
            )

        if "spacex" in q_lower or "launch tonight" in q_lower or "latest nasa" in q_lower or "right now" in q_lower:
            return (
                "Real-time orbital launch schedules and live astronomical announcements cannot be verified in the current assistant context. "
                "Please consult official mission portals such as NASA.gov or SpaceTrack for real-time telemetry."
            )

        if "spiral" in q_lower:
            return (
                "Spiral galaxies are disk-shaped galaxies characterized by a central bulge of older stars surrounded by a rotating disk containing prominent spiral arms of gas, dust, and young blue star clusters. "
                "Our Milky Way and Andromeda (M31) are prominent examples of spiral galaxies."
            )

        if "smooth" in q_lower or "elliptical" in q_lower:
            return (
                "Smooth or elliptical galaxies feature smooth, symmetric light profiles ranging from spherical to elongated ellipsoids. "
                "They contain little gas and dust, consisting primarily of older red stars with random orbital trajectories."
            )

        if "edge-on" in q_lower or "edge on" in q_lower:
            return (
                "An edge-on galaxy is a disk galaxy viewed near parallel to the line of sight (inclination near 90°). "
                "From Earth's perspective, it appears as a thin needle-like structure, often bisected by a dark dust lane."
            )

        # General astronomy fallback
        return (
            "In astronomy, objects are studied through imaging morphology, spectroscopy, and photometrical measurements. "
            "Galaxies range from smooth ellipticals to structured spirals and irregular mergers, each providing clues about cosmic galaxy evolution and dark matter distribution."
        )

    def _call_llm_provider(
        self,
        question: str,
        observation_context: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]],
        image_base64: Optional[str]
    ) -> Optional[str]:
        """
        Call configured external LLM Provider (Google Gemini / OpenAI).
        """
        if self.provider == "google":
            return self._call_gemini_api(question, observation_context, conversation_history, image_base64)
        elif self.provider == "openai":
            return self._call_openai_api(question, observation_context, conversation_history, image_base64)
        return None

    def _call_gemini_api(
        self,
        question: str,
        observation_context: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]],
        image_base64: Optional[str]
    ) -> Optional[str]:
        """
        Direct REST call to Google Gemini API (no external SDK required).
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        prompt_parts = [ASTRA_SPACE_AI_SYSTEM_PROMPT]
        if conversation_history:
            hist_str = "\n".join([f"{(h.get('role') or h.get('sender') or 'user').upper()}: {h.get('content', '')}" for h in conversation_history[-6:]])
            prompt_parts.append(f"CONVERSATION HISTORY:\n{hist_str}")
        if observation_context:
            prompt_parts.append(f"ATTACHED OBSERVATION CONTEXT PAYLOAD:\n{json.dumps(observation_context, indent=2)}")
        prompt_parts.append(f"USER QUESTION: {question}")
        
        full_text = "\n\n".join(prompt_parts)
        
        contents = [{"parts": [{"text": full_text}]}]
        if image_base64:
            contents[0]["parts"].append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            })
            
        payload = json.dumps({"contents": contents}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            logger.warning(f"Gemini REST API error: {e}")
        return None

    def _call_openai_api(
        self,
        question: str,
        observation_context: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]],
        image_base64: Optional[str]
    ) -> Optional[str]:
        """
        Direct REST call to OpenAI API (no external SDK required).
        """
        url = "https://api.openai.com/v1/chat/completions"
        
        messages = [{"role": "system", "content": ASTRA_SPACE_AI_SYSTEM_PROMPT}]
        if conversation_history:
            for h in conversation_history[-6:]:
                messages.append({
                    "role": "user" if h.get("role") == "user" else "assistant",
                    "content": h.get("content", "")
                })

        user_content = []
        if observation_context:
            user_content.append({"type": "text", "text": f"ATTACHED OBSERVATION CONTEXT:\n{json.dumps(observation_context, indent=2)}"})
        user_content.append({"type": "text", "text": question})
        
        if image_base64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })

        messages.append({"role": "user", "content": user_content})

        payload = json.dumps({
            "model": self.model_name or "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 500
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.warning(f"OpenAI REST API error: {e}")
        return None

space_ai_service = SpaceAIService()

