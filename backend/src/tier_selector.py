"""
Tier Selector Module
Selects the best performance tier and component pair based on budget and intent.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)

CLASS_HIERARCHY = ["Entry", "Mid", "High", "Pro"]
RESOLUTION_RANK = {"1080p": 1, "1440p": 2, "4K": 3}

TIER_THRESHOLDS = [
    (150_000, "High-End"),
    (80_000,  "Mid-Range"),
    (50_000,  "Budget"),
    (0,       "Entry-Level"),
]

TIER_DESCRIPTIONS = {
    "High-End":    "Premium components for maximum performance",
    "Mid-Range":   "Balanced performance and excellent value",
    "Budget":      "Best performance-per-rupee builds",
    "Entry-Level": "Covers everyday computing needs",
}


class TierSelector:
    """Selects CPU/GPU tiers and scores component pairs for a given intent and budget."""

    def __init__(self, db, intent_classifier):
        self.db = db
        self.ic = intent_classifier

    # ── Public API ───────────────────────────────────────────────────────────

    def select_cpu_gpu_pair(
        self, intent: str, budget: float, resolution: str = "1080p"
    ) -> dict | None:
        """Return the best {cpu, gpu, total_price} pair within 60% of budget."""
        reqs = self.ic.get_requirements(intent)
        cpu_gpu_budget = budget * 0.60

        eligible_cpus = self._get_eligible_cpus(reqs.cpu_class)
        eligible_gpus = self._get_eligible_gpus(reqs.gpu_class, resolution)

        if not eligible_cpus or not eligible_gpus:
            logger.warning("No eligible CPUs or GPUs for intent=%s", intent)
            return None

        best_pair = None
        best_score = float("-inf")

        # Limit search space for performance (top 15 per component)
        for cpu in eligible_cpus[:15]:
            for gpu in eligible_gpus[:15]:
                total = cpu["Price"] + gpu["Price"]
                if total > cpu_gpu_budget:
                    continue
                score = self._score_pair(cpu, gpu, intent)
                if score > best_score:
                    best_score = score
                    best_pair = {"cpu": cpu, "gpu": gpu, "total_price": total}

        if best_pair:
            logger.debug(
                "Best pair: %s + %s @ ₹%.0f (score %.1f)",
                best_pair["cpu"].get("Name"), best_pair["gpu"].get("Name"),
                best_pair["total_price"], best_score,
            )
        return best_pair

    def determine_tier(self, budget: float, intent: str = "") -> str:
        for threshold, label in TIER_THRESHOLDS:
            if budget >= threshold:
                return label
        return "Entry-Level"

    def get_tier_description(self, tier: str) -> str:
        return TIER_DESCRIPTIONS.get(tier, "Custom build")

    # ── Component filtering ──────────────────────────────────────────────────

    def _get_eligible_cpus(self, target_class: str) -> list[dict]:
        df = self.db.components.get("cpu")
        if df is None or df.empty:
            return []

        acceptable = self._acceptable_classes(target_class)
        rows = df[df.get("Performance_Class", "Entry").isin(acceptable)] \
            if "Performance_Class" in df.columns else df

        result = self._df_to_priced_dicts(rows)
        result.sort(key=lambda x: x["Price"])
        return result

    def _get_eligible_gpus(
        self, target_class: str, resolution: str, strict_resolution: bool = True
    ) -> list[dict]:
        df = self.db.components.get("gpu")
        if df is None or df.empty:
            return []

        acceptable = self._acceptable_classes(target_class)
        target_rank = RESOLUTION_RANK.get(resolution, 1)

        result = []
        for _, row in df.iterrows():
            cls = row.get("Performance_Class", "Entry")
            res = row.get("Resolution_Target", "1080p")
            class_ok = cls in acceptable
            # If strict_resolution=False, skip the resolution check entirely
            res_ok = (not strict_resolution) or (RESOLUTION_RANK.get(res, 1) >= target_rank)
            if class_ok and res_ok:
                d = self._to_priced_dict(row)
                result.append(d)

        # If nothing matched with resolution filter, relax it automatically
        if not result and strict_resolution:
            logger.debug(
                "No GPUs matched resolution=%s for class=%s — relaxing resolution filter",
                resolution, target_class,
            )
            return self._get_eligible_gpus(target_class, resolution, strict_resolution=False)

        result.sort(key=lambda x: x["Price"])
        return result

    # ── Pair scoring ─────────────────────────────────────────────────────────

    def _score_pair(self, cpu: dict, gpu: dict, intent: str) -> float:
        """Higher is better. Penalizes bottlenecks and extreme price imbalances."""
        score = 100.0

        cpu_cores = self._safe_float(cpu.get("Core Count"), 6)
        gpu_vram  = self._safe_float(gpu.get("VRAM"), 8)
        cpu_price = cpu["Price"]
        gpu_price = gpu["Price"]

        if intent in ("FPS Gaming", "Esports"):
            if cpu_cores < 6:
                score -= 30
            if gpu_vram > 12 and cpu_cores < 8:
                score -= 15  # GPU overkill
        elif intent in ("AAA Gaming",):
            if gpu_vram < 8:
                score -= 30
            if cpu_cores < 6:
                score -= 15
        elif intent in ("Video Editing", "CAD/3D Modeling"):
            if cpu_cores < 8:
                score -= 25
            if gpu_vram < 8:
                score -= 10

        # Penalise extreme price imbalance (CPU > 2× GPU or GPU > 3× CPU)
        if cpu_price > gpu_price * 2:
            score -= 20
        if gpu_price > cpu_price * 3:
            score -= 10

        # Small bonus for using more of the budget (maximise value)
        score += (cpu_price + gpu_price) / 10_000

        return score

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _acceptable_classes(target_class: str) -> list[str]:
        idx = CLASS_HIERARCHY.index(target_class) if target_class in CLASS_HIERARCHY else 1
        return CLASS_HIERARCHY[: idx + 1]

    @staticmethod
    def _to_priced_dict(row) -> dict:
        d = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        try:
            d["Price"] = float(d.get("Price", float("inf")))
        except (TypeError, ValueError):
            d["Price"] = float("inf")
        return d

    @staticmethod
    def _df_to_priced_dicts(df: pd.DataFrame) -> list[dict]:
        result = []
        for _, row in df.iterrows():
            d = row.to_dict()
            try:
                d["Price"] = float(d.get("Price", float("inf")))
            except (TypeError, ValueError):
                d["Price"] = float("inf")
            if d["Price"] < float("inf"):
                result.append(d)
        return result

    @staticmethod
    def _safe_float(value, default: float) -> float:
        try:
            v = float(value)
            return v if not pd.isna(v) else default
        except (TypeError, ValueError):
            return default