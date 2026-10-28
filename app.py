"""FinWise AI - Streamlit UI. Run with:  streamlit run app.py

Flow: API-key gate -> unlocked console -> form -> Python maths -> LangChain
LLMChain (JSON) -> dashboard -> streamed recommendation.
"""
from __future__ import annotations

import datetime as dt
import html
import io
import json

import altair as alt
import pandas as pd
import streamlit as st

from src import config as C
from src.cache_manager import clear_cache, configure_cache, sqlite_size_kb
from src.chains import (build_inputs, build_llm, build_llmchain, message_demo,
                        render_single_string_prompt, run_analysis,
                        stream_recommendations, validate_key)
from src.financial_calculator import (band_color, calculate, goal_tracker,
                                      score_band, what_if)
from src.theme import MODES, PIE_COLORS, build_css
from src.utils import fallback_analysis, looks_like_key, mask_key, money, safe_parse_json

st.set_page_config(page_title=C.APP_NAME, page_icon="💸", layout="wide")

RISK_COLORS = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#ef4444"}


# ============================================================ state helpers
def native_mode() -> str:
    """Light/Dark as chosen in Streamlit's own Settings (falls back to Dark)."""
    try:
        return "Light" if st.context.theme.type == "light" else "Dark"
    except Exception:
        return "Dark"


THEME_PRESETS = {
    "Light": {"theme.base": "light", "theme.backgroundColor": "#f3f5ff",
              "theme.secondaryBackgroundColor": "#e8ebfb", "theme.textColor": "#121830"},
    "Dark": {"theme.base": "dark", "theme.backgroundColor": "#0a0f1f",
             "theme.secondaryBackgroundColor": "#1a2242", "theme.textColor": "#e8ecf8"},
}


def apply_native_theme() -> None:
    """Switch Streamlit's own theme so inputs, dropdowns and popups change too.

    Streamlit has no official API for this, so we set the theme config options and
    the rerun that follows the radio click pushes them to the browser. The setting
    is process-wide, which is fine for a local single-user app.
    """
    for key, value in THEME_PRESETS[st.session_state.theme_mode].items():
        st._config.set_option(key, value)


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("api_key", "")
    ss.setdefault("key_ok", False)
    ss.setdefault("theme_mode", native_mode())
    ss.setdefault("palette", "Aurora")
    ss.setdefault("model", C.DEFAULT_MODEL)
    ss.setdefault("temperature", C.DEFAULT_TEMPERATURE)
    ss.setdefault("cache_mode", "In-Memory")
    ss.setdefault("result", None)
    ss.setdefault("history", [])
    # form defaults
    ss.setdefault("f_income", 0.0)
    ss.setdefault("f_savings", 0.0)
    ss.setdefault("f_goal", C.FINANCIAL_GOALS[0])
    ss.setdefault("f_currency", "USD")
    ss.setdefault("f_label", dt.date.today().strftime("%B %Y"))
    ss.setdefault("f_goal_amount", 0.0)
    ss.setdefault("f_goal_months", 12)
    for key in C.EXPENSE_CATEGORIES:
        ss.setdefault(f"e_{key}", 0.0)


def load_scenario(name: str) -> None:
    data = C.TEST_SCENARIOS[name]
    st.session_state["f_income"] = float(data["income"])
    st.session_state["f_savings"] = float(data["savings"])
    for key in C.EXPENSE_CATEGORIES:
        st.session_state[f"e_{key}"] = float(data.get(key, 0))
    st.session_state["result"] = None


def reset_session() -> None:
    """Clear everything except the unlocked key and theme choices."""
    keep = {k: st.session_state[k] for k in
            ("api_key", "key_ok", "theme_mode", "palette", "model",
             "temperature", "cache_mode") if k in st.session_state}
    st.session_state.clear()
    st.session_state.update(keep)
    init_state()


def lock_console() -> None:
    st.session_state.clear()
    init_state()


