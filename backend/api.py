"""
PC Build Recommender — FastAPI Backend
Run with: uvicorn api:app --reload --port 8000
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Load environment variables (.env file support) ────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    logger.info(".env file loaded")
except ImportError:
    logger.warning("python-dotenv not installed. Using system environment variables only.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_PROVIDER    = os.getenv("AI_PROVIDER", "gemini")   # "gemini" or "openai"

if not GEMINI_API_KEY and not OPENAI_API_KEY:
    logger.warning(
        "No AI API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in your .env file "
        "or environment to enable AI fallback."
    )

# ── Engine import ─────────────────────────────────────────────────────────────
try:
    from src.main_engine import PCRecommendationEngine
    _ENGINE_AVAILABLE = True
    logger.info("PCRecommendationEngine imported successfully")
except ImportError as exc:
    _ENGINE_AVAILABLE = False
    logger.error("Could not import PCRecommendationEngine: %s", exc)
    logger.warning("Falling back to mock engine")

# ── Mock engine (used when real engine cannot be imported) ────────────────────

_MOCK_BUILDS = {
    "budget": {
        "components": {
            "cpu":         {"Name": "AMD Ryzen 5 5600G",          "Price": 12500, "specs": {"Cores": "6C/12T",  "Clock": "3.9 GHz"}},
            "gpu":         {"Name": "Integrated Radeon Graphics",  "Price": 0,     "specs": {"Note":  "Integrated"}},
            "motherboard": {"Name": "MSI B550M PRO-VDH",          "Price": 8500,  "specs": {"Socket": "AM4",   "RAM": "DDR4"}},
            "ram":         {"Name": "Corsair Vengeance 16GB DDR4", "Price": 3800,  "specs": {"Speed": "3200 MHz","Capacity": "16 GB"}},
            "storage":     {"Name": "Crucial P3 500GB NVMe",       "Price": 3200,  "specs": {"Capacity": "500 GB","Type": "NVMe"}},
        },
        "total_price": 28000, "psu": "450W Bronze", "cabinet": "mATX Compact",
        "intent": "Office / Study", "tier": "Entry",
    },
    "mid": {
        "components": {
            "cpu":         {"Name": "Intel Core i5-13400F",        "Price": 16500, "specs": {"Cores": "10C/16T", "Clock": "2.5 GHz"}},
            "gpu":         {"Name": "NVIDIA RTX 4060",             "Price": 26500, "specs": {"VRAM":  "8 GB",    "Cores": "3072"}},
            "motherboard": {"Name": "ASUS Prime B760-PLUS D4",     "Price": 14500, "specs": {"Socket": "LGA1700","RAM": "DDR4"}},
            "ram":         {"Name": "Kingston Fury Beast 32GB DDR4","Price": 7500, "specs": {"Speed": "3200 MHz","Capacity": "32 GB"}},
            "storage":     {"Name": "Samsung 980 1TB NVMe",        "Price": 6500,  "specs": {"Capacity": "1 TB", "Speed": "3500 MB/s"}},
        },
        "total_price": 71500, "psu": "650W Bronze", "cabinet": "Mid Tower",
        "intent": "Gaming", "tier": "Mid-Range",
    },
    "high": {
        "components": {
            "cpu":         {"Name": "AMD Ryzen 7 7800X3D",          "Price": 32500, "specs": {"Cores": "8C/16T", "Cache": "96 MB"}},
            "gpu":         {"Name": "NVIDIA RTX 4070 Super",         "Price": 52000, "specs": {"VRAM":  "12 GB",  "Cores": "7168"}},
            "motherboard": {"Name": "MSI MAG B650 Tomahawk WiFi",    "Price": 18500, "specs": {"Socket": "AM5",   "Chipset": "B650"}},
            "ram":         {"Name": "Corsair Vengeance 32GB DDR5",   "Price": 9500,  "specs": {"Speed": "6000 MHz","Capacity": "32 GB"}},
            "storage":     {"Name": "Samsung 980 Pro 1TB NVMe",      "Price": 7500,  "specs": {"Capacity": "1 TB","Speed": "7000 MB/s"}},
        },
        "total_price": 120000, "psu": "750W Gold", "cabinet": "Mid Tower",
        "intent": "Gaming", "tier": "High-End",
    },
}


class _MockEngine:
    """Fallback mock engine used when the real engine can't be loaded."""

    def __init__(self, data_path: str):
        logger.info("Mock engine initialised (data_path=%s)", data_path)

    def recommend(self, query: str, budget: float, resolution: str) -> dict:
        query_lower = query.lower()

        if budget < 50_000:
            build = _MOCK_BUILDS["budget"]
        elif budget < 100_000:
            build = _MOCK_BUILDS["mid"]
        else:
            build = _MOCK_BUILDS["high"]

        # Shallow copy so we can tweak without mutating the constant
        build = dict(build)
        components = {k: dict(v) for k, v in build["components"].items()}

        if "video" in query_lower or "edit" in query_lower:
            build["intent"] = "Video Editing"
            components["ram"]     = {"Name": "Kingston Fury 64GB DDR5", "Price": 18500, "specs": {"Speed": "5600 MHz", "Capacity": "64 GB"}}
            components["storage"] = {"Name": "WD Black SN850X 2TB",     "Price": 12500, "specs": {"Capacity": "2 TB",  "Speed": "7300 MB/s"}}
            build["total_price"]  = sum(c["Price"] for c in components.values())

        return {
            "build": {
                "components":  components,
                "total_price": build["total_price"],
                "ai_generated": False,
            },
            "psu_wattage":  build["psu"],
            "cabinet_type": build["cabinet"],
            "intent":       build["intent"],
            "tier":         build["tier"],
            "message":      f"Build optimised for {build['intent']} at {resolution} within ₹{budget:,.0f}.",
            "type":         "recommendation",
        }


