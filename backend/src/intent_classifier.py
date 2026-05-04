"""
Intent Classifier Module
Classifies user intent from natural language input with weighted keyword scoring.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class IntentRequirements:
    cpu_class: str = "Mid"
    gpu_class: str = "Mid"
    priority: str = "Balanced"
    min_ram: int = 16
    min_fps: Optional[int] = None
    resolution: str = "1080p"
    needs_nvenc: bool = False


# ---------------------------------------------------------------------------
# Intent definitions
# Each keyword can optionally carry a weight (default = 1).
# Format: "keyword" -> weight  OR just list plain strings for weight=1.
# ---------------------------------------------------------------------------
INTENT_PROFILES: dict[str, dict] = {
    "FPS Gaming": {
        "keywords": {
            "valorant": 3, "cs2": 3, "csgo": 3, "apex": 2, "warzone": 2,
            "fortnite": 2, "call of duty": 2, "battlefield": 2,
            "competitive": 2, "fps": 2, "high fps": 3, "144hz": 2, "240hz": 3,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="Mid",
            priority="CPU", min_fps=144,
        ),
    },
    "Esports": {
        "keywords": {
            "esports": 3, "tournament": 3, "competitive gaming": 3,
            "low settings": 2, "360hz": 3, "240hz": 2,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="Mid",
            priority="CPU", min_fps=240,
        ),
    },
    "AAA Gaming": {
        "keywords": {
            "cyberpunk": 3, "rdr2": 3, "red dead": 3, "gta": 2,
            "witcher": 2, "ray tracing": 3, "rtx": 2, "ultra settings": 3,
            "4k gaming": 3, "aaa": 2, "open world": 2,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="High",
            priority="GPU", resolution="1440p",
        ),
    },
    "Gaming": {
        "keywords": {
            "gaming": 2, "game": 1, "play games": 2, "gamer": 2,
            "steam": 1, "xbox": 1, "playstation": 1,
        },
        "requirements": IntentRequirements(
            cpu_class="Mid", gpu_class="Mid",
            priority="GPU", min_fps=60,
        ),
    },
    "CAD/3D Modeling": {
        "keywords": {
            "autocad": 3, "solidworks": 3, "blender": 3, "3d modeling": 3,
            "maya": 3, "fusion 360": 3, "cad": 2, "3d rendering": 3,
            "simulation": 2, "ansys": 3, "rhino": 2,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="High",
            priority="CPU", min_ram=32,
        ),
    },
    "Video Editing": {
        "keywords": {
            "premiere": 3, "after effects": 3, "davinci resolve": 3,
            "final cut": 3, "video editing": 3, "vegas pro": 3,
            "color grading": 2, "4k video": 2, "video production": 2,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="High",
            priority="Balanced", min_ram=32,
        ),
    },
    "Streaming": {
        "keywords": {
            "streaming": 3, "twitch": 3, "youtube live": 3, "obs": 2,
            "broadcast": 2, "live stream": 3, "content creator": 2,
        },
        "requirements": IntentRequirements(
            cpu_class="High", gpu_class="High",
            priority="Balanced", needs_nvenc=True,
        ),
    },
    "Programming": {
        "keywords": {
            "programming": 2, "coding": 2, "development": 2, "developer": 2,
            "vscode": 2, "docker": 2, "virtual machine": 2, "vm": 2,
            "compile": 2, "machine learning": 3, "deep learning": 3,
            "data science": 3, "pytorch": 3, "tensorflow": 3,
        },
        "requirements": IntentRequirements(
            cpu_class="Mid", gpu_class="Entry",
            priority="CPU", min_ram=16,
        ),
    },
    "Office/Productivity": {
        "keywords": {
            "office": 1, "work": 1, "productivity": 1, "excel": 1,
            "browsing": 1, "everyday": 1, "student": 1, "study": 1,
            "basic": 1, "general use": 1, "word": 1,
        },
        "requirements": IntentRequirements(
            cpu_class="Entry", gpu_class="Entry",
            priority="Value",
        ),
    },
}

PRIORITY_COMPONENT_MAP = {
    "CPU": ["CPU", "RAM"],
    "GPU": ["GPU", "CPU"],
    "Value": ["Value", "Efficiency"],
    "Balanced": ["CPU", "GPU", "RAM"],
}


class IntentClassifier:
    """Classifies user intent for PC build recommendations using weighted scoring."""

    def __init__(self):
        self.profiles = INTENT_PROFILES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, message: str) -> str:
        """Return the best-matching intent label for a free-text message."""
        if not message or len(message.strip()) < 2:
            return "Office/Productivity"

        message = message.lower().strip()
        scores: dict[str, float] = {}

        for intent, profile in self.profiles.items():
            score = self._score_message(message, profile["keywords"])
            if score > 0:
                scores[intent] = score

        if not scores:
            # Heuristic: if the message contains a number, assume gaming
            if re.search(r"\d{4,}", message):   # budget-like number
                logger.debug("No intent matched; defaulting to Gaming (budget hint)")
                return "Gaming"
            logger.debug("No intent matched; defaulting to Office/Productivity")
            return "Office/Productivity"

        best = max(scores, key=scores.__getitem__)
        logger.debug("Intent scores: %s → selected: %s", scores, best)
        return best

    def classify_intent(self, message: str) -> tuple[str, list[str]]:
        """Return (intent, priority_components) for a message."""
        intent = self.classify(message)
        requirements = self.get_requirements(intent)
        priority_components = PRIORITY_COMPONENT_MAP.get(
            requirements.priority, ["CPU", "GPU", "RAM"]
        )
        return intent, priority_components

    def get_requirements(self, intent: str) -> IntentRequirements:
        """Return IntentRequirements dataclass for a given intent label."""
        profile = self.profiles.get(intent, self.profiles["Office/Productivity"])
        return profile["requirements"]

    def get_all_intents(self) -> list[str]:
        return list(self.profiles.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_message(message: str, keywords: dict[str, float]) -> float:
        score = 0.0
        for kw, weight in keywords.items():
            if kw in message:
                score += weight
        return score