# ============================================================ UI pieces
def disclaimer() -> None:
    st.markdown(f"<div class='fw-disclaimer'>⚠️ {html.escape(C.DISCLAIMER)}</div>",
                unsafe_allow_html=True)


def hero(subtitle: str) -> None:
    st.markdown(
        f"<div class='fw-hero'><span class='fw-coin'>💸</span>"
        f"<h1>{C.APP_NAME}</h1><p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True)


def score_ring(score: int, color: str) -> str:
    offset = 339.29 * (1 - max(0, min(100, score)) / 100)
    return (
        f"<svg class='fw-ring' viewBox='0 0 140 140'>"
        f"<circle class='bg' cx='70' cy='70' r='54'/>"
        f"<circle class='fg' cx='70' cy='70' r='54' stroke='{color}' "
        f"style='--off:{offset:.2f};color:{color}'/>"
        f"<text x='70' y='76' text-anchor='middle' font-size='34'>{score}</text>"
        f"<text x='70' y='96' text-anchor='middle' font-size='10' "
        f"style='opacity:.65'>out of 100</text></svg>")


def card(title: str, items: list[str], icon: str = "") -> None:
    if not items:
        items = ["No items returned."]
    lis = "".join(f"<li>{html.escape(str(i))}</li>" for i in items)
    st.markdown(f"<div class='fw-card'><h4>{icon} {html.escape(title)}</h4><ul>{lis}</ul></div>",
                unsafe_allow_html=True)


def style_chart(chart: alt.Chart) -> alt.Chart:
    m = MODES[st.session_state.theme_mode]
    txt = m["text"]
    return (chart.configure(background="rgba(0,0,0,0)")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=txt, titleColor=txt, gridColor="rgba(128,128,128,.2)",
                            domainColor="rgba(128,128,128,.4)")
            .configure_legend(labelColor=txt, titleColor=txt))


def sidebar() -> None:
    ss = st.session_state
    with st.sidebar:
        st.markdown(f"### 💸 {C.APP_NAME}")
        st.caption(f"v{C.APP_VERSION} · LangChain + Streamlit")
        st.markdown("<span class='fw-pill'>Educational</span><span class='fw-pill'>No real money</span>",
                    unsafe_allow_html=True)
        st.divider()

        st.markdown("**🎨 Appearance**")
        st.radio("Mode", ["Dark", "Light"], key="theme_mode", horizontal=True,
                 label_visibility="collapsed", on_change=apply_native_theme)
        st.selectbox("Colour palette", list(C.PALETTES), key="palette")

        if ss.key_ok:
            st.divider()
            st.markdown("**🤖 Model settings**")
            st.selectbox("Model", C.MODELS, key="model")
            st.slider("Temperature", 0.0, 1.0, step=0.05, key="temperature",
                      help="Lower = more consistent answers.")
            st.markdown("**⚡ Cache**")
            st.radio("Cache type", C.CACHE_OPTIONS, key="cache_mode", horizontal=True,
                     label_visibility="collapsed",
                     help="In-Memory: RAM, gone on restart. SQLite: file on disk, survives restarts.")
            st.caption(configure_cache(ss.cache_mode))
            if ss.cache_mode == "SQLite":
                st.caption(f"Cache file size: {sqlite_size_kb():.1f} KB")
            if ss.cache_mode != "None" and st.button("Clear cache", key="clear_cache"):
                clear_cache(ss.cache_mode)
                st.toast("Cache cleared")

            st.divider()
            st.markdown("**🧪 Test scenarios**")
            scenario = st.selectbox("Scenario", list(C.TEST_SCENARIOS), label_visibility="collapsed",
                                    key="scenario_pick")
            st.button("Load scenario into form", on_click=load_scenario, args=(scenario,))

            st.divider()
            st.caption(f"🔑 Key: `{mask_key(ss.api_key)}` (this session only)")
            c1, c2 = st.columns(2)
            c1.button("Reset", on_click=reset_session, help="Clear inputs and results")
            c2.button("Lock", on_click=lock_console, help="Remove the key and lock the console")

        st.divider()
        st.markdown("**ℹ️ Project info**")
        st.caption("Python does the maths. The AI explains it. "
                   "Nothing here moves money or connects to a bank.")
        st.markdown(f"<div class='fw-disclaimer'>⚠️ {html.escape(C.DISCLAIMER)}</div>",
                    unsafe_allow_html=True)


