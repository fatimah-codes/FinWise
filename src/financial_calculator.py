"""Deterministic financial maths. NO AI in this file.

Same inputs always give the same outputs. The LLM only receives these
numbers; it never calculates them.
"""
from __future__ import annotations

from typing import Dict

from src.config import EXPENSE_CATEGORIES, SCORE_BANDS


def _safe_pct(part: float, whole: float) -> float:
    """Percentage with divide-by-zero guard (income 0 -> 0.0)."""
    if whole is None or whole <= 0:
        return 0.0
    return (part / whole) * 100.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def total_expenses(expenses: Dict[str, float]) -> float:
    return float(sum(max(0.0, float(v or 0)) for v in expenses.values()))


def score_band(score: float) -> str:
    for threshold, label, _ in SCORE_BANDS:
        if score >= threshold:
            return label
    return SCORE_BANDS[-1][1]


def band_color(score: float) -> str:
    for threshold, _, color in SCORE_BANDS:
        if score >= threshold:
            return color
    return SCORE_BANDS[-1][2]


def preliminary_risk(score: float, remaining: float) -> str:
    """Rule-based risk label used as a sanity check against the LLM."""
    if remaining < 0 or score < 40:
        return "HIGH"
    if score < 65 or remaining == 0:
        return "MEDIUM"
    return "LOW"


def preliminary_score(income: float, savings: float, remaining: float,
                      expense_ratio: float, debt_ratio: float) -> int:
    """Weighted 0-100 heuristic.

    Weights: savings 30 | leftover cash 25 | expense ratio 25 | debt burden 20
    """
    if income <= 0:
        return 0

    savings_ratio = _safe_pct(savings, income)
    leftover_ratio = _safe_pct(remaining, income)

    # Savings: 20% of income or more earns the full 30 points
    s_savings = _clamp(savings_ratio / 20.0) * 30

    # Leftover cash: 20% of income unspent earns the full 25 points
    s_left = _clamp(leftover_ratio / 20.0) * 25

    # Expense ratio: <=50% full marks, >=100% zero, linear in between
    s_exp = _clamp((100.0 - expense_ratio) / 50.0) * 25

    # Debt burden: <=10% of income full marks, >=40% zero, linear in between
    s_debt = _clamp((40.0 - debt_ratio) / 30.0) * 20

    return int(round(s_savings + s_left + s_exp + s_debt))


def calculate(income: float, expenses: Dict[str, float], savings: float) -> Dict:
    """Run every deterministic calculation and return one result dict."""
    income = max(0.0, float(income or 0))
    savings = max(0.0, float(savings or 0))
    clean = {k: max(0.0, float(v or 0)) for k, v in expenses.items()}

    total = total_expenses(clean)
    remaining = income - total
    savings_ratio = _safe_pct(savings, income)
    expense_ratio = _safe_pct(total, income)
    debt_ratio = _safe_pct(clean.get("loan_debt", 0.0), income)

    score = preliminary_score(income, savings, remaining, expense_ratio, debt_ratio)

    breakdown = []
    for key, amount in clean.items():
        breakdown.append({
            "key": key,
            "category": EXPENSE_CATEGORIES.get(key, key),
            "amount": amount,
            "pct_of_income": round(_safe_pct(amount, income), 1),
            "pct_of_expenses": round(_safe_pct(amount, total), 1),
        })
    breakdown.sort(key=lambda r: r["amount"], reverse=True)

    return {
        "monthly_income": income,
        "savings": savings,
        "expenses": clean,
        "total_expenses": total,
        "remaining_income": remaining,
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
        "debt_ratio": round(debt_ratio, 2),
        "preliminary_score": score,
        "preliminary_band": score_band(score),
        "preliminary_risk": preliminary_risk(score, remaining),
        "breakdown": breakdown,
        "top_category": breakdown[0]["category"] if breakdown and breakdown[0]["amount"] > 0 else "None",
        "income_is_zero": income <= 0,
    }


def expense_breakdown_text(calc: Dict, currency_symbol: str = "") -> str:
    """Plain text breakdown that gets inserted into the prompt."""
    lines = []
    for row in calc["breakdown"]:
        lines.append(
            f"- {row['category']}: {currency_symbol}{row['amount']:,.2f} "
            f"({row['pct_of_income']}% of income)"
        )
    return "\n".join(lines)


def goal_tracker(goal_amount: float, goal_months: int, monthly_savings: float,
                 remaining: float) -> Dict:
    """Simple deterministic progress helper for the optional goal tracker."""
    if goal_amount <= 0 or goal_months <= 0:
        return {"enabled": False}
    needed = goal_amount / goal_months
    capacity = max(0.0, monthly_savings + max(0.0, remaining))
    months_at_current = (goal_amount / monthly_savings) if monthly_savings > 0 else None
    months_at_capacity = (goal_amount / capacity) if capacity > 0 else None
    return {
        "enabled": True,
        "needed_per_month": needed,
        "current_savings": monthly_savings,
        "capacity": capacity,
        "months_at_current": months_at_current,
        "months_at_capacity": months_at_capacity,
        "on_track": monthly_savings >= needed,
        "progress_pct": round(_clamp(monthly_savings / needed) * 100, 1) if needed > 0 else 0.0,
    }


def what_if(income: float, expenses: Dict[str, float], savings: float,
            cuts_pct: Dict[str, float]) -> Dict:
    """Recalculate after cutting some categories by a percentage.

    The money saved from the cuts is added to monthly savings.
    """
    new_exp = {k: v * (1 - cuts_pct.get(k, 0) / 100.0) for k, v in expenses.items()}
    freed = sum(expenses.values()) - sum(new_exp.values())
    return calculate(income, new_exp, savings + freed) | {"freed": freed}
