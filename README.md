# FinWise AI

AI-powered personal financial analysis and smart budget assistant.
Built with **LangChain + Streamlit + OpenAI**.

> Educational use only. Not financial advice. It never connects to a bank,
> moves money or guarantees any outcome.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

When the app opens it asks for your OpenAI API key first. The key is checked
with OpenAI, kept only in the browser session, and unlocks the console.
The field is never pre-filled: paste your key each session and press **Unlock**.

## Features

Required by the assignment:
- Form with income, 10 expense categories, savings, goal and currency
- Python-only maths (`financial_calculator.py`) with divide-by-zero guard
- `PromptTemplate`, `ChatPromptTemplate`, `SystemMessage / HumanMessage / AIMessage`
- Reusable `LLMChain` returning strict JSON, parsed safely with a fallback
- Streaming recommendation via `llm.stream()` + `st.write_stream()`, shown in a
  visible box above the tabs so you can watch it type
- In-Memory and SQLite caching, switchable in the sidebar
- Dashboard: metrics, progress bars, tabs, expanders, risk level, action plan
- Disclaimer on every screen, reset-session button

Extras:
- API-key gate before the console unlocks, lock button to remove the key
- Animated themes: dark/light (follows Streamlit's ⋮ > Settings > Theme), 5 colour palettes, drifting gradient, animated score ring
- Donut and bar charts, goal tracker, what-if sliders (pure Python)
- Month history and comparison, CSV import, HTML report and JSON download
- Developer console tab (filled prompt, raw JSON, message demo, timing, cache hit hint)
- Five test scenarios loadable from the sidebar
- Python score vs AI score cross-check

## Python vs AI

| Python (deterministic) | AI (LLM) |
|---|---|
| totals, remaining income, ratios, preliminary score | explanation, observations, priorities, plans |
| same input = same output | wording can vary a little |

The LLM receives the Python numbers and is told not to invent figures.
The dashboard shows both scores so you can spot disagreements.

## Caching

| | InMemoryCache | SQLiteCache |
|---|---|---|
| Stored in | RAM | `.finwise_cache.db` |
| Survives restart | No | Yes |
| Best for | one session | reuse across sessions |

`set_llm_cache()` registers one global cache. LangChain checks it before each
call, so the same prompt skips the API call (faster and cheaper). Streaming
output may bypass the cache depending on the LangChain version.

## Project structure

```
finwise_ai/
  app.py                    Streamlit UI
  requirements.txt  .env.example  README.md  .gitignore
  .streamlit/config.toml    Streamlit server + base theme
  src/
    config.py               settings, form options, test scenarios
    prompts.py              PromptTemplate, ChatPromptTemplate, JSON schema
    financial_calculator.py deterministic maths (no AI)
    chains.py               ChatOpenAI, LLMChain, messages demo, streaming
    cache_manager.py        in-memory + SQLite caching
    utils.py                safe JSON parsing and helpers
    theme.py                animated CSS themes
  docs/FinTech_AI_Assignment.pdf
```

Troubleshooting: if Light mode ever shows dark input boxes or text like
`arrow_right` on expanders, hard-refresh the browser (Ctrl+Shift+R) so the
updated CSS in `src/theme.py` is loaded.

Note: the PDF names nine expense categories but asks for ten, so
"Shopping & Subscriptions" was added as the tenth.

## Testing scenarios

Load them from the sidebar. Python results:

| # | Income | Expenses | Remaining | Python score |
|---|---|---|---|---|
| 1 | 8000 | 2000 | 6000 | 100 (LOW) |
| 2 | 2000 | 2600 | -600 | 20 (HIGH) |
| 3 | 5000 | 4600 (debt 2500) | 400 | 23 (HIGH) |
| 4 | 4000 | 2100 (savings 1200) | 1900 | 99 (LOW) |
| 5 | 3000 | 3000 | 0 | 20 (HIGH) |