# ============================================================ API key gate
def key_gate() -> None:
    hero("Enter your OpenAI API key to unlock the console")
    # Streamlit cannot wrap widgets in a raw <div>, so centre with columns instead.
    _, mid, _ = st.columns([1, 2, 1])
    with mid, st.container(border=True):
        st.markdown("#### 🔐 Unlock the console")
        st.caption("Your key is checked with OpenAI, kept only in this browser session "
                   "and never written to disk.")
        # Never pre-fill from .env: the user types/pastes the key on purpose.
        key = st.text_input("OpenAI API key", type="password", placeholder="sk-...",
                            autocomplete="off", key="gate_key_input")
        if st.button("Unlock console 🚀"):
            key = (key or "").strip()
            if not looks_like_key(key):
                st.error("That does not look like an OpenAI key (it should start with sk-).")
            else:
                with st.spinner("Checking your key with OpenAI..."):
                    ok, msg = validate_key(key)
                if ok:
                    st.session_state.api_key = key
                    st.session_state.key_ok = True
                    st.session_state.pop("gate_key_input", None)
                    st.toast("Console unlocked ✨")
                    st.rerun()
                else:
                    st.error(msg)
        st.caption("No key yet? Create one at platform.openai.com. "
                   "Using the API may cost a small amount; gpt-4o-mini is very cheap.")
    disclaimer()


# ============================================================ CSV import
def parse_csv(file) -> tuple[dict, str]:
    """Read a CSV with columns category,amount. Returns (values, message)."""
    try:
        df = pd.read_csv(file)
    except Exception as exc:
        return {}, f"Could not read the CSV: {exc}"
    df.columns = [str(c).strip().lower() for c in df.columns]
    if not {"category", "amount"} <= set(df.columns):
        return {}, "CSV needs the columns: category, amount"
    out, unknown = {}, []
    labels = {k: v.lower() for k, v in C.EXPENSE_CATEGORIES.items()}
    aliases = {"rent": "housing", "house": "housing", "home": "housing", "mortgage": "housing",
               "groceries": "food", "transport": "transportation", "bills": "utilities",
               "school": "education", "tuition": "education", "health": "healthcare",
               "medical": "healthcare", "subscriptions": "shopping", "loan": "loan_debt",
               "debt": "loan_debt", "loans": "loan_debt", "misc": "other"}
    for _, row in df.iterrows():
        name = str(row["category"]).strip().lower()
        try:
            amount = float(row["amount"])
        except (TypeError, ValueError):
            continue
        if not name or name == "nan" or amount != amount:  # blank row / NaN amount
            continue
        if name in ("income", "monthly income"):
            out["income"] = amount
        elif name in ("savings", "monthly savings", "current savings"):
            out["savings"] = amount
        else:
            match = aliases.get(name) or next(
                (k for k, lab in labels.items()
                 if name == k or name == lab or name.split()[0] in lab.split()), None)
            if match:
                out[match] = out.get(match, 0.0) + amount
            else:
                unknown.append(name)
    msg = f"Loaded {len(out)} values."
    if unknown:
        msg += f" Ignored: {', '.join(unknown)}."
    return out, msg


def csv_import() -> None:
    with st.expander("📂 Import from CSV (optional)"):
        sample = "category,amount\nincome,4000\nsavings,500\nhousing,1000\nfood,450\ntransportation,200\n"
        st.download_button("Download sample CSV", sample, "sample_expenses.csv", "text/csv")
        up = st.file_uploader("Upload a CSV with columns: category, amount", type="csv")
        if up is not None and st.button("Apply CSV to form"):
            values, msg = parse_csv(up)
            if not values:
                st.error(msg)
            else:
                if "income" in values:
                    st.session_state["f_income"] = values.pop("income")
                if "savings" in values:
                    st.session_state["f_savings"] = values.pop("savings")
                for k, v in values.items():
                    st.session_state[f"e_{k}"] = float(v)
                st.toast(msg)
                st.rerun()


