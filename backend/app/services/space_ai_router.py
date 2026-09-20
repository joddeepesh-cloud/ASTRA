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
    "fifa", "football", "soccer", "cricket", "basketball", "nba", "baseball", "tennis", "sports", "match",
    "programming", "coding", "script", "python", "java", "c++", "javascript", "react", "html", "css",
    "iphone", "android", "samsung", "recipe", "pizza", "burger", "cook", "cooking", "food",
    "resume", "job", "career", "interview", "salary",
    "joke", "funny", "crypto", "bitcoin", "stock market", "finance", "medical", "doctor",
    "president", "prime minister", "government", "politics", "election", "movie", "song", "weather"
]

OFF_TOPIC_PATTERNS = [
    r"^(write|create|build|generate|make)\s+(me\s+)?(a\s+)?(python|code|program|script|app|software|recipe|poem|essay|resume|cover letter)\b",
    r"\bwho\s+won\s+the\s+(football|soccer|cricket|nba|match|game)\b",
    r"\bhow\s+to\s+(cook|bake|make)\b",
    r"\bhelp\s+(me\s+)?with\s+(my\s+)?(resume|cv|job|interview)\b"
]

# Explicit terms referring specifically to the currently active observation payload
OBSERVATION_EXPLICIT_PATTERNS = [
    r"^(more\s+details|tell\s+me\s+more|why\s*\?|what\s+else(\s+can\s+you\s+tell\s+me)?\??|how\s+sure(\s+are\s+you)?\??|and\s+the\s+score\??|what\s+about\s+that\??|what\s+looks\s+unusual\??|what\s+should\s+we\s+investigate\s+next\??)$",
    r"\b(this|it|active|selected|current)\s+(observation|target|galaxy|star|quasar|nebula|exoplanet|image|object|result|score|anomaly)\b",
    r"\bwhy\s+(was|is|isn't)\s+(this|it)\s+(a|an)?\s*(prioritized|flagged|high|critical|medium|low|star|galaxy|quasar|nebula|exoplanet)?\b",
    r"\bwhy\s+(is|was|isn't)\s+(this|it)\b",
    r"\b(explain|interpret|summarize|tell\s+me\s+about)\s+(this|it)\s*(result|observation|target|image|dossier|score|evidence)?\b",
    r"\bwhat\s+(is|about)\s+(this|it)\b",
    r"\bwhat\s+(does|did)\s+astra\s+(think|predict|find)\s+(about|for)\s+(this|it)\b",
    r"\bwhy\s+did\s+the\s+model\s+classify\s+(this|it)\b",
    r"\b(is|was)\s+(this|it)\s+(a\s+)?(new|unusual|exotic|anomalous|star|galaxy|quasar|nebula|exoplanet)\b",
    r"\bdoes\s+(this|it)\s+prove\b",
    r"\bcoordinates\s+of\s+(this|it)\b",
    r"\bwhat\s+does\s+the\s+(novelty|uncertainty|oddity|triage|anomaly)\s+score\s+mean\s+(for|in)\s+(this|it)\b",
    r"\bcould\s+(this|it)\s+(observation\s+)?be\s+(a|an)?\s*(star|galaxy|quasar|nebula|exoplanet|black hole)?\b",
    r"\b(provide|give|generate|show)\s+(a\s+)?(detailed\s+)?(scientific\s+)?(explanation|analysis)\s+(of|for)\s+(observation|target|this|it)\b",
    r"\bobservation\s+(lib-|live-|obs-)\b",
    r"\b(lib-|live-|obs-)[a-z0-9-_]+\b",
    r"\bwhat\s+evidence\s+(do\s+we\s+have|is\s+there|would\s+confirm|does\s+the\s+gaia\s+evidence\s+mean)\b"
]

