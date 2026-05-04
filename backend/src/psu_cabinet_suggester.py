"""
PSU and Cabinet Suggester Module
Recommends power supply and case for a PC build.
"""

import logging

logger = logging.getLogger(__name__)

STANDARD_PSU_WATTAGES = [450, 550, 650, 750, 850, 1000, 1200]
PSU_SAFETY_MULTIPLIER = 1.35   # 35% headroom

# Estimated Indian market price ranges (min, max) in INR
PSU_PRICES: dict[int, tuple[int, int]] = {
    450:  (3_000,  4_500),
    550:  (4_000,  6_000),
    650:  (5_500,  8_500),
    750:  (7_500, 11_000),
    850:  (9_500, 14_000),
    1000: (13_000, 18_000),
    1200: (16_000, 25_000),
}

CABINET_PRICES: dict[str, tuple[int, int]] = {
    "Mini Tower":  (2_500,  4_500),
    "Micro Tower": (3_000,  5_500),
    "Mid Tower":   (4_000, 12_000),
    "Full Tower":  (8_000, 20_000),
}

TIER_MIN_PSU = {
    "High-End":    850,
    "Mid-Range":   650,
    "Budget":      550,
    "Entry-Level": 450,
}


class PSUSuggester:
    """Suggests PSU wattage and cabinet type for PC builds."""

    # ── PSU ─────────────────────────────────────────────────────────────────

    def suggest_psu_wattage(self, total_tdp_w: float) -> int:
        required = total_tdp_w * PSU_SAFETY_MULTIPLIER
        for psu in STANDARD_PSU_WATTAGES:
            if psu >= required:
                return psu
        return STANDARD_PSU_WATTAGES[-1]

    def get_psu_price_estimate(self, wattage: int) -> tuple[int, int]:
        return PSU_PRICES.get(wattage, (5_000, 8_000))

    # ── Cabinet ──────────────────────────────────────────────────────────────

    def suggest_cabinet_type(self, motherboard: dict | None) -> str:
        if not motherboard:
            return "Mid Tower"
        form_factor = str(motherboard.get("Form Factor", "ATX"))
        if "Mini-ITX" in form_factor or "Mini" in form_factor:
            return "Mini Tower"
        if "mATX" in form_factor or "Micro" in form_factor:
            return "Micro Tower"
        return "Mid Tower"

    def get_cabinet_price_estimate(self, cabinet_type: str) -> tuple[int, int]:
        return CABINET_PRICES.get(cabinet_type, (4_000, 8_000))

    # ── Combined recommendations ─────────────────────────────────────────────

    def get_recommendations(
        self, components: dict, tier: str = "Mid-Range"
    ) -> dict:
        cpu = components.get("cpu", {})
        gpu = components.get("gpu", {})
        mobo = components.get("motherboard")

        cpu_tdp = self._safe_float(cpu.get("TDP"), 65)
        gpu_tdp = self._safe_float(gpu.get("TDP"), 150)
        total_tdp = cpu_tdp + gpu_tdp + 50  # +50W overhead

        wattage = self.suggest_psu_wattage(total_tdp)
        # Enforce tier minimum
        min_wattage = TIER_MIN_PSU.get(tier, 550)
        wattage = max(wattage, min_wattage)

        cabinet_type = self.suggest_cabinet_type(mobo)
        psu_price    = self.get_psu_price_estimate(wattage)
        cab_price    = self.get_cabinet_price_estimate(cabinet_type)

        return {
            "psu_wattage":       f"{wattage}W",
            "psu_price_min":     psu_price[0],
            "psu_price_max":     psu_price[1],
            "cabinet_type":      cabinet_type,
            "cabinet_price_min": cab_price[0],
            "cabinet_price_max": cab_price[1],
            "psu_note":  f"{wattage}W PSU recommended (includes {int((PSU_SAFETY_MULTIPLIER-1)*100)}% headroom)",
            "cabinet_note": f"{cabinet_type} compatible with your motherboard",
        }

    def get_full_build_estimate(self, components: dict, tier: str = "Mid-Range") -> dict:
        recs = self.get_recommendations(components, tier)
        return {
            "psu": {
                "wattage":   recs["psu_wattage"],
                "price_min": recs["psu_price_min"],
                "price_max": recs["psu_price_max"],
            },
            "cabinet": {
                "type":      recs["cabinet_type"],
                "price_min": recs["cabinet_price_min"],
                "price_max": recs["cabinet_price_max"],
            },
            "additional_cost_min": recs["psu_price_min"] + recs["cabinet_price_min"],
            "additional_cost_max": recs["psu_price_max"] + recs["cabinet_price_max"],
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_float(value, default: float) -> float:
        try:
            import pandas as pd
            v = float(value)
            return v if not pd.isna(v) else default
        except (TypeError, ValueError):
            return default