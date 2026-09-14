import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("astra.space_ai_router")

INTENT_GREETING = "GREETING"
INTENT_OFF_TOPIC = "OFF_TOPIC"
INTENT_ASTRONOMY_GENERAL = "ASTRONOMY_GENERAL"
INTENT_ASTRA_PRODUCT = "ASTRA_PRODUCT"
INTENT_OBSERVATION_ANALYSIS = "OBSERVATION_ANALYSIS"
INTENT_UNSUPPORTED = "UNSUPPORTED"

GREETING_PATTERNS = [
    r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening|howdy)\b",
    r"^(who are you|what can you do|what are your capabilities|help|introduce yourself)\b"
]

OFF_TOPIC_KEYWORDS = [
    "fifa", "football", "soccer", "cricket", "basketball", "nba", "baseball", "tennis",
    "programming", "coding", "script",
    "iphone", "android", "samsung", "recipe", "pizza", "burger",
    "joke", "funny", "crypto", "bitcoin", "stock market", "finance", "medical", "doctor",
    "president", "prime minister", "government", "politics", "election", "movie", "song", "weather"
]

# Explicit terms referring specifically to the currently active observation payload
OBSERVATION_EXPLICIT_PATTERNS = [
    r"\b(this|active|selected|current)\s+(observation|target|galaxy|image|object|result|score|anomaly)\b",
    r"\bwhy\s+(was|is)\s+(this|the)\s+(observation|target|galaxy|image)?\s*(prioritized|flagged|high|critical|medium|low)\b",
    r"\b(explain|interpret)\s+(this|the)\s+(result|observation|target|image|dossier|score)\b",
    r"\bwhat\s+(does|did)\s+astra\s+(think|predict)\s+(about|for)\s+this\b",
    r"\bwhy\s+did\s+the\s+model\s+classify\s+this\b",
    r"\bis\s+this\s+(a\s+)?(new|unusual|exotic|anomalous)\s+(galaxy|object|star)\b",
    r"\bdoes\s+this\s+prove\b",
    r"\bcoordinates\s+of\s+this\b",
    r"\bwhat\s+does\s+the\s+(novelty|uncertainty|oddity)\s+score\s+mean\s+for\s+this\b",
    r"\bcould\s+this\s+observation\s+be\b"
]

# Terms referring specifically to ASTRA product system, pipeline, gates, and triage methodology
ASTRA_PRODUCT_PATTERNS = [
    r"\b(what\s+does\s+astra\s+do|how\s+does\s+astra\s+work|astra\s+pipeline|astra\s+architecture)\b",
    r"\b(semantic\s+gate|semantic\s+pre-gate|domain\s+gate|domain\s+validation|multiple\s+validation)\b",
    r"\b(triage\s+engine|triage\s+score|triage\s+system|triage\s+pipeline|triage\s+heuristic|triage\s+workflow)\b",
    r"\b(novelty\s+score|uncertainty\s+score|oddity\s+score|s_novelty|s_uncertainty|s_oddity)\b",
    r"\b(galaxy\s+zoo|gz2|sdss|sdss\s+dr7|4-class|taxonomy)\b",
    r"\b(why\s+does\s+astra\s+use|why\s+are\s+there\s+multiple\s+validation|why\s+doesn't\s+astra\s+call|why\s+can't\s+astra\s+analyze)\b",
    r"\b(screenshot|non-astronomical|rejected|domain\s+compatibility)\b"
]

