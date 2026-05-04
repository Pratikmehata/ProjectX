"""
Compatibility Engine Module
Validates and enforces component compatibility for PC builds.
"""

import logging
import re
import pandas as pd

logger = logging.getLogger(__name__)

# Known socket families for fuzzy matching
SOCKET_FAMILIES = [
    {"LGA1700", "LGA1851"},   # Intel 12th–15th gen share boards (with BIOS update caveats)
    {"AM4"},
    {"AM5"},
    {"LGA1200"},
    {"LGA2066"},
    {"TR4", "TRX40", "TRX50"},  # Threadripper
]

DEFAULT_CPU_TDP = 65
DEFAULT_GPU_TDP = 150
DEFAULT_OVERHEAD_W = 50   # Mobo + RAM + storage + fans


class CompatibilityEngine:
    """Validates CPU/Mobo/RAM compatibility and estimates power requirements."""

    def __init__(self, db):
        self.db = db

    # ── Socket compatibility ─────────────────────────────────────────────────

    def check_cpu_mobo_compatibility(self, cpu: dict, motherboard: dict) -> bool:
        cpu_socket = self._safe_str(cpu.get("Socket"))
        mobo_socket = self._safe_str(motherboard.get("Socket/CPU"))

        if not cpu_socket or not mobo_socket:
            return False
        if cpu_socket == mobo_socket:
            return True

        # Check if both belong to the same family
        for family in SOCKET_FAMILIES:
            if cpu_socket in family and mobo_socket in family:
                return True
        return False

    # ── Motherboard selection ────────────────────────────────────────────────

    def find_compatible_motherboard(
        self, cpu: dict, budget_remaining: float | None = None
    ) -> dict | None:
        """Return the best compatible motherboard for a given CPU."""
        mobo_df = self.db.components.get("motherboard")
        if mobo_df is None or mobo_df.empty:
            return None

        candidates = [
            self._to_priced_dict(row)
            for _, row in mobo_df.iterrows()
            if self.check_cpu_mobo_compatibility(cpu, row.to_dict())
        ]

        if not candidates:
            logger.debug("No compatible motherboard found for socket: %s", cpu.get("Socket"))
            return None

        candidates.sort(key=lambda x: x["Price"])

        if budget_remaining is not None:
            target = budget_remaining * 0.15
            affordable = [m for m in candidates if m["Price"] <= target]
            if affordable:
                return affordable[-1]  # Best within target
            # Fallback: cheapest that fits in 25% of remaining
            affordable = [m for m in candidates if m["Price"] <= budget_remaining * 0.25]
            if affordable:
                return affordable[0]

        return candidates[0]

    # ── RAM selection ────────────────────────────────────────────────────────

    def find_compatible_ram(
        self, motherboard: dict, min_size_gb: int = 16
    ) -> dict | None:
        """Return cheapest RAM compatible with the motherboard."""
        ram_df = self.db.components.get("ram")
        if ram_df is None or ram_df.empty:
            return None

        mobo_ram_type = self._safe_str(motherboard.get("Memory Type", "DDR4")).lower()

        candidates = []
        for _, row in ram_df.iterrows():
            d = self._to_priced_dict(row)
            ram_type = self._safe_str(d.get("Type", "")).lower()
            if mobo_ram_type not in ram_type and ram_type not in mobo_ram_type:
                continue
            size = self._extract_ram_size(d.get("Size", ""))
            if size >= min_size_gb:
                candidates.append(d)

        if not candidates:
            return None

        candidates.sort(key=lambda x: x["Price"])
        return candidates[0]

    # ── Power estimation ─────────────────────────────────────────────────────

    def calculate_total_tdp(self, cpu: dict, gpu: dict) -> float:
        cpu_tdp = self._safe_float(cpu.get("TDP"), DEFAULT_CPU_TDP)
        gpu_tdp = self._safe_float(gpu.get("TDP"), DEFAULT_GPU_TDP)
        return cpu_tdp + gpu_tdp + DEFAULT_OVERHEAD_W

    # ── Build-level checks ───────────────────────────────────────────────────

    def check_full_compatibility(self, build: dict) -> tuple[bool, list[str]]:
        """Return (is_compatible, list_of_issues)."""
        issues: list[str] = []
        cpu = build.get("cpu", {})
        motherboard = build.get("motherboard", {})
        ram = build.get("ram", {})

        if cpu and motherboard:
            if not self.check_cpu_mobo_compatibility(cpu, motherboard):
                issues.append(
                    f"Socket mismatch: CPU ({cpu.get('Socket')}) ↔ "
                    f"Motherboard ({motherboard.get('Socket/CPU')})"
                )

        if motherboard and ram:
            ram_type = self._safe_str(ram.get("Type", "")).lower()
            mobo_type = self._safe_str(motherboard.get("Memory Type", "DDR4")).lower()
            if ram_type and mobo_type and ram_type not in mobo_type:
                issues.append(
                    f"RAM type mismatch: {ram.get('Type')} with {motherboard.get('Memory Type')} board"
                )

        return len(issues) == 0, issues

    def get_compatibility_report(self, build: dict) -> list[dict]:
        """Return a human-readable compatibility report for a build."""
        report = []
        cpu        = build.get("cpu", {})
        gpu        = build.get("gpu", {})
        motherboard = build.get("motherboard", {})
        ram        = build.get("ram", {})

        # CPU ↔ Motherboard
        if cpu and motherboard:
            ok = self.check_cpu_mobo_compatibility(cpu, motherboard)
            report.append({
                "check": "CPU ↔ Motherboard",
                "detail": f"{cpu.get('Socket')} ↔ {motherboard.get('Socket/CPU')}",
                "compatible": ok,
                "status": "✅ Compatible" if ok else "❌ Incompatible",
            })

        # RAM ↔ Motherboard
        if motherboard and ram:
            ram_type  = self._safe_str(ram.get("Type", "")).lower()
            mobo_type = self._safe_str(motherboard.get("Memory Type", "DDR4")).lower()
            ok = ram_type in mobo_type or mobo_type in ram_type
            report.append({
                "check": "RAM ↔ Motherboard",
                "detail": f"{ram.get('Type')} ↔ {motherboard.get('Memory Type')}",
                "compatible": ok,
                "status": "✅ Compatible" if ok else "⚠️  Check compatibility",
            })

        # Power estimate
        if cpu and gpu:
            total_tdp = self.calculate_total_tdp(cpu, gpu)
            recommended_psu = int(total_tdp * 1.3 / 50 + 1) * 50  # Round up to nearest 50W
            report.append({
                "check": "Power Requirements",
                "detail": f"Total TDP ≈ {total_tdp:.0f}W → Recommended PSU ≥ {recommended_psu}W",
                "compatible": True,
                "status": "✅ Estimated",
            })

        return report

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_str(value) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        return str(value).strip()

    @staticmethod
    def _safe_float(value, default: float) -> float:
        try:
            v = float(value)
            return v if not pd.isna(v) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_priced_dict(row) -> dict:
        d = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        price = d.get("Price", 0)
        try:
            d["Price"] = float(price) if not pd.isna(price) else float("inf")
        except (TypeError, ValueError):
            d["Price"] = float("inf")
        return d

    @staticmethod
    def _extract_ram_size(size_str) -> int:
        try:
            nums = re.findall(r"\d+", str(size_str))
            return int(nums[0]) if nums else 16
        except (IndexError, ValueError):
            return 16