# Terms referring specifically to ASTRA product system, pipeline, gates, and triage methodology
ASTRA_PRODUCT_PATTERNS = [
    r"\b(what\s+does\s+astra\s+do|how\s+does\s+astra\s+work|astra\s+pipeline|astra\s+architecture)\b",
    r"\b(semantic\s+gate|semantic\s+pre-gate|domain\s+gate|domain\s+validation|multiple\s+validation)\b",
    r"\b(triage\s+engine|triage\s+score|triage\s+system|triage\s+pipeline|triage\s+heuristic|triage\s+workflow)\b",
    r"\b(novelty\s+score|uncertainty\s+score|oddity\s+score|s_novelty|s_uncertainty|s_oddity)\b",
    r"\b(galaxy\s+zoo|gz2|sdss|sdss\s+dr7|4-class|taxonomy)\b",
    r"\b(why\s+does\s+astra\s+use|why\s+are\s+there\s+multiple\s+validation|why\s+doesn't\s+astra\s+call|why\s+can't\s+astra\s+analyze)\b",
    r"\b(screenshot|non-astronomical|rejected|domain\s+compatibility)\b",
    r"\b(what\s+(is|are|do\s+we\s+mean\s+by)\s+(an?\s*)?anomaly|anomalies|anomalous|outlier|ood|divergence)\b",
    r"\b(why\s+is\s+this|why\s+was\s+this|what\s+makes\s+something)\s+(anomalous|flagged|prioritized)\b",
    r"\b(explain|definition\s+of)\s+anomaly\b",
    r"\bhow\s+does\s+astra\s+detect\s+unusual\s+observations\b"
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
    "transient", "instrumentation", "tess", "light curve", "lightcurve"
]

ASTRONOMY_QUESTION_PATTERNS = [
    r"\bwhat\s+(is|are|causes)\s+a?\s*(galaxy|spiral\s+galaxy|quasar|star|nebula|black\s+hole|neutron\s+star|supernova|gravitational\s+lensing|transit|light\s+curve|galaxy\s+cluster|dark\s+matter|dark\s+energy)\b",
    r"\bhow\s+do\s+astronomers\s+detect\s+exoplanets\b",
    r"\bhow\s+does\s+tess\s+work\b",
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

    def classify_intent(self, question: str, has_observation_context: bool = False) -> Dict[str, Any]:
        """
        Classify incoming user question into one of:
        GREETING, OFF_TOPIC, ASTRONOMY_GENERAL, ASTRA_PRODUCT, OBSERVATION_ANALYSIS, UNSUPPORTED.
        """
        q_clean = question.strip()
        q_lower = q_clean.lower()

        # 1. Greetings (explicit standalone greeting like "hi", "hello")
        for pat in GREETING_PATTERNS:
            if re.search(pat, q_lower) and len(q_clean.split()) <= 4:
                return {
                    "intent": INTENT_GREETING,
                    "needs_observation_context": False,
                    "reason": "Matched greeting pattern"
                }

        # 2. Check explicit OFF-TOPIC keywords and patterns (e.g. fifa, recipe, stocks, programming, etc.)
        for kw in OFF_TOPIC_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", q_lower):
                return {
                    "intent": INTENT_OFF_TOPIC,
                    "needs_observation_context": False,
                    "reason": f"Matched off-topic keyword '{kw}'"
                }

        for pat in OFF_TOPIC_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_OFF_TOPIC,
                    "needs_observation_context": False,
                    "reason": f"Matched off-topic pattern '{pat}'"
                }

        # 3. Check ASTRA Product Questions FIRST (e.g. triage score, domain gate, discovery caution)
        for pat in ASTRA_PRODUCT_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_ASTRA_PRODUCT,
                    "needs_observation_context": False,
                    "reason": f"Matched ASTRA product pattern: {pat}"
                }

        # 4. Check Explicit Observation Questions if user uses observation-specific phrasing
        for pat in OBSERVATION_EXPLICIT_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "intent": INTENT_OBSERVATION_ANALYSIS,
                    "needs_observation_context": True,
                    "reason": f"Matched explicit observation pattern: {pat}"
                }

        # 5. Check explicit standalone general astronomy questions (e.g. "What is a black hole?", "Why does Mars look red?")
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

        # 6. Contextual Follow-Up Rule: If active observation context exists, classify short/ambiguous/elliptical follow-ups as OBSERVATION_ANALYSIS
        if has_observation_context:
            return {
                "intent": INTENT_OBSERVATION_ANALYSIS,
                "needs_observation_context": True,
                "reason": "Contextual follow-up with active observation payload"
            }

        # 7. Fallback Off-Topic redirect if question matches none of above and no context exists
        return {
            "intent": INTENT_OFF_TOPIC,
            "needs_observation_context": False,
            "reason": "Query contains no recognized space, astronomy, or ASTRA intent"
        }