# Broad astronomy, astrophysics, solar system, cosmology, observational terms & question structures
ASTRONOMY_KEYWORDS = [
    # Celestial objects
    "galaxy", "galaxies", "spiral", "smooth", "elliptical", "edge-on", "disk", "bulge",
    "star", "stars", "sun", "planet", "planets", "moon", "moons", "asteroid", "asteroids",
    "comet", "comets", "meteor", "meteorite", "meteoroid", "black hole", "event horizon",
    "singularity", "neutron star", "pulsar", "magnetar", "quasar", "blazar", "agn",
    "supernova", "supernovae", "nebula", "nebulae", "exoplanet", "exoplanets", "dwarf",
    # Astrophysics & Cosmology
    "redshift", "hubble", "jwst", "sdss", "dark matter", "dark energy", "cosmology",
    "big bang", "gravitational lensing", "gravitational waves", "lensing", "spacetime",
    "cosmic", "interstellar", "intergalactic", "stellar evolution", "accretion",
    # Observational instruments & concepts
    "telescope", "telescopes", "observatory", "observatories", "spectrograph",
    "spectroscopy", "photometry", "spectrum", "spectra", "wavelength", "light-year",
    "lightyear", "parsec", "celestial", "transit", "radial velocity", "astronomical",
    "transient", "instrumentation"
]

ASTRONOMY_QUESTION_PATTERNS = [
    r"\bwhat\s+(causes|is|are)\s+a?\s*(supernova|black\s+hole|quasar|galaxy|exoplanet|light-year|parsec|redshift|event\s+horizon|spectrograph|transient|dark\s+matter)\b",
    r"\bwhy\s+do\s+(stars|galaxies|planets)\b",
    r"\bwhy\s+does\s+(mars|the\s+sun|a\s+star)\b",
    r"\bhow\s+(do|does)\s+(astronomers|telescopes|spectrographs|a\s+telescope)\b",
    r"\bcould\s+a\s+planet\s+exist\b",
    r"\bhow\s+far\s+(away\s+is|to)\b",
    r"\bhow\s+are\s+galaxies\s+classified\b",
    r"\bdifference\s+between\s+(a\s+)?(meteor|star|galaxy|planet)\b"
]

class SpaceAIRouter:
    """
    Semantic Intent Router for ASTRA Space Help AI.
    Classifies user queries into distinct intent classes BEFORE observation context is applied.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, provider: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or "gemini-1.5-flash"
        self.provider = (provider or "").lower()

    def classify_intent(self, question: str) -> Dict[str, Any]:
        """
        Classify incoming user question into one of:
        GREETING, OFF_TOPIC, ASTRONOMY_GENERAL, ASTRA_PRODUCT, OBSERVATION_ANALYSIS, UNSUPPORTED.
        """
        q_clean = question.strip()
        q_lower = q_clean.lower()

        # 1. Greetings
        for pat in GREETING_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_GREETING,
                    "needs_observation_context": False,
                    "reason": "Matched greeting pattern"
                }

        # 2. Check Explicit Observation Questions FIRST if user uses observation-specific phrasing
        for pat in OBSERVATION_EXPLICIT_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_OBSERVATION_ANALYSIS,
                    "needs_observation_context": True,
                    "reason": f"Matched explicit observation pattern: {pat}"
                }

        # 3. Check ASTRA Product Questions
        for pat in ASTRA_PRODUCT_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_ASTRA_PRODUCT,
                    "needs_observation_context": False,
                    "reason": f"Matched ASTRA product pattern: {pat}"
                }

        # 4. Check General Astronomy Questions & Patterns
        for pat in ASTRONOMY_QUESTION_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_ASTRONOMY_GENERAL,
                    "needs_observation_context": False,
                    "reason": f"Matched astronomy question pattern: {pat}"
                }

        if any(kw in q_lower for kw in ASTRONOMY_KEYWORDS):
            return {
                "intent": INTENT_ASTRONOMY_GENERAL,
                "needs_observation_context": False,
                "reason": "Matched general astronomy keyword"
            }

        # 5. Off-Topic Filtering
        for kw in OFF_TOPIC_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", q_lower):
                return {
                    "intent": INTENT_OFF_TOPIC,
                    "needs_observation_context": False,
                    "reason": f"Matched off-topic keyword '{kw}'"
                }

        # 6. Fallback Off-Topic redirect if question matches none of above
        return {
            "intent": INTENT_OFF_TOPIC,
            "needs_observation_context": False,
            "reason": "Query contains no recognized space, astronomy, or ASTRA intent"
        }