# ============================================================ input form
def input_form() -> bool:
    csv_import()
    with st.form("fin_form"):
        t1, t2, t3 = st.tabs(["💰 Income & savings", "🧾 Expenses", "🎯 Goal"])
        with t1:
            c1, c2, c3 = st.columns(3)
            c1.number_input("Monthly income", min_value=0.0, step=100.0, format="%.2f", key="f_income")
            c2.number_input("Current monthly savings", min_value=0.0, step=50.0, format="%.2f", key="f_savings")
            c3.selectbox("Currency", list(C.CURRENCIES), key="f_currency")
            st.text_input("Label for this month", key="f_label",
                          help="Used in history and the month comparison.")
        with t2:
            cols = st.columns(3)
            for i, (key, label) in enumerate(C.EXPENSE_CATEGORIES.items()):
                cols[i % 3].number_input(f"{C.EXPENSE_ICONS[key]} {label}", min_value=0.0,
                                         step=25.0, format="%.2f", key=f"e_{key}")
        with t3:
            st.selectbox("Financial goal", C.FINANCIAL_GOALS, key="f_goal")
            g1, g2 = st.columns(2)
            g1.number_input("Goal target amount (optional)", min_value=0.0, step=100.0,
                            format="%.2f", key="f_goal_amount",
                            help="Used by the goal tracker tab.")
            g2.number_input("Months to reach it", min_value=1, max_value=240, step=1, key="f_goal_months")
        return st.form_submit_button("Analyse my finances ✨")


# ============================================================ analysis flow
def run_flow() -> None:
    ss = st.session_state
    expenses = {k: ss[f"e_{k}"] for k in C.EXPENSE_CATEGORIES}
    calc = calculate(ss.f_income, expenses, ss.f_savings)
    if calc["income_is_zero"]:
        st.warning("Please enter a monthly income above 0 to run the analysis.")
        return

    if calc["savings"] > max(0.0, calc["remaining_income"]):
        st.warning("Your monthly savings are higher than the income left after expenses. "
                   "Check the numbers: savings should come out of the money that remains.")

    currency = ss.f_currency
    symbol = C.CURRENCIES[currency]
    inputs = build_inputs(calc, ss.f_goal, currency, symbol)
    configure_cache(ss.cache_mode)

    raw, seconds, error = "", 0.0, None
    try:
        llm = build_llm(ss.api_key, ss.model, ss.temperature, json_mode=True)
        chain = build_llmchain(llm)
        with st.spinner("Python finished the maths. The AI is reviewing it..."):
            raw, seconds = run_analysis(chain, inputs)
    except Exception as exc:
        error = friendly_error(exc)

    analysis = None
    if raw:
        analysis, parse_error = safe_parse_json(raw)
        if parse_error:
            error = parse_error if analysis else f"{parse_error} Showing a rule-based summary instead."
    if analysis is None:
        analysis = fallback_analysis(calc, ss.f_goal)

    result = {
        "calc": calc, "analysis": analysis, "raw": raw, "seconds": seconds,
        "inputs": inputs, "currency": currency, "goal": ss.f_goal,
        "label": ss.f_label, "model": ss.model, "error": error,
        "ai_ok": bool(raw) and not (error and "Showing a rule-based" in error),
        "need_stream": error is None or bool(raw),
        "narrative": "", "cache_mode": ss.cache_mode,
        "goal_amount": ss.f_goal_amount, "goal_months": int(ss.f_goal_months),
    }
    ss.result = result
    ss.history.append({
        "label": ss.f_label, "time": dt.datetime.now().strftime("%d %b %H:%M"),
        "currency": currency, "income": calc["monthly_income"],
        "expenses": calc["total_expenses"], "remaining": calc["remaining_income"],
        "savings": calc["savings"], "ai_score": analysis["financial_health_score"],
        "py_score": calc["preliminary_score"], "risk": analysis["risk_level"],
    })


