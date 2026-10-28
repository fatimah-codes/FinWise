"""Prompts: PromptTemplate, ChatPromptTemplate and the JSON schema."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# ---------------------------------------------------------------- system role
SYSTEM_PROMPT = """You are FinWise AI, an educational personal-finance assistant.

SAFETY RULES (always follow):
1. This is for EDUCATION ONLY. You are not a financial advisor.
2. Never guarantee any financial outcome, return or result.
3. Never recommend specific stocks, funds, crypto or other investment products.
4. Never ask for or mention bank account numbers, card numbers or passwords.
5. You cannot execute transactions; only explain and suggest budgeting habits.
6. Use only the numbers given to you. Do not invent figures.
7. Be kind, clear and practical. Remind the user to consult a qualified
   financial professional for real decisions."""

# ---------------------------------------------------------------- JSON schema
JSON_SCHEMA = """{
  "financial_summary": "2-4 sentence plain-language summary",
  "financial_health_score": 0,
  "spending_analysis": [
    {"category": "", "observation": "", "recommendation": ""}
  ],
  "risk_level": "LOW | MEDIUM | HIGH",
  "top_priorities": [],
  "budget_recommendations": [],
  "savings_strategy": [],
  "next_month_action_plan": []
}"""

SCORE_GUIDE = (
    "Score bands: 80-100 strong, 60-79 generally healthy, "
    "40-59 needs improvement, below 40 high attention."
)

# ---------------------------------------------------------------- PromptTemplate
# One reusable single-string template carrying every required variable.
FINANCIAL_PROMPT = PromptTemplate(
    input_variables=[
        "monthly_income", "total_expenses", "remaining_income", "savings",
        "savings_ratio", "expense_ratio", "financial_goal", "expense_breakdown",
        "currency", "preliminary_score", "debt_ratio", "json_schema",
    ],
    template="""Analyse this person's monthly finances for educational purposes.

Currency: {currency}
Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current monthly savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Debt payments as % of income: {debt_ratio}%
Rule-based preliminary score (calculated by Python): {preliminary_score}/100
Financial goal: {financial_goal}

Expense breakdown:
{expense_breakdown}

Return ONLY valid JSON that matches this exact schema (no markdown, no extra text):
{json_schema}
""",
)

# ---------------------------------------------------------------- ChatPromptTemplate (analysis)
HUMAN_ANALYSIS_TEMPLATE = (
    "Here is the user's data, already calculated by Python:\n\n"
    "Currency: {currency}\n"
    "Monthly income: {monthly_income}\n"
    "Total expenses: {total_expenses}\n"
    "Remaining income: {remaining_income}\n"
    "Current monthly savings: {savings}\n"
    "Savings ratio: {savings_ratio}%\n"
    "Expense ratio: {expense_ratio}%\n"
    "Debt payments as % of income: {debt_ratio}%\n"
    "Preliminary rule-based score: {preliminary_score}/100\n"
    "Financial goal: {financial_goal}\n\n"
    "Expense breakdown:\n{expense_breakdown}\n\n"
    "Respond with ONLY valid JSON using this exact schema:\n{json_schema}\n\n"
    + SCORE_GUIDE
)

ANALYSIS_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_ANALYSIS_TEMPLATE),
])

# ---------------------------------------------------------------- ChatPromptTemplate (streamed narrative)
HUMAN_NARRATIVE_TEMPLATE = (
    "Write a friendly monthly recommendation (about 250-350 words) in plain text "
    "with short paragraphs and a few bullet points, for educational purposes.\n"
    "Cover: what is going well, the biggest concern, 3 concrete budgeting steps for "
    "next month, and one habit to build toward the goal '{financial_goal}'.\n\n"
    "Facts (Python-calculated):\n"
    "Income {monthly_income}, expenses {total_expenses}, remaining {remaining_income}, "
    "savings {savings} ({savings_ratio}% of income), expense ratio {expense_ratio}%, "
    "debt {debt_ratio}% of income, currency {currency}.\n"
    "Expense breakdown:\n{expense_breakdown}\n\n"
    "End with one sentence reminding the reader this is educational and not financial advice."
)

NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_NARRATIVE_TEMPLATE),
])

# Every variable the chat templates need (used by chains.py)
TEMPLATE_VARIABLES = [
    "monthly_income", "total_expenses", "remaining_income", "savings",
    "savings_ratio", "expense_ratio", "financial_goal", "expense_breakdown",
    "currency", "preliminary_score", "debt_ratio", "json_schema",
]
