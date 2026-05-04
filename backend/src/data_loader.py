"""
Data Loader Module
Loads and indexes PC component data from CSV files with caching and validation.
"""

import os
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Price-tier thresholds (INR) ──────────────────────────────────────────────
CPU_TIERS = [
    (10_000,  "Entry"),
    (20_000,  "Mid"),
    (35_000,  "High"),
    (float("inf"), "Pro"),
]
GPU_TIERS = [
    (25_000,  "Entry"),
    (45_000,  "Mid"),
    (70_000,  "High"),
    (float("inf"), "Pro"),
]
GPU_RESOLUTION_THRESHOLDS = {
    30_000: "1440p",
    50_000: "4K",
}

FILES_CONFIG: dict[str, str] = {
    "cpu":         "cpu.csv",
    "gpu":         "gpu.csv",
    "motherboard": "motherboard.csv",
    "ram":         "ram.csv",
    "storage":     "storage.csv",
}


def _price_tier(price: float, tiers: list[tuple]) -> str:
    for threshold, label in tiers:
        if price < threshold:
            return label
    return tiers[-1][1]


class ComponentDatabase:
    """Loads, validates, and indexes PC component CSVs for fast lookup."""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.components: dict[str, pd.DataFrame] = {}

        self._load_all()
        self._enrich_all()
        self._build_indexes()
        self._log_stats()

    # ── Loading ──────────────────────────────────────────────────────────────

    def _load_all(self):
        logger.info("Loading component data from: %s", self.data_path)
        for comp_type, filename in FILES_CONFIG.items():
            filepath = os.path.join(self.data_path, filename)
            if not os.path.exists(filepath):
                logger.warning("File not found: %s", filepath)
                self.components[comp_type] = pd.DataFrame()
                continue

            df = pd.read_csv(filepath)
            df = self._clean_prices(df, comp_type)
            self.components[comp_type] = df
            logger.info("  %-12s %d rows loaded", comp_type, len(df))

    @staticmethod
    def _clean_prices(df: pd.DataFrame, comp_type: str) -> pd.DataFrame:
        if "Price" not in df.columns:
            logger.warning("%s CSV has no 'Price' column", comp_type)
            return df

        df = df.copy()
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        before = len(df)
        df = df[df["Price"].notna() & (df["Price"] > 0)]
        removed = before - len(df)
        if removed:
            logger.debug("  %s: removed %d rows with invalid prices", comp_type, removed)
        return df.reset_index(drop=True)

    # ── Enrichment ───────────────────────────────────────────────────────────

    def _enrich_all(self):
        self._enrich_cpus()
        self._enrich_gpus()

    def _enrich_cpus(self):
        df = self.components.get("cpu")
        if df is None or df.empty:
            return

        df = df.copy()
        df["Performance_Class"] = df["Price"].apply(
            lambda p: _price_tier(p, CPU_TIERS)
        )
        df["Gaming_Score"] = (df["Price"] / 5_000).clip(0, 10).round(2)
        self.components["cpu"] = df

    def _enrich_gpus(self):
        df = self.components.get("gpu")
        if df is None or df.empty:
            return

        df = df.copy()

        # Extract VRAM
        if "Memory" in df.columns and "VRAM" not in df.columns:
            df["VRAM"] = (
                df["Memory"].astype(str)
                .str.extract(r"(\d+)", expand=False)
                .astype(float)
            )
        elif "VRAM" not in df.columns:
            df["VRAM"] = 8.0

        df["Performance_Class"] = df["Price"].apply(
            lambda p: _price_tier(p, GPU_TIERS)
        )

        # Resolution target
        def _res(price):
            for threshold, res in sorted(GPU_RESOLUTION_THRESHOLDS.items()):
                if price >= threshold:
                    result = res
                else:
                    break
            else:
                result = GPU_RESOLUTION_THRESHOLDS.get(
                    max(GPU_RESOLUTION_THRESHOLDS), "1080p"
                )
            return result

        df["Resolution_Target"] = df["Price"].apply(
            lambda p: "4K" if p >= 50_000 else ("1440p" if p >= 30_000 else "1080p")
        )
        self.components["gpu"] = df

    # ── Indexes ──────────────────────────────────────────────────────────────

    def _build_indexes(self):
        """Build fast-lookup dictionaries keyed by socket / class / resolution."""
        self.cpu_by_socket:     dict[str, list[dict]] = {}
        self.cpu_by_class:      dict[str, list[dict]] = {}
        self.mobo_by_socket:    dict[str, list[dict]] = {}
        self.gpu_by_class:      dict[str, list[dict]] = {}
        self.gpu_by_resolution: dict[str, list[dict]] = {}

        for _, row in self.components.get("cpu", pd.DataFrame()).iterrows():
            d = row.to_dict()
            socket = d.get("Socket")
            if socket and pd.notna(socket):
                self.cpu_by_socket.setdefault(str(socket), []).append(d)
            cls = d.get("Performance_Class", "Entry")
            self.cpu_by_class.setdefault(cls, []).append(d)

        for _, row in self.components.get("motherboard", pd.DataFrame()).iterrows():
            d = row.to_dict()
            socket = d.get("Socket/CPU")
            if socket and pd.notna(socket):
                self.mobo_by_socket.setdefault(str(socket), []).append(d)

        for _, row in self.components.get("gpu", pd.DataFrame()).iterrows():
            d = row.to_dict()
            cls = d.get("Performance_Class", "Entry")
            self.gpu_by_class.setdefault(cls, []).append(d)
            res = d.get("Resolution_Target", "1080p")
            self.gpu_by_resolution.setdefault(str(res), []).append(d)

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log_stats(self):
        logger.info("── Component Database Summary ──────────────────────")
        total = 0
        for comp_type, df in self.components.items():
            count = len(df)
            total += count
            if count == 0 or "Price" not in df.columns:
                logger.info("  %-12s  0 components", comp_type)
                continue
            logger.info(
                "  %-12s  %d items | ₹%s – ₹%s (avg ₹%s)",
                comp_type, count,
                f"{df['Price'].min():,.0f}",
                f"{df['Price'].max():,.0f}",
                f"{df['Price'].mean():,.0f}",
            )
        logger.info("  %-12s  %d total", "TOTAL", total)
        logger.info("────────────────────────────────────────────────────")

    # ── Public helpers ───────────────────────────────────────────────────────

    def get_component(self, comp_type: str, name: str) -> dict | None:
        """Fuzzy-search a component by name fragment."""
        df = self.components.get(comp_type)
        if df is None or df.empty or "Name" not in df.columns:
            return None
        matches = df[df["Name"].str.contains(name, case=False, na=False)]
        return matches.iloc[0].to_dict() if not matches.empty else None

    def get_by_price_range(
        self, comp_type: str, min_price: float, max_price: float
    ) -> list[dict]:
        """Return all components of a type within a price band."""
        df = self.components.get(comp_type)
        if df is None or df.empty or "Price" not in df.columns:
            return []
        mask = (df["Price"] >= min_price) & (df["Price"] <= max_price)
        return df[mask].to_dict("records")

    def has_data(self, comp_type: str) -> bool:
        df = self.components.get(comp_type)
        return df is not None and not df.empty