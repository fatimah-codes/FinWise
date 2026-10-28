"""ChatOpenAI, the reusable LLMChain, message demo and streaming."""
from __future__ import annotations

import time
import warnings
from typing import Dict, Iterator, Tuple

# LLMChain is required by the assignment but LangChain marks it deprecated.
warnings.filterwarnings("ignore", message=".*LLMChain.*")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.prompts import (ANALYSIS_CHAT_TEMPLATE, FINANCIAL_PROMPT, JSON_SCHEMA,
                         NARRATIVE_CHAT_TEMPLATE, SYSTEM_PROMPT)

# LLMChain moved between packages in newer LangChain versions.
try:  # langchain 0.x
    from langchain.chains import LLMChain
except Exception:  # pragma: no cover
    try:  # langchain 1.x legacy package
        from langchain_classic.chains import LLMChain
    except Exception:
        LLMChain = None


def build_llm(api_key: str, model: str, temperature: float,
              json_mode: bool = False, streaming: bool = False) -> ChatOpenAI:
    """Create the ChatOpenAI model. json_mode asks OpenAI for strict JSON."""
    kwargs = {}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(
        api_key=api_key, model=model, temperature=temperature,
        streaming=streaming, timeout=60, max_retries=2, **kwargs,
    )


def build_llmchain(llm):
    """Reusable chain: ChatPromptTemplate -> model.

    Uses LLMChain when available, otherwise the equivalent `prompt | llm` pipe.
    """
    if LLMChain is not None:
        try:
            return LLMChain(llm=llm, prompt=ANALYSIS_CHAT_TEMPLATE)
        except Exception:
            pass
    return ANALYSIS_CHAT_TEMPLATE | llm


def build_inputs(calc: Dict, goal: str, currency: str, symbol: str) -> Dict:
    """Turn the Python results into the template variables."""
    from src.financial_calculator import expense_breakdown_text
    return {
        "monthly_income": f"{symbol}{calc['monthly_income']:,.2f}",
        "total_expenses": f"{symbol}{calc['total_expenses']:,.2f}",
        "remaining_income": f"{symbol}{calc['remaining_income']:,.2f}",
        "savings": f"{symbol}{calc['savings']:,.2f}",
        "savings_ratio": f"{calc['savings_ratio']:.1f}",
        "expense_ratio": f"{calc['expense_ratio']:.1f}",
        "debt_ratio": f"{calc['debt_ratio']:.1f}",
        "preliminary_score": calc["preliminary_score"],
        "financial_goal": goal,
        "expense_breakdown": expense_breakdown_text(calc, symbol),
        "currency": currency,
        "json_schema": JSON_SCHEMA,
    }


def run_analysis(chain, inputs: Dict) -> Tuple[str, float]:
    """Run the chain once. Returns (raw_text, seconds)."""
    start = time.perf_counter()
    result = chain.invoke(inputs)
    seconds = time.perf_counter() - start
    if isinstance(result, dict):  # LLMChain output
        text = result.get("text", "")
    elif hasattr(result, "content"):  # AIMessage from the pipe version
        text = result.content
    else:
        text = str(result)
    return text, seconds


def stream_recommendations(llm, inputs: Dict) -> Iterator[str]:
    """Yield text chunks for st.write_stream()."""
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content


def message_demo(inputs: Dict, ai_reply: str = "") -> list:
    """Raw System / Human / AI messages, as the assignment asks.

    Shows how a conversation is represented without any template.
    """
    human = (
        f"My income is {inputs['monthly_income']} and my expenses are "
        f"{inputs['total_expenses']}. My goal: {inputs['financial_goal']}."
    )
    reply = ai_reply or "Thanks! Let me review your numbers and share educational budgeting ideas."
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human),
        AIMessage(content=reply),
    ]


def render_single_string_prompt(inputs: Dict) -> str:
    """Fill the PromptTemplate (single-string version) for display in the console."""
    return FINANCIAL_PROMPT.format(**inputs)


def validate_key(api_key: str) -> Tuple[bool, str]:
    """Check the key with a free models.list call (no tokens used)."""
    try:
        from openai import AuthenticationError, OpenAI, PermissionDeniedError, RateLimitError
        client = OpenAI(api_key=api_key, timeout=20, max_retries=1)
        client.models.list()
        return True, "Key accepted."
    except AuthenticationError:
        return False, "OpenAI rejected this key. Check it and try again."
    except PermissionDeniedError:
        return False, "This key does not have permission to list models."
    except RateLimitError:
        # A valid key can still be rate limited / out of quota
        return True, "Key accepted (note: rate limit or quota warning from OpenAI)."
    except Exception as exc:
        return False, f"Could not reach OpenAI: {type(exc).__name__}. Check your internet and key."