def friendly_error(exc: Exception) -> str:
    name = type(exc).__name__
    text = str(exc)
    if name == "AuthenticationError":
        return "OpenAI rejected the key. Use the Lock button in the sidebar and enter a valid key."
    if name == "RateLimitError":
        return "Rate limit or quota reached on your OpenAI account. Wait a moment or check billing."
    if name in ("APIConnectionError", "APITimeoutError"):
        return "Could not reach OpenAI. Check your internet connection and try again."
    if name == "NotFoundError":
        return "This model is not available for your key. Pick another model in the sidebar."
    return f"{name}: {text[:200]}"


# ============================================================ dashboard
def overview_tab(res: dict) -> None:
    calc, cur = res["calc"], res["currency"]
    st.markdown("<span class='fw-pill'>🧮 Calculated by Python - no AI</span>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    r1.metric("Savings ratio", f"{calc['savings_ratio']:.1f}%")
    r1.progress(min(1.0, calc["savings_ratio"] / 100))
    r2.metric("Expense ratio", f"{calc['expense_ratio']:.1f}%")
    r2.progress(min(1.0, calc["expense_ratio"] / 100))
    r3.metric("Debt share of income", f"{calc['debt_ratio']:.1f}%")
    r3.progress(min(1.0, calc["debt_ratio"] / 100))

    rows = [r for r in calc["breakdown"] if r["amount"] > 0]
    if not rows:
        st.info("Add some expenses to see charts.")
        return
    df = pd.DataFrame(rows)
    left, right = st.columns(2)
    with left:
        st.markdown("##### Where the money goes")
        donut = (alt.Chart(df).mark_arc(innerRadius=62, outerRadius=125, stroke="rgba(0,0,0,0)")
                 .encode(theta="amount:Q",
                         color=alt.Color("category:N", scale=alt.Scale(range=PIE_COLORS),
                                         legend=alt.Legend(title=None, orient="bottom", columns=2)),
                         tooltip=["category", alt.Tooltip("amount:Q", format=",.0f"),
                                  alt.Tooltip("pct_of_income:Q", title="% of income")])
                 .properties(height=330))
        st.altair_chart(style_chart(donut), width="stretch")
    with right:
        st.markdown("##### Biggest categories")
        bars = (alt.Chart(df).mark_bar(cornerRadiusEnd=6)
                .encode(x=alt.X("amount:Q", title=f"Amount ({cur})"),
                        y=alt.Y("category:N", sort="-x", title=None),
                        color=alt.Color("category:N", scale=alt.Scale(range=PIE_COLORS), legend=None),
                        tooltip=["category", alt.Tooltip("amount:Q", format=",.0f"),
                                 alt.Tooltip("pct_of_income:Q", title="% of income")])
                .properties(height=330))
        st.altair_chart(style_chart(bars), width="stretch")


def insights_tab(res: dict) -> None:
    an, calc = res["analysis"], res["calc"]
    score = an["financial_health_score"]
    color = band_color(score)
    risk = an["risk_level"]
    if not res["ai_ok"]:
        st.warning("These insights are rule-based because the AI answer was not available.")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"<div class='fw-card'>{score_ring(score, color)}"
                    f"<div style='text-align:center;margin-top:.4rem'>"
                    f"<span class='fw-badge' style='background:{color}'>{score_band(score)}</span></div>"
                    f"</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='fw-card'><h4>🧠 AI summary</h4>"
                    f"<p>{html.escape(an['financial_summary'] or 'No summary returned.')}</p>"
                    f"<span class='fw-badge' style='background:{RISK_COLORS[risk]}'>Risk: {risk}</span> "
                    f"<span class='fw-pill'>Python score {calc['preliminary_score']}/100</span>"
                    f"<span class='fw-pill'>AI score {score}/100</span></div>", unsafe_allow_html=True)
        st.progress(score / 100, text=f"Financial health score: {score}/100")

    # Sanity checks: compare the AI with the deterministic numbers
    if calc["remaining_income"] < 0 and risk == "LOW":
        st.error("Check: spending is above income but the AI said LOW risk. Trust the numbers first.")
    elif abs(score - calc["preliminary_score"]) > 25:
        st.warning("The AI score is far from the rule-based score. Read both with care.")
    if calc["remaining_income"] < 0:
        st.error(f"You spend {money(-calc['remaining_income'], res['currency'])} more than you earn each month.")
    elif calc["remaining_income"] == 0:
        st.warning("Nothing is left after expenses. There is no buffer for surprises.")

    card("Top priorities", an["top_priorities"], "🎯")


