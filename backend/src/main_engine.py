"""
Main PC Recommendation Engine
Orchestrates all modules and exposes a clean public API.
"""

import logging

from src.data_loader import ComponentDatabase
from src.intent_classifier import IntentClassifier
from src.compatibility_engine import CompatibilityEngine
from src.tier_selector import TierSelector
from src.budget_optimizer import BudgetOptimizer
from src.psu_cabinet_suggester import PSUSuggester

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class PCRecommendationEngine:
    """
    High-level facade that ties all sub-modules together.

    Usage:
        engine = PCRecommendationEngine(data_path="data/")
        result = engine.recommend("I want a gaming PC", budget=80000)
        print(result["message"])
    """

    VERSION = "2.0.0"

    def __init__(self, data_path: str, ai_api_key: str | None = None):
        logger.info("=" * 60)
        logger.info("PC Recommendation Engine v%s", self.VERSION)
        logger.info("=" * 60)

        self.db            = ComponentDatabase(data_path)
        self.ic            = IntentClassifier()
        self.compat        = CompatibilityEngine(self.db)
        self.tier_selector = TierSelector(self.db, self.ic)
        self.optimizer     = BudgetOptimizer(
            self.db, self.compat, self.tier_selector, self.ic,
            ai_api_key=ai_api_key,
        )
        self.psu           = PSUSuggester()
        logger.info("Engine ready.\n")

    # ── Primary API ──────────────────────────────────────────────────────────

    def recommend(self, user_input: str, budget: int, resolution: str = "1080p") -> dict:
        """
        Generate a PC build recommendation.

        Returns a dict with keys:
            type        "recommendation" | "error"
            intent      detected use-case
            tier        build tier label
            build       raw build dict (components, total_price, …)
            psu_wattage recommended PSU
            cabinet     recommended cabinet type
            message     human-readable markdown summary
            compat      compatibility report list
        """
        logger.info("Request — input=%r budget=₹%d resolution=%s", user_input, budget, resolution)

        # 1. Classify intent
        intent, priority_components = self.ic.classify_intent(user_input)
        logger.info("Intent: %s | Priority: %s", intent, priority_components)

        # 2. Optimise build
        build = self.optimizer.optimize_build(intent, budget, resolution)
        if not build:
            return {
                "type":    "error",
                "message": (
                    "Sorry, I couldn't find a suitable build for your requirements. "
                    "Please try a higher budget or a different use-case."
                ),
            }

        # 3. Determine tier
        tier = self.tier_selector.determine_tier(budget, intent)

        # 4. PSU & cabinet
        if "psu_wattage" in build:
            psu_wattage  = build["psu_wattage"]
            cabinet_type = build.get("cabinet_type", "Mid Tower")
            psu_details  = None
        else:
            psu_rec      = self.psu.get_recommendations(build["components"], tier)
            psu_wattage  = psu_rec["psu_wattage"]
            cabinet_type = psu_rec["cabinet_type"]
            psu_details  = psu_rec

        # 5. Compatibility report
        compat_report = self.compat.get_compatibility_report(build["components"])

        # 6. Render message
        message = self._render_markdown(
            build, intent, tier, resolution, psu_wattage, cabinet_type, psu_details
        )

        return {
            "type":        "recommendation",
            "intent":      intent,
            "tier":        tier,
            "build":       build,
            "psu_wattage": psu_wattage,
            "cabinet":     cabinet_type,
            "message":     message,
            "compat":      compat_report,
        }

    def get_alternatives(
        self, user_input: str, budget: int, resolution: str = "1080p", count: int = 3
    ) -> list[dict]:
        """Return up to `count` alternative builds at ±15% budget variations."""
        primary = self.recommend(user_input, budget, resolution)
        results = [primary]

        for multiplier in [0.85, 1.15]:
            alt_budget = int(budget * multiplier)
            alt = self.recommend(user_input, alt_budget, resolution)
            if alt["type"] == "recommendation":
                results.append(alt)
            if len(results) >= count:
                break

        return results[:count]

    def get_compatibility_report(self, build: dict) -> list[dict]:
        return self.compat.get_compatibility_report(build.get("components", {}))

    def get_supported_intents(self) -> list[str]:
        return self.ic.get_all_intents()

    # ── Response rendering ───────────────────────────────────────────────────

    def _render_markdown(
        self,
        build: dict,
        intent: str,
        tier: str,
        resolution: str,
        psu_wattage: str,
        cabinet_type: str,
        psu_details: dict | None,
    ) -> str:
        components   = build["components"]
        is_ai        = build.get("ai_generated", False)
        total_price  = build.get("total_price", 0)
        budget_usage = build.get("budget_usage", "—")

        # ── Header ───────────────────────────────────────────────
        lines = [
            f"## 🖥️  {intent} Build — {tier} ({resolution})",
            "",
        ]
        if is_ai:
            lines += ["> 🤖 **AI-Generated Recommendation** — based on market knowledge.", ""]

        # ── Core components ───────────────────────────────────────
        lines.append("### 📦 Core Components")
        lines.append("")
        lines.append("| Component | Model | Price |")
        lines.append("|-----------|-------|------:|")

        labels = {
            "cpu":         "CPU",
            "gpu":         "GPU",
            "motherboard": "Motherboard",
            "ram":         "RAM",
            "storage":     "Storage",
        }

        core_total = 0.0
        for key, label in labels.items():
            comp = components.get(key)
            if not comp:
                continue
            price = float(comp.get("Price", 0))
            core_total += price
            lines.append(f"| {label} | {comp.get('Name', '—')} | ₹{price:,.0f} |")

        lines += [
            "",
            f"**Core subtotal:** ₹{core_total:,.0f}",
            f"**Budget utilisation:** {budget_usage}",
            "",
        ]

        # ── Power & Case ──────────────────────────────────────────
        lines.append("### ⚡ Power & Case")
        lines.append("")
        if psu_details:
            psu_range = f"₹{psu_details['psu_price_min']:,} – ₹{psu_details['psu_price_max']:,}"
            cab_range = f"₹{psu_details['cabinet_price_min']:,} – ₹{psu_details['cabinet_price_max']:,}"
            lines += [
                f"| PSU       | {psu_wattage} (est. {psu_range}) |",
                f"| Cabinet   | {cabinet_type} (est. {cab_range}) |",
                "",
            ]
            extra_min = psu_details["psu_price_min"] + psu_details["cabinet_price_min"]
            extra_max = psu_details["psu_price_max"] + psu_details["cabinet_price_max"]
            lines.append(
                f"**Total estimated (with PSU & cabinet):** "
                f"₹{core_total + extra_min:,.0f} – ₹{core_total + extra_max:,.0f}"
            )
        else:
            lines += [
                f"| PSU     | {psu_wattage} |",
                f"| Cabinet | {cabinet_type} |",
                "",
                f"**Total (core components):** ₹{total_price:,.0f}",
            ]

        lines.append("")

        # ── Compatibility summary ─────────────────────────────────
        compat_report = self.compat.get_compatibility_report(components)
        if compat_report:
            lines.append("### 🔍 Compatibility")
            lines.append("")
            for item in compat_report:
                lines.append(f"- {item['status']} **{item['check']}**: {item['detail']}")
            lines.append("")

        # ── AI note ───────────────────────────────────────────────
        if is_ai:
            lines += [
                "### ℹ️  Note",
                "This build was generated by AI because specific component data was "
                "unavailable in the local dataset. Verify prices on Indian e-commerce sites "
                "before purchasing.",
                "",
            ]

        return "\n".join(lines)