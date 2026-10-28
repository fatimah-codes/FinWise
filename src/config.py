"""Central settings and form options for FinWise AI."""
import os

from dotenv import load_dotenv

# Load .env once at import time (python-dotenv). The UI also asks for the key.
load_dotenv()

APP_NAME = "FinWise AI"
APP_TAGLINE = "AI-Powered Personal Financial Analysis & Smart Budget Assistant"
APP_VERSION = "1.0.0"

DISCLAIMER = (
    "Educational use only. FinWise AI is a learning prototype, not financial advice. "
    "It does not guarantee any outcome, connect to bank accounts or move money. "
    "Please talk to a qualified financial professional before making real money decisions."
)

ENV_API_KEY = os.getenv("OPENAI_API_KEY", "")

MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3

CACHE_OPTIONS = ["None", "In-Memory", "SQLite"]
SQLITE_PATH = ".finwise_cache.db"

# key -> label. The PDF lists nine names but asks for ten categories,
# so "Shopping & Subscriptions" is added as the tenth.
EXPENSE_CATEGORIES = {
    "housing": "Housing / Rent",
    "food": "Food & Groceries",
    "transportation": "Transportation",
    "utilities": "Utilities",
    "education": "Education",
    "healthcare": "Healthcare",
    "entertainment": "Entertainment",
    "shopping": "Shopping & Subscriptions",
    "loan_debt": "Loan / Debt Payments",
    "other": "Other",
}

EXPENSE_ICONS = {
    "housing": "🏠", "food": "🍽️", "transportation": "🚌", "utilities": "💡",
    "education": "🎓", "healthcare": "🩺", "entertainment": "🎬",
    "shopping": "🛍️", "loan_debt": "💳", "other": "📦",
}

FINANCIAL_GOALS = [
    "Save money",
    "Build an emergency fund",
    "Pay off debt",
    "Vacation",
    "Start a business",
    "Improve budgeting",
]

CURRENCIES = {
    "PKR": "Rs ", "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹",
    "AED": "AED ", "SAR": "SAR ", "CAD": "C$", "AUD": "A$",
}

SCORE_BANDS = [
    (80, "Strong", "#22c55e"),
    (60, "Generally healthy", "#84cc16"),
    (40, "Needs improvement", "#f59e0b"),
    (0, "High attention", "#ef4444"),
]

# Animated colour themes: accent colours + gradient stops
PALETTES = {
    "Aurora": {"a": "#7c3aed", "b": "#06b6d4", "c": "#22d3ee"},
    "Sunset": {"a": "#f97316", "b": "#ec4899", "c": "#facc15"},
    "Ocean": {"a": "#0ea5e9", "b": "#2563eb", "c": "#2dd4bf"},
    "Emerald": {"a": "#10b981", "b": "#14b8a6", "c": "#a3e635"},
    "Rose": {"a": "#e11d48", "b": "#a855f7", "c": "#fb7185"},
}

# Ready-made inputs for the five testing scenarios in the assignment
TEST_SCENARIOS = {
    "1 - High income, low expenses": dict(
        income=8000, savings=2500, housing=800, food=400, transportation=200,
        utilities=150, education=100, healthcare=100, entertainment=100,
        shopping=100, loan_debt=0, other=50),
    "2 - Overspending": dict(
        income=2000, savings=0, housing=900, food=500, transportation=250,
        utilities=200, education=100, healthcare=100, entertainment=150,
        shopping=150, loan_debt=200, other=50),
    "3 - Heavy debt": dict(
        income=5000, savings=300, housing=900, food=500, transportation=200,
        utilities=150, education=0, healthcare=100, entertainment=100,
        shopping=100, loan_debt=2500, other=50),
    "4 - Strong saver": dict(
        income=4000, savings=1200, housing=900, food=450, transportation=200,
        utilities=150, education=50, healthcare=100, entertainment=100,
        shopping=100, loan_debt=0, other=50),
    "5 - Break-even": dict(
        income=3000, savings=0, housing=1000, food=500, transportation=250,
        utilities=200, education=100, healthcare=150, entertainment=200,
        shopping=200, loan_debt=300, other=100),
}