def spending_tab(res: dict) -> None:
    items = res["analysis"]["spending_analysis"]
    if not items:
        st.info("No category analysis was returned.")
    for i, it in enumerate(items):
        with st.expander(f"{it['category'] or 'Category'}", expanded=i == 0):
            st.markdown(f"**Observation:** {it['observation']}")
            st.success(f"💡 {it['recommendation']}")


def plan_tab(res: dict) -> None:
    an = res["analysis"]
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Budget recommendations", an["budget_recommendations"], "📒")
    with c2:
        card("Savings strategy", an["savings_strategy"], "🏦")
    with c3:
        st.markdown("<div class='fw-card'><h4>🗓️ Next-month action plan</h4></div>", unsafe_allow_html=True)
        for i, step in enumerate(an["next_month_action_plan"] or ["No steps returned."]):
            st.checkbox(step, key=f"plan_{res['label']}_{i}")


def recommendation_tab(res: dict) -> None:
    ss = st.session_state
    if res.get("need_stream"):
        try:
            llm = build_llm(ss.api_key, ss.model, ss.temperature, streaming=True)
            text = st.write_stream(stream_recommendations(llm, res["inputs"]))
            res["narrative"] = text if isinstance(text, str) else "".join(map(str, text))
        except Exception as exc:
            st.error(friendly_error(exc))
        res["need_stream"] = False
    elif res.get("narrative"):
        st.markdown(res["narrative"])
    else:
        st.info("No written recommendation is available for this run.")
    st.caption("Educational only. Not financial advice.")


def goal_tab(res: dict) -> None:
    calc, cur = res["calc"], res["currency"]
    st.markdown("##### 🎯 Goal tracker")
    g = goal_tracker(res["goal_amount"], res["goal_months"], calc["savings"], calc["remaining_income"])
    if not g["enabled"]:
        st.info("Add a goal target amount and months in the Goal tab of the form to see progress.")
    else:
        a, b, c = st.columns(3)
        a.metric("Needed per month", money(g["needed_per_month"], cur))
        b.metric("You save now", money(g["current_savings"], cur))
        c.metric("Months at current pace",
                 f"{g['months_at_current']:.1f}" if g["months_at_current"] else "never")
        st.progress(g["progress_pct"] / 100, text=f"{g['progress_pct']:.0f}% of the monthly amount needed")
        if g["on_track"]:
            st.success("At the current pace you would reach this goal in time.")
        else:
            st.warning("You would need to save more each month to reach the goal in time.")

    st.markdown("##### 🧪 What-if: trim some spending")
    top = [r for r in calc["breakdown"] if r["amount"] > 0 and r["key"] != "housing"][:4]
    if not top:
        st.info("Nothing to trim yet.")
        return
    cols = st.columns(len(top))
    cuts = {r["key"]: cols[i].slider(r["category"], 0, 50, 0, 5, format="%d%%", key=f"cut_{r['key']}")
            for i, r in enumerate(top)}
    sim = what_if(calc["monthly_income"], calc["expenses"], calc["savings"], cuts)
    m1, m2, m3 = st.columns(3)
    m1.metric("Extra saved per month", money(sim["freed"], cur))
    m2.metric("New remaining income", money(sim["remaining_income"], cur),
              delta=money(sim["remaining_income"] - calc["remaining_income"], cur))
    m3.metric("New Python score", f"{sim['preliminary_score']}/100",
              delta=sim["preliminary_score"] - calc["preliminary_score"])
    st.caption("Simulation uses the same Python formulas. No AI call is made here.")