# ── Engine initialisation ─────────────────────────────────────────────────────

def _resolve_data_path() -> str:
    candidates = [
        os.path.join(BASE_DIR, "data"),
        os.path.join(BASE_DIR, "..", "data"),
        os.path.join(BASE_DIR, "..", "..", "data"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            logger.info("Data path resolved: %s", path)
            return os.path.abspath(path)
    logger.warning("Data directory not found; using default path")
    return os.path.join(BASE_DIR, "data")


def _create_engine():
    data_path = _resolve_data_path()
    ai_key = GEMINI_API_KEY or OPENAI_API_KEY

    if _ENGINE_AVAILABLE:
        try:
            eng = PCRecommendationEngine(data_path=data_path, ai_api_key=ai_key)
            logger.info("Real engine loaded successfully")
            return eng
        except Exception as exc:
            logger.error("Real engine failed to load: %s — using mock", exc)

    return _MockEngine(data_path)


engine = _create_engine()

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="PC Build Recommender API",
    description="AI-powered PC build recommendations for the Indian market",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── AI Panel router ───────────────────────────────────────────────────────────
try:
    from routers.ai_panel import router as ai_router
    app.include_router(ai_router)
except ImportError as exc:
    import logging as _l; _l.getLogger(__name__).warning("AI panel router not loaded: %s", exc)

# ── Pydantic models ───────────────────────────────────────────────────────────

class ComponentSpec(BaseModel):
    Name: str
    Price: float
    specs: Optional[Dict[str, str]] = None

class BuildComponents(BaseModel):
    cpu:         ComponentSpec
    gpu:         ComponentSpec
    motherboard: ComponentSpec
    ram:         ComponentSpec
    storage:     ComponentSpec

class Build(BaseModel):
    components:   BuildComponents
    total_price:  float
    ai_generated: bool = False

class RecommendationRequest(BaseModel):
    query:      str   = Field(..., min_length=2, example="I want a gaming PC")
    budget:     float = Field(..., gt=0,         example=80000)
    resolution: str   = Field("1080p",           example="1080p")

class RecommendationResponse(BaseModel):
    build:        Build
    psu_wattage:  str
    cabinet_type: str
    intent:       str
    tier:         str
    message:      str
    type:         str = "recommendation"

# ── Response normaliser ───────────────────────────────────────────────────────

def _normalise_response(raw: dict) -> dict:
    """
    Ensures the engine response always matches RecommendationResponse.
    Handles differences between the real engine and mock engine output shapes.
    """
    # Defaults
    defaults = {
        "psu_wattage":  "650W",
        "cabinet_type": "Mid Tower",
        "intent":       "General",
        "tier":         "Mid-Range",
        "message":      "",
        "type":         "recommendation",
    }
    for key, val in defaults.items():
        raw.setdefault(key, val)

    # Normalise build
    build = raw.get("build", {})
    if not isinstance(build, dict):
        raise ValueError("Engine returned invalid 'build' field")

    build.setdefault("ai_generated", False)
    build.setdefault("total_price", 0.0)

    # Normalise each component — ensure 'specs' key always exists
    components = build.get("components", {})
    for key in ("cpu", "gpu", "motherboard", "ram", "storage"):
        comp = components.get(key, {})
        comp.setdefault("Name",  "Unknown")
        comp.setdefault("Price", 0.0)
        comp.setdefault("specs", {})
        components[key] = comp

    build["components"] = components
    raw["build"] = build
    return raw

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["General"])
async def root():
    return {
        "name":    "PC Build Recommender API",
        "version": "2.0.0",
        "status":  "running",
        "endpoints": ["/api/health", "/api/recommend", "/api/resolutions", "/docs"],
    }


@app.get("/api/health", tags=["General"])
async def health_check():
    return {
        "status":      "healthy",
        "engine":      "real" if _ENGINE_AVAILABLE else "mock",
        "ai_provider": AI_PROVIDER if (GEMINI_API_KEY or OPENAI_API_KEY) else "none",
    }


@app.get("/api/resolutions", tags=["General"])
async def get_resolutions():
    return {"resolutions": ["1080p", "1440p", "4K"]}


@app.post("/api/recommend", response_model=RecommendationResponse, tags=["Recommendation"])
async def get_recommendation(request: RecommendationRequest):
    logger.info(
        "Recommendation request — query=%r budget=₹%.0f resolution=%s",
        request.query, request.budget, request.resolution,
    )

    try:
        raw = engine.recommend(request.query, request.budget, request.resolution)
    except Exception as exc:
        logger.exception("Engine error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {exc}")

    if not raw or raw.get("type") == "error":
        msg = raw.get("message", "No build found") if raw else "Engine returned empty result"
        raise HTTPException(status_code=422, detail=msg)

    try:
        normalised = _normalise_response(raw)
    except Exception as exc:
        logger.error("Response normalisation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to format engine response")

    return normalised


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  PC Build Recommender API  v2.0.0")
    print("=" * 55)
    print("  API:   http://localhost:8000")
    print("  Docs:  http://localhost:8000/docs")
    print("  Health:http://localhost:8000/api/health")
    print("=" * 55)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")