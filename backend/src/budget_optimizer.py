"""
Budget Optimizer Module
Optimizes PC builds within budget constraints using intent-aware allocation.
Strategies: High-End (₹2L+), Mid-Range (₹50K-₹2L), Budget (<₹50K).
"""

import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

# CPU+GPU share of total budget per strategy
ALLOCATION = {
    "high":   (0.45, 0.80),   # (min%, max%) of max_budget
    "medium": (0.40, 0.75),
    "budget": (0.30, 0.75),
}

BUDGET_HEADROOM = 0.92   # Use 92% of stated budget to leave 8% buffer


class BudgetOptimizer:
    """Selects the best full build for a given intent, budget and resolution."""

    def __init__(self, db, compatibility_engine, tier_selector, intent_classifier, ai_api_key=None):
        self.db       = db
        self.compat   = compatibility_engine
        self.tier_sel = tier_selector
        self.ic       = intent_classifier

        self._ai: "AIFallback | None" = None
        if ai_api_key:
            try:
                try:
                    from src.ai_fallback import AIFallback
                except ImportError:
                    from ai_fallback import AIFallback
                import os
                provider = os.getenv("AI_PROVIDER", "gemini")
                self._ai = AIFallback(api_key=ai_api_key, provider=provider)
                logger.info("AI fallback initialised (provider=%s)", provider)
            except Exception as exc:
                logger.warning("Could not initialise AI fallback: %s", exc)
        else:
            logger.warning("No AI API key provided — AI fallback disabled")

    # ── Main entry point ─────────────────────────────────────────────────────

    def optimize_build(self, intent: str, budget: int, resolution: str = "1080p") -> dict | None:
        max_budget = budget * BUDGET_HEADROOM
        logger.info("Optimising build | intent=%s budget=₹%d resolution=%s", intent, budget, resolution)

        if not self.db.has_data("cpu") or not self.db.has_data("gpu"):
            logger.warning("Missing CPU or GPU data — trying AI fallback")
            return self._try_ai_fallback(intent, budget, resolution)

        try:
            if budget >= 200_000:
                result = self._strategy_high_end(max_budget, resolution, intent)
            elif budget >= 50_000:
                result = self._strategy_mid_range(max_budget, resolution, intent)
            else:
                result = self._strategy_budget(max_budget, intent)

            if result is None:
                logger.warning("No build found in database; trying AI fallback")
                return self._try_ai_fallback(intent, budget, resolution)
            return result

        except Exception as exc:
            logger.exception("Unexpected error during optimisation: %s", exc)
            return self._try_ai_fallback(intent, budget, resolution)

    # ── Strategy: High-End ───────────────────────────────────────────────────

    def _strategy_high_end(self, max_budget: float, resolution: str, intent: str) -> dict | None:
        logger.info("Strategy: HIGH-END (max ₹%.0f)", max_budget)

        cpus = self._cpus_for_intent(intent, strategy="high")
        gpus = self._gpus_for_intent(intent, resolution, strategy="high")
        if not cpus or not gpus:
            return None

        best, best_score = None, float("-inf")

        for cpu in cpus[:30]:
            for gpu in gpus[:30]:
                pair_total = cpu["Price"] + gpu["Price"]
                # Only hard cap: pair must fit within budget
                if pair_total > max_budget * 0.85:
                    continue

                mobo = self.compat.find_compatible_motherboard(cpu, max_budget - pair_total)
                if not mobo:
                    continue
                ram = self.compat.find_compatible_ram(mobo, min_size_gb=32)
                if not ram:
                    ram = self.compat.find_compatible_ram(mobo, min_size_gb=16)
                if not ram:
                    continue
                storage = self._storage_best_nvme(max_budget, cap_budget=25_000)

                total = pair_total + mobo["Price"] + ram["Price"] + storage["Price"]
                if total > max_budget * 1.05:
                    continue

                usage = total / max_budget
                score = self._perf_score(cpu, gpu) + usage * 50
                if score > best_score:
                    best_score = score
                    best = self._make_build(cpu, gpu, mobo, ram, storage, total, usage, "high-end")

        if best:
            logger.info("High-end build found: ₹%.0f", best["total_price"])
        else:
            logger.warning("No high-end build; falling back to mid-range")
            best = self._strategy_mid_range(max_budget, resolution, intent)

        return best

    # ── Strategy: Mid-Range ──────────────────────────────────────────────────

    def _strategy_mid_range(self, max_budget: float, resolution: str, intent: str) -> dict | None:
        logger.info("Strategy: MID-RANGE (max ₹%.0f)", max_budget)

        cpus = self._cpus_for_intent(intent, strategy="mid")
        gpus = self._gpus_for_intent(intent, resolution, strategy="mid")
        if not cpus or not gpus:
            return self._strategy_budget(max_budget, intent)

        best, best_score = None, float("-inf")

        for cpu in cpus[:40]:
            for gpu in gpus[:40]:
                pair_total = cpu["Price"] + gpu["Price"]
                if pair_total > max_budget * 0.80:
                    continue

                mobo = self.compat.find_compatible_motherboard(cpu, max_budget - pair_total)
                if not mobo:
                    continue
                ram = self.compat.find_compatible_ram(mobo, min_size_gb=16)
                if not ram:
                    continue
                storage = self._storage_best_value()

                total = pair_total + mobo["Price"] + ram["Price"] + storage["Price"]
                if total > max_budget * 1.05:
                    continue

                usage = total / max_budget
                perf  = self._perf_score(cpu, gpu)
                score = perf / (total / 1_000) * (1 + usage * 0.5)

                if score > best_score:
                    best_score = score
                    best = self._make_build(cpu, gpu, mobo, ram, storage, total, usage, "mid-range")

        if best:
            logger.info("Mid-range build found: ₹%.0f", best["total_price"])
        else:
            logger.warning("No mid-range build; falling back to budget")
            best = self._strategy_budget(max_budget, intent)

        return best

    # ── Strategy: Budget ─────────────────────────────────────────────────────

    def _strategy_budget(self, max_budget: float, intent: str = "") -> dict | None:
        logger.info("Strategy: BUDGET (max ₹%.0f)", max_budget)

        cpu     = self._cheapest_cpu()
        gpu     = self._cheapest_gpu()
        if not cpu or not gpu:
            return None

        mobo    = self.compat.find_compatible_motherboard(cpu)
        if not mobo:
            return None
        ram     = self.compat.find_compatible_ram(mobo, min_size_gb=8)
        if not ram:
            return None
        storage = self._storage_cheapest()

        total = cpu["Price"] + gpu["Price"] + mobo["Price"] + ram["Price"] + storage["Price"]

        if total > max_budget * 1.1:
            logger.warning("Even cheapest build (₹%.0f) exceeds budget (₹%.0f)", total, max_budget)
            return None

        # Try to upgrade if significant headroom remains
        if max_budget > total * 1.3:
            upgraded = self._upgrade_budget_build(max_budget)
            if upgraded:
                return upgraded

        usage = total / max_budget
        return self._make_build(cpu, gpu, mobo, ram, storage, total, usage, "budget")

    # ── Intent-aware component selection ────────────────────────────────────

    # Maps intent → (cpu_class, gpu_class) overrides per strategy level
    _INTENT_CLASS_MAP = {
        # intent: {high: (cpu, gpu), mid: (cpu, gpu), budget: (cpu, gpu)}
        "Programming":        {"high": ("Pro",  "Mid"),  "mid": ("High", "Entry"), "budget": ("Mid", "Entry")},
        "Office/Productivity":{"high": ("High", "Mid"),  "mid": ("Mid",  "Entry"), "budget": ("Entry","Entry")},
        "CAD/3D Modeling":    {"high": ("Pro",  "High"), "mid": ("High", "Mid"),   "budget": ("Mid",  "Mid")},
        "Video Editing":      {"high": ("Pro",  "High"), "mid": ("High", "Mid"),   "budget": ("Mid",  "Mid")},
        "Streaming":          {"high": ("Pro",  "High"), "mid": ("High", "High"),  "budget": ("Mid",  "Mid")},
        "Gaming":             {"high": ("High", "Pro"),  "mid": ("Mid",  "High"),  "budget": ("Mid",  "Mid")},
        "FPS Gaming":         {"high": ("Pro",  "High"), "mid": ("High", "Mid"),   "budget": ("Mid",  "Mid")},
        "Esports":            {"high": ("Pro",  "High"), "mid": ("High", "Mid"),   "budget": ("Mid",  "Mid")},
        "AAA Gaming":         {"high": ("High", "Pro"),  "mid": ("High", "High"),  "budget": ("Mid",  "High")},
    }
    _DEFAULT_CLASS = {"high": ("High", "High"), "mid": ("Mid", "Mid"), "budget": ("Entry", "Entry")}

    def _intent_classes(self, intent: str, strategy: str) -> tuple[str, str]:
        return self._INTENT_CLASS_MAP.get(intent, self._DEFAULT_CLASS).get(
            strategy, self._DEFAULT_CLASS[strategy]
        )

    def _cpus_for_intent(self, intent: str, strategy: str) -> list[dict]:
        cpu_class, _ = self._intent_classes(intent, strategy)
        cpus = self.tier_sel._get_eligible_cpus(cpu_class)
        # Sort: high strategy → best first; others → value first
        if strategy == "high":
            cpus.sort(key=lambda x: self._cpu_score(x), reverse=True)
        else:
            cpus.sort(key=lambda x: self._cpu_score(x) / x["Price"] if x["Price"] else 0, reverse=True)
        return cpus

    def _gpus_for_intent(self, intent: str, resolution: str, strategy: str) -> list[dict]:
        _, gpu_class = self._intent_classes(intent, strategy)
        gpus = self.tier_sel._get_eligible_gpus(gpu_class, resolution)
        if strategy == "high":
            gpus.sort(key=lambda x: self._gpu_score(x), reverse=True)
        else:
            gpus.sort(key=lambda x: self._gpu_score(x) / x["Price"] if x["Price"] else 0, reverse=True)
        return gpus

    def _upgrade_budget_build(self, max_budget: float) -> dict | None:
        """Scan for the best build between 70-90% of budget."""
        lo, hi = max_budget * 0.70, max_budget * 0.90
        cpus = self._cpus_by_price()
        gpus = self._gpus_by_price()
        best, best_score = None, float("-inf")

        for cpu in cpus[:30]:
            for gpu in gpus[:30]:
                mobo = self.compat.find_compatible_motherboard(cpu)
                if not mobo:
                    continue
                ram = self.compat.find_compatible_ram(mobo, min_size_gb=8)
                if not ram:
                    continue
                storage = self._storage_cheapest()
                total = cpu["Price"] + gpu["Price"] + mobo["Price"] + ram["Price"] + storage["Price"]
                if lo <= total <= hi:
                    score = self._perf_score(cpu, gpu)
                    if score > best_score:
                        best_score = score
                        best = self._make_build(cpu, gpu, mobo, ram, storage, total,
                                                total / max_budget, "upgraded-budget")
        return best

    # ── AI fallback ──────────────────────────────────────────────────────────

    def _try_ai_fallback(self, intent: str, budget: int, resolution: str) -> dict | None:
        if self._ai is None:
            logger.error("AI fallback not available and no local build found")
            return None

        missing = [k for k in ("cpu", "gpu", "motherboard", "ram", "storage")
                   if not self.db.has_data(k)]

        ai_build = self._ai.generate_build_fallback(
            intent=intent, budget=budget, resolution=resolution,
            missing_components=missing or None,
        )
        if not ai_build:
            return None

        max_budget = budget * BUDGET_HEADROOM
        usage = ai_build["total_price"] / max_budget

        return {
            "components":    ai_build["components"],
            "total_price":   ai_build["total_price"],
            "budget_usage":  f"{usage * 100:.1f}%",
            "type":          "ai-generated",
            "psu_wattage":   ai_build.get("psu_wattage", "650W"),
            "cabinet_type":  ai_build.get("cabinet_type", "Mid Tower"),
            "ai_generated":  True,
        }

    # ── Component retrieval helpers ──────────────────────────────────────────

    def _iter_priced(self, comp_type: str):
        df = self.db.components.get(comp_type, pd.DataFrame())
        for _, row in df.iterrows():
            d = row.to_dict()
            try:
                price = float(d.get("Price", 0))
            except (TypeError, ValueError):
                continue
            if price > 0:
                d["Price"] = price
                yield d

    def _cpus_by_performance(self) -> list[dict]:
        return sorted(self._iter_priced("cpu"), key=lambda x: self._cpu_score(x), reverse=True)

    def _cpus_by_value(self) -> list[dict]:
        def value(c):
            p = c["Price"]
            return self._cpu_score(c) / p if p else 0
        return sorted(self._iter_priced("cpu"), key=value, reverse=True)

    def _cpus_by_price(self) -> list[dict]:
        return sorted(self._iter_priced("cpu"), key=lambda x: x["Price"])

    def _gpus_by_performance(self) -> list[dict]:
        return sorted(self._iter_priced("gpu"), key=lambda x: self._gpu_score(x), reverse=True)

    def _gpus_by_value(self) -> list[dict]:
        def value(g):
            p = g["Price"]
            return self._gpu_score(g) / p if p else 0
        return sorted(self._iter_priced("gpu"), key=value, reverse=True)

    def _gpus_by_price(self) -> list[dict]:
        return sorted(self._iter_priced("gpu"), key=lambda x: x["Price"])

    def _cheapest_cpu(self) -> dict | None:
        cpus = self._cpus_by_price()
        return cpus[0] if cpus else None

    def _cheapest_gpu(self) -> dict | None:
        gpus = self._gpus_by_price()
        return gpus[0] if gpus else None

    # ── Storage helpers ──────────────────────────────────────────────────────

    def _storage_best_nvme(self, max_budget: float, cap_budget: int = 25_000) -> dict:
        df = self.db.components.get("storage", pd.DataFrame())
        if df.empty:
            return self._storage_cheapest()
        df = df[df.get("Type", pd.Series()).str.contains("NVMe", na=False)].copy()
        df = df[df["Price"].astype(float) <= min(cap_budget, max_budget * 0.05)]
        if df.empty:
            return self._storage_cheapest()
        best = df.nlargest(1, "Price").iloc[0].to_dict()
        best["Price"] = float(best["Price"])
        return best

    def _storage_best_value(self) -> dict:
        df = self.db.components.get("storage", pd.DataFrame())
        if df.empty:
            return self._storage_cheapest()
        df = df[df.get("Type", pd.Series()).str.contains("NVMe", na=False)].copy()
        if df.empty:
            return self._storage_cheapest()
        capacity = df["Capacity"].astype(str).str.extract(r"(\d+)", expand=False).astype(float)
        df = df.copy()
        df["_value"] = capacity / df["Price"].astype(float)
        best = df.nlargest(1, "_value").iloc[0].to_dict()
        best["Price"] = float(best["Price"])
        return best

    def _storage_cheapest(self) -> dict:
        df = self.db.components.get("storage", pd.DataFrame())
        if not df.empty and "Price" in df.columns:
            row = df.nsmallest(1, "Price").iloc[0].to_dict()
            row["Price"] = float(row["Price"])
            return row
        return {"Name": "500GB SSD", "Price": 3_500.0, "Type": "SSD", "Capacity": "500GB"}

    # ── Scoring helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _cpu_score(cpu: dict) -> float:
        class_mult = {"Entry": 1, "Mid": 2, "High": 3, "Pro": 4}
        cores = float(cpu.get("Core Count") or 6)
        cls   = class_mult.get(cpu.get("Performance_Class", "Entry"), 1)
        return cores * 10 + cls * 20 + cpu["Price"] / 1_000

    @staticmethod
    def _gpu_score(gpu: dict) -> float:
        class_mult = {"Entry": 1, "Mid": 2, "High": 3, "Pro": 4}
        vram = float(gpu.get("VRAM") or 8)
        cls  = class_mult.get(gpu.get("Performance_Class", "Entry"), 1)
        return vram * 15 + cls * 30 + gpu["Price"] / 1_000

    def _perf_score(self, cpu: dict, gpu: dict) -> float:
        return self._cpu_score(cpu) + self._gpu_score(gpu)

    # ── Build dict factory ───────────────────────────────────────────────────

    @staticmethod
    def _make_build(cpu, gpu, mobo, ram, storage, total, usage, build_type) -> dict:
        return {
            "components": {
                "cpu":         cpu,
                "gpu":         gpu,
                "motherboard": mobo,
                "ram":         ram,
                "storage":     storage,
            },
            "total_price":  total,
            "budget_usage": f"{usage * 100:.1f}%",
            "type":         build_type,
        }

    # ── Static helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_ram_size(size_str) -> int:
        try:
            nums = re.findall(r"\d+", str(size_str))
            return int(nums[0]) if nums else 16
        except (IndexError, ValueError):
            return 16