def compare_tab() -> None:
    hist = st.session_state.history
    if not hist:
        st.info("Run an analysis to start your history.")
        return
    df = pd.DataFrame(hist)
    st.dataframe(df, hide_index=True, width="stretch")
    if len(hist) < 2:
        st.info("Run a second analysis (for example another month) to compare.")
        return
    labels = [f"{i + 1}. {h['label']} ({h['time']})" for i, h in enumerate(hist)]
    c1, c2 = st.columns(2)
    a = c1.selectbox("Earlier", labels, index=len(hist) - 2)
    b = c2.selectbox("Later", labels, index=len(hist) - 1)
    ha, hb = hist[labels.index(a)], hist[labels.index(b)]
    cols = st.columns(4)
    for col, (name, key) in zip(cols, [("Income", "income"), ("Expenses", "expenses"),
                                       ("Remaining", "remaining"), ("Savings", "savings")]):
        col.metric(name, f"{hb[key]:,.0f}", delta=f"{hb[key] - ha[key]:+,.0f}",
                   delta_color="inverse" if key == "expenses" else "normal")
    s1, s2 = st.columns(2)
    s1.metric("AI score", hb["ai_score"], delta=hb["ai_score"] - ha["ai_score"])
    s2.metric("Python score", hb["py_score"], delta=hb["py_score"] - ha["py_score"])
    chart = (alt.Chart(df.reset_index()).mark_line(point=True, strokeWidth=3)
             .encode(x=alt.X("index:O", title="Run"), y=alt.Y("ai_score:Q", title="AI score", scale=alt.Scale(domain=[0, 100])),
                     tooltip=["label", "ai_score", "py_score"]).properties(height=240))
    st.altair_chart(style_chart(chart), width="stretch")


