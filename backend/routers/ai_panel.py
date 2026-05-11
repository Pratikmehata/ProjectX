"""
AI Panel Endpoints
Handles: /api/ai/explain, /api/ai/chat, /api/ai/upgrades, /api/ai/compare
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Panel"])

# ── Gemini client (lazy init) ─────────────────────────────────────────────────

_gemini_model = None

def _get_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="No AI API key configured. Set GEMINI_API_KEY in your .env file."
        )

    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        _gemini_model = client
        logger.info("Gemini client initialised for AI panel")
        return _gemini_model
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="google-generativeai not installed. Run: pip install google-generativeai"
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI model init failed: {exc}")


def _call_ai(prompt: str) -> str:
    """Call Gemini and return text response."""
    model = _get_model()
    try:
        response = model.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI API error: {exc}")


def _format_build_summary(build: dict) -> str:
    """Convert build dict to a readable string for prompts."""
    components = build.get("components", {})
    lines = []
    for key in ("cpu", "gpu", "motherboard", "ram", "storage"):
        comp = components.get(key)
        if comp:
            name  = comp.get("Name", comp.get("name", "Unknown"))
            price = comp.get("Price", comp.get("price", 0))
            lines.append(f"  {key.upper()}: {name} (₹{price:,.0f})")
    total = build.get("total_price", 0)
    if total:
        lines.append(f"  TOTAL: ₹{total:,.0f}")
    return "\n".join(lines) if lines else "No components listed"


# ── Pydantic models ───────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    build:      Dict[str, Any]
    intent:     str
    budget:     float
    resolution: str = "1080p"

class ExplainResponse(BaseModel):
    explanation: str


class ChatMessage(BaseModel):
    role:    str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message:    str
    build:      Dict[str, Any]
    intent:     str
    budget:     float
    resolution: str = "1080p"
    history:    List[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str


class UpgradesRequest(BaseModel):
    current_specs: Dict[str, str]
    budget:        float
    use_case:      str = "Gaming"

class UpgradesResponse(BaseModel):
    suggestions: str


class CompareRequest(BaseModel):
    build_a:    Dict[str, Any]
    build_b:    Dict[str, Any]
    intent:     str
    resolution: str = "1080p"

class CompareResponse(BaseModel):
    comparison: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/explain", response_model=ExplainResponse)
async def explain_build(req: ExplainRequest):
    """Explain why each component was chosen for the user's use case."""
    logger.info("AI explain — intent=%s budget=₹%.0f", req.intent, req.budget)

    build_summary = _format_build_summary(req.build)

    prompt = f"""You are a PC building expert helping an Indian customer understand their build.

BUILD:
{build_summary}

USE CASE: {req.intent}
BUDGET: ₹{req.budget:,.0f}
TARGET RESOLUTION: {req.resolution}

Write a friendly, concise explanation (under 400 words) covering:
1. Why the CPU was chosen for this use case
2. Why the GPU was chosen and how it handles {req.resolution}
3. Why the RAM amount is appropriate
4. Overall build balance and value for money in the Indian market
5. One honest limitation or trade-off of this build

Use markdown formatting with ## headers. Keep it conversational, not robotic.
Do NOT suggest buying from specific stores."""

    text = _call_ai(prompt)
    return ExplainResponse(explanation=text)


@router.post("/chat", response_model=ChatResponse)
async def chat_about_build(req: ChatRequest):
    """Answer a user's question about their build."""
    logger.info("AI chat — intent=%s question=%r", req.intent, req.message[:60])

    build_summary = _format_build_summary(req.build)

    # Build conversation history string
    history_str = ""
    if req.history:
        history_lines = []
        for msg in req.history[-6:]:  # last 6 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.content}")
        history_str = "\n".join(history_lines)

    prompt = f"""You are a helpful PC building expert assistant for Indian customers.

CURRENT BUILD:
{build_summary}

USE CASE: {req.intent}
BUDGET: ₹{req.budget:,.0f}
RESOLUTION: {req.resolution}

{"CONVERSATION HISTORY:" + chr(10) + history_str if history_str else ""}

USER'S QUESTION: {req.message}

Answer helpfully and concisely. Use markdown if needed. Keep answers under 300 words.
Focus on practical advice for the Indian market (prices in INR).
If asked about compatibility, give a clear yes/no first, then explain."""

    text = _call_ai(prompt)
    return ChatResponse(reply=text)


@router.post("/upgrades", response_model=UpgradesResponse)
async def suggest_upgrades(req: UpgradesRequest):
    """Suggest the best upgrades for existing specs within a budget."""
    logger.info("AI upgrades — use_case=%s budget=₹%.0f", req.use_case, req.budget)

    specs_str = "\n".join(f"  {k.upper()}: {v}" for k, v in req.current_specs.items() if v)

    prompt = f"""You are a PC upgrade advisor for Indian customers.

CURRENT PC SPECS:
{specs_str}

UPGRADE BUDGET: ₹{req.budget:,.0f}
USE CASE: {req.use_case}

Analyze the current specs and suggest the BEST upgrades within the budget.

Structure your response with:
## 🔍 Bottleneck Analysis
(What is limiting performance most for {req.use_case})

## ⬆️ Recommended Upgrades (Priority Order)
(List upgrades by priority — highest impact first)
For each upgrade:
- Component name
- Specific model recommendation
- Estimated Indian market price
- Expected performance gain

## 💡 What to Skip
(Which components don't need upgrading yet and why)

## 💰 Budget Allocation
(How to split ₹{req.budget:,.0f} optimally)

Keep advice practical for the Indian market. All prices in INR."""

    text = _call_ai(prompt)
    return UpgradesResponse(suggestions=text)


@router.post("/compare", response_model=CompareResponse)
async def compare_builds(req: CompareRequest):
    """Compare two builds and explain trade-offs."""
    logger.info("AI compare — intent=%s", req.intent)

    summary_a = _format_build_summary(req.build_a)
    summary_b = _format_build_summary(req.build_b)

    budget_a = req.build_a.get("total_price", req.build_a.get("budget", 0))
    budget_b = req.build_b.get("total_price", req.build_b.get("budget", 0))

    prompt = f"""You are a PC build comparison expert for Indian customers.

BUILD A (₹{budget_a:,.0f}):
{summary_a}

BUILD B (₹{budget_b:,.0f}):
{summary_b}

USE CASE: {req.intent}
TARGET RESOLUTION: {req.resolution}

Compare these two builds with:

## ⚖️ Side-by-Side Comparison
(Key differences in a readable format)

## 🎮 Gaming / {req.intent} Performance
(Which build performs better and by how much approximately)

## 💰 Value for Money
(Which gives better performance per rupee)

## ✅ Choose Build A if...
(2-3 specific reasons)

## ✅ Choose Build B if...
(2-3 specific reasons)

## 🏆 Verdict
(Clear recommendation with reasoning)

Be honest and data-driven. All prices in INR."""

    text = _call_ai(prompt)
    return CompareResponse(comparison=text)
