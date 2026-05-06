"""
AI Fallback Module
Provides AI-powered recommendations when the local dataset is insufficient.
Supports Google Gemini and OpenAI with a clean provider abstraction.
"""

import json
import logging
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ── Hardcoded fallback builds ────────────────────────────────────────────────

FALLBACK_BUILDS = {
    "high": {
        "components": {
            "cpu":         {"Name": "Intel Core i9-14900K",       "Price": 55000, "Socket": "LGA1700", "Core Count": 24, "TDP": 125},
            "gpu":         {"Name": "NVIDIA RTX 4080 Super",       "Price": 95000, "VRAM": 16,          "TDP": 320},
            "motherboard": {"Name": "ASUS ROG Z790 Maximus",       "Price": 45000, "Socket/CPU": "LGA1700", "Memory Type": "DDR5", "Form Factor": "ATX"},
            "ram":         {"Name": "Corsair Dominator 32GB DDR5", "Price": 16000, "Type": "DDR5",      "Size": "32GB"},
            "storage":     {"Name": "Samsung 990 Pro 2TB NVMe",    "Price": 15000, "Type": "NVMe",      "Capacity": "2TB"},
        },
        "total_price": 226000,
        "psu_wattage": "1000W",
        "cabinet_type": "Full Tower",
    },
    "mid": {
        "components": {
            "cpu":         {"Name": "AMD Ryzen 5 7600X",           "Price": 22000, "Socket": "AM5",     "Core Count": 6,  "TDP": 105},
            "gpu":         {"Name": "NVIDIA RTX 4060 Ti",          "Price": 35000, "VRAM": 8,           "TDP": 160},
            "motherboard": {"Name": "MSI B650 Tomahawk",           "Price": 18000, "Socket/CPU": "AM5", "Memory Type": "DDR5", "Form Factor": "ATX"},
            "ram":         {"Name": "G.Skill Ripjaws 16GB DDR5",   "Price":  7500, "Type": "DDR5",      "Size": "16GB"},
            "storage":     {"Name": "WD Black SN770 1TB NVMe",     "Price":  6500, "Type": "NVMe",      "Capacity": "1TB"},
        },
        "total_price": 89000,
        "psu_wattage": "750W",
        "cabinet_type": "Mid Tower",
    },
    "budget": {
        "components": {
            "cpu":         {"Name": "Intel Core i3-12100F",        "Price":  8500, "Socket": "LGA1700", "Core Count": 4,  "TDP": 58},
            "gpu":         {"Name": "AMD Radeon RX 6600",          "Price": 22000, "VRAM": 8,           "TDP": 132},
            "motherboard": {"Name": "Gigabyte H610M DS2H",         "Price":  7500, "Socket/CPU": "LGA1700", "Memory Type": "DDR4", "Form Factor": "Micro-ATX"},
            "ram":         {"Name": "Corsair Vengeance 16GB DDR4", "Price":  4500, "Type": "DDR4",      "Size": "16GB"},
            "storage":     {"Name": "Kingston NV2 500GB NVMe",     "Price":  3500, "Type": "NVMe",      "Capacity": "500GB"},
        },
        "total_price": 46000,
        "psu_wattage": "550W",
        "cabinet_type": "Mid Tower",
    },
}


# ── Provider abstraction ─────────────────────────────────────────────────────

class _AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class _GeminiProvider(_AIProvider):
    def __init__(self, api_key: str):
        from google import genai
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return response.text


class _OpenAIProvider(_AIProvider):
    def __init__(self, api_key: str):
        import openai
        self._client = openai.OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a PC building expert. Always return valid JSON only."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content


# ── Main class ───────────────────────────────────────────────────────────────