def report_html(res: dict) -> str:
    an, calc, cur = res["analysis"], res["calc"], res["currency"]
    def ul(items): return "<ul>" + "".join(f"<li>{html.escape(str(i))}</li>" for i in items) + "</ul>"
    spend = "".join(f"<h4>{html.escape(s['category'])}</h4><p>{html.escape(s['observation'])}<br>"
                    f"<em>{html.escape(s['recommendation'])}</em></p>" for s in an["spending_analysis"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>FinWise AI report</title>
<style>body{{font-family:Arial,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#1b2140}}
h1{{color:#5b21b6}}.box{{background:#f3f0ff;padding:1rem;border-radius:12px}}
.warn{{background:#fff7e6;border-left:4px solid #f59e0b;padding:.7rem;margin-top:1.5rem}}</style></head><body>
<h1>FinWise AI - {html.escape(res['label'])}</h1>
<div class='box'><b>Income:</b> {money(calc['monthly_income'], cur)} &nbsp; <b>Expenses:</b> {money(calc['total_expenses'], cur)}
&nbsp; <b>Remaining:</b> {money(calc['remaining_income'], cur)} &nbsp; <b>Savings:</b> {money(calc['savings'], cur)}<br>
<b>Savings ratio:</b> {calc['savings_ratio']:.1f}% &nbsp; <b>Expense ratio:</b> {calc['expense_ratio']:.1f}%
&nbsp; <b>Python score:</b> {calc['preliminary_score']}/100</div>
<h2>AI health score: {an['financial_health_score']}/100 ({score_band(an['financial_health_score'])}) - Risk {an['risk_level']}</h2>
<p>{html.escape(an['financial_summary'])}</p>
<h3>Top priorities</h3>{ul(an['top_priorities'])}
<h3>Spending analysis</h3>{spend}
<h3>Budget recommendations</h3>{ul(an['budget_recommendations'])}
<h3>Savings strategy</h3>{ul(an['savings_strategy'])}
<h3>Next-month action plan</h3>{ul(an['next_month_action_plan'])}
<h3>Written recommendation</h3><p>{html.escape(res.get('narrative', '')).replace(chr(10), '<br>')}</p>
<div class='warn'>{html.escape(C.DISCLAIMER)}</div></body></html>"""


def console_tab(res: dict) -> None:
    st.caption("Developer console: see what Python sent to the model and what came back.")
    cached = res["cache_mode"] != "None" and res["seconds"] < 0.3 and res["ai_ok"]
    a, b, c, d = st.columns(4)
    a.metric("Model", res["model"])
    b.metric("Response time", f"{res['seconds']:.2f}s")
    c.metric("Cache", res["cache_mode"])
    d.metric("Cache hit?", "Likely" if cached else "No")
    if res["error"]:
        st.warning(res["error"])
    with st.expander("1. PromptTemplate (single-string, filled)"):
        st.code(render_single_string_prompt(res["inputs"]), language="text")
    with st.expander("2. System / Human / AI message demo"):
        for m in message_demo(res["inputs"], res["analysis"]["financial_summary"]):
            st.markdown(f"**{type(m).__name__}**")
            st.code(m.content, language="text")
    with st.expander("3. Raw model output"):
        st.code(res["raw"] or "(no output)", language="json")
    with st.expander("4. Parsed JSON"):
        st.json(res["analysis"])
    with st.expander("5. Python calculations"):
        st.json({k: v for k, v in res["calc"].items() if k not in ("breakdown", "expenses")})

    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download report (HTML)", report_html(res),
                       f"finwise_report_{res['label'].replace(' ', '_')}.html", "text/html")
    d2.download_button("⬇️ Download JSON", json.dumps(res["analysis"], indent=2),
                       "finwise_analysis.json", "application/json")


def dashboard(res: dict) -> None:
    calc, cur = res["calc"], res["currency"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 Monthly income", money(calc["monthly_income"], cur))
    m2.metric("🧾 Total expenses", money(calc["total_expenses"], cur))
    m3.metric("🧮 Remaining balance", money(calc["remaining_income"], cur),
              delta=f"{calc['remaining_income'] / calc['monthly_income'] * 100:+.1f}% of income",
              delta_color="normal")
    m4.metric("🏦 Current savings", money(calc["savings"], cur))

    if res["error"] and res["ai_ok"]:
        st.warning(res["error"])
    elif res["error"]:
        st.error(res["error"])

    st.markdown("##### ✍️ Written recommendation")
    rec_box = st.container(border=True)  # filled after the tabs so the page does not wait

    tabs = st.tabs(["📊 Overview", "🧠 AI insights", "🔍 Spending", "🗺️ Plan",
                    "🎯 Goal & what-if", "📈 Compare", "🛠️ Console"])
    with tabs[0]:
        overview_tab(res)
    with tabs[1]:
        insights_tab(res)
    with tabs[2]:
        spending_tab(res)
    with tabs[3]:
        plan_tab(res)
    with tabs[4]:
        goal_tab(res)
    with tabs[5]:
        compare_tab()
    with tabs[6]:
        console_tab(res)

    with rec_box:
        recommendation_tab(res)


# ============================================================ main
def main() -> None:
    init_state()
    st.markdown(build_css(st.session_state.theme_mode, st.session_state.palette),
                unsafe_allow_html=True)
    sidebar()

    if not st.session_state.key_ok:
        key_gate()
        return

    hero(C.APP_TAGLINE)
    disclaimer()
    st.write("")
    submitted = input_form()
    if submitted:
        run_flow()
    if st.session_state.result:
        st.divider()
        dashboard(st.session_state.result)
    else:
        st.info("Fill in the form above (or load a test scenario from the sidebar) and press Analyse.")
    st.write("")
    disclaimer()


main()