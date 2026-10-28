"""Safe JSON parsing and small helpers."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

from src.config import CURRENCIES

REQUIRED_KEYS = [
    "financial_summary", "financial_health_score", "spending_analysis",
    "risk_level", "top_priorities", "budget_recommendations",
    "savings_strategy", "next_month_action_plan",
]
LIST_KEYS = ["top_priorities", "budget_recommendations", "savings_strategy",
             "next_month_action_plan"]


def money(value: float, currency: str = "USD") -> str:
    """Format a number with the chosen currency symbol."""
    symbol = CURRENCIES.get(currency, "")
    sign = "-" if value < 0 else ""
    return f"{sign}{symbol}{abs(value):,.0f}"


def mask_key(key: str) -> str:
    if not key or len(key) < 10:
        return "••••"
    return f"{key[:3]}…{key[-4:]}"


def looks_like_key(key: str) -> bool:
    key = (key or "").strip()
    return key.startswith("sk-") and len(key) >= 20 and " " not in key


def _extract_json_text(raw: str) -> str:
    """Strip ```json fences and grab the outermost {...} block."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v) if not isinstance(v, str) else v for v in value]
    return [str(value)]


def normalise(data: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce types, clamp the score, fill missing keys."""
    out: Dict[str, Any] = {}
    out["financial_summary"] = str(data.get("financial_summary", "")).strip()

    try:
        score = int(round(float(data.get("financial_health_score", 0))))
    except (TypeError, ValueError):
        score = 0
    out["financial_health_score"] = max(0, min(100, score))

    spending = []
    for item in data.get("spending_analysis") or []:
        if isinstance(item, dict):
            spending.append({
                "category": str(item.get("category", "")),
                "observation": str(item.get("observation", "")),
                "recommendation": str(item.get("recommendation", "")),
            })
    out["spending_analysis"] = spending

    risk = str(data.get("risk_level", "")).strip().upper()
    out["risk_level"] = risk if risk in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM"

    for key in LIST_KEYS:
        out[key] = _as_list(data.get(key))
    return out


def safe_parse_json(raw: str) -> Tuple[Dict[str, Any] | None, str | None]:
    """Parse model output safely.

    Returns (data, error). On success error is None; on failure data is None.
    """
    if not raw or not raw.strip():
        return None, "The model returned an empty response."
    try:
        data = json.loads(_extract_json_text(raw))
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON from model: {exc}"
    if not isinstance(data, dict):
        return None, "JSON was valid but not an object."
    missing = [k for k in REQUIRED_KEYS if k not in data]
    result = normalise(data)
    if missing:
        return result, f"Model left out: {', '.join(missing)} (filled with defaults)."
    return result, None


def fallback_analysis(calc: Dict, goal: str) -> Dict[str, Any]:
    """Rule-based result shown when the LLM output cannot be parsed.

    Keeps the dashboard usable without pretending the AI answered.
    """
    score = calc["preliminary_score"]
    top = calc["breakdown"][:3]
    return normalise({
        "financial_summary": (
            "The AI response could not be read, so this is a rule-based summary. "
            f"Expenses are {calc['expense_ratio']:.0f}% of income and savings are "
            f"{calc['savings_ratio']:.0f}% of income. Your goal is: {goal}."
        ),
        "financial_health_score": score,
        "spending_analysis": [
            {"category": r["category"],
             "observation": f"{r['pct_of_income']}% of income.",
             "recommendation": "Review this category for possible savings."}
            for r in top if r["amount"] > 0
        ],
        "risk_level": calc["preliminary_risk"],
        "top_priorities": ["Cover essentials first", f"Work toward: {goal}"],
        "budget_recommendations": ["Track every expense for one month",
                                   "Aim to keep expenses below 80% of income"],
        "savings_strategy": ["Save a fixed amount right after income arrives"],
        "next_month_action_plan": ["Pick one category and trim it by 10%"],
    })