class AIFallback:
    """Generates PC build recommendations via an AI API when the dataset is insufficient."""

    def __init__(self, api_key: str | None = None, provider: str = "gemini"):
        self._provider: _AIProvider | None = None

        if api_key:
            try:
                if provider == "gemini":
                    self._provider = _GeminiProvider(api_key)
                elif provider == "openai":
                    self._provider = _OpenAIProvider(api_key)
                else:
                    logger.warning("Unknown AI provider '%s'. Falling back to hardcoded builds.", provider)
            except ImportError as exc:
                logger.warning("Could not import %s library: %s. Using hardcoded fallback.", provider, exc)
            except Exception as exc:
                logger.error("Failed to initialise AI provider: %s", exc)

    # ── Public API ───────────────────────────────────────────────────────────

    def generate_build_fallback(
        self,
        intent: str,
        budget: int,
        resolution: str,
        missing_components: list[str] | None = None,
    ) -> dict | None:
        """
        Attempt to generate a build via the AI API.
        Falls back to hardcoded builds on any failure.
        """
        logger.info("AI fallback triggered for intent=%s budget=₹%d", intent, budget)

        if self._provider is not None:
            try:
                prompt = self._build_prompt(intent, budget, resolution, missing_components)
                raw    = self._provider.generate(prompt)
                result = self._parse_json(raw)
                if result and self._validate_build(result):
                    logger.info("AI build generated successfully (₹%s)", result.get("total_price"))
                    return result
                logger.warning("AI response failed validation; using hardcoded fallback.")
            except Exception as exc:
                logger.error("AI API error: %s. Using hardcoded fallback.", exc)

        return self._hardcoded_fallback(budget)

    # ── Prompt construction ──────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(
        intent: str,
        budget: int,
        resolution: str,
        missing_components: list[str] | None,
    ) -> str:
        missing_str = ", ".join(missing_components) if missing_components else "None"
        return f"""You are an expert PC builder for the Indian market.
Generate a complete PC build with the following constraints:

INTENT: {intent}
BUDGET: ₹{budget:,} (stay within this)
RESOLUTION: {resolution}
MISSING DATA FOR: {missing_str}

Rules:
- All components must be compatible (socket, RAM type, etc.)
- Use realistic current Indian market prices (INR)
- Suggest specific real product model names

Return ONLY a valid JSON object — no markdown, no explanation:
{{
    "components": {{
        "cpu":         {{"Name": "...", "Price": 0, "Socket": "...", "Core Count": 0, "TDP": 0}},
        "gpu":         {{"Name": "...", "Price": 0, "VRAM": 0, "TDP": 0}},
        "motherboard": {{"Name": "...", "Price": 0, "Socket/CPU": "...", "Memory Type": "DDR4|DDR5", "Form Factor": "ATX|Micro-ATX|Mini-ITX"}},
        "ram":         {{"Name": "...", "Price": 0, "Type": "DDR4|DDR5", "Size": "16GB|32GB"}},
        "storage":     {{"Name": "...", "Price": 0, "Type": "NVMe|SSD", "Capacity": "500GB|1TB|2TB"}}
    }},
    "total_price": 0,
    "psu_wattage": "650W",
    "cabinet_type": "Mid Tower"
}}"""

    # ── Response parsing ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        # Strip markdown fences if present
        text = re.sub(r"```(?:json)?", "", text).strip()
        # Attempt to extract the outermost JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            logger.warning("No JSON object found in AI response.")
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse error: %s", exc)
            return None

    @staticmethod
    def _validate_build(build: dict) -> bool:
        """Basic structural validation of an AI-generated build."""
        required_keys = {"components", "total_price"}
        required_components = {"cpu", "gpu", "motherboard", "ram", "storage"}
        if not required_keys.issubset(build.keys()):
            return False
        components = build.get("components", {})
        if not required_components.issubset(components.keys()):
            return False
        # Each component must have a Name and a positive Price
        for key in required_components:
            comp = components[key]
            if not comp.get("Name") or not (comp.get("Price", 0) > 0):
                return False
        return True

    # ── Hardcoded fallback ───────────────────────────────────────────────────

    @staticmethod
    def _hardcoded_fallback(budget: int) -> dict:
        if budget >= 200_000:
            return FALLBACK_BUILDS["high"]
        if budget >= 80_000:
            return FALLBACK_BUILDS["mid"]
        return FALLBACK_BUILDS["budget"]
