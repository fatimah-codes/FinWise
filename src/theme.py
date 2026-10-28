"""Animated theme: CSS variables, gradient blobs, smooth light/dark transitions."""
from src.config import PALETTES

MODES = {
    "Dark": {
        "bg": "#0a0f1f", "sidebar": "rgba(14,20,40,0.82)", "text": "#e8ecf8",
        "muted": "#9aa6c7", "card": "rgba(255,255,255,0.06)",
        "border": "rgba(255,255,255,0.13)", "input": "#1a2242",
        "pop": "#141b33", "shadow": "rgba(0,0,0,0.45)", "blob": "0.38",
    },
    "Light": {
        "bg": "#f3f5ff", "sidebar": "rgba(255,255,255,0.85)", "text": "#121830",
        "muted": "#56607f", "card": "rgba(255,255,255,0.78)",
        "border": "rgba(20,30,70,0.13)", "input": "#ffffff",
        "pop": "#ffffff", "shadow": "rgba(40,50,110,0.18)", "blob": "0.30",
    },
}

PIE_COLORS = ["#7c3aed", "#06b6d4", "#f97316", "#22c55e", "#ec4899",
              "#eab308", "#3b82f6", "#ef4444", "#14b8a6", "#a855f7"]


def build_css(mode: str, palette: str) -> str:
    m = MODES.get(mode, MODES["Dark"])
    p = PALETTES.get(palette, PALETTES["Aurora"])
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Registered colour properties so the palette cross-fades smoothly */
@property --a {{ syntax: '<color>'; inherits: true; initial-value: #7c3aed; }}
@property --b {{ syntax: '<color>'; inherits: true; initial-value: #06b6d4; }}
@property --c {{ syntax: '<color>'; inherits: true; initial-value: #22d3ee; }}
@property --bg {{ syntax: '<color>'; inherits: true; initial-value: #0a0f1f; }}
@property --text {{ syntax: '<color>'; inherits: true; initial-value: #e8ecf8; }}

:root {{
  --a: {p['a']}; --b: {p['b']}; --c: {p['c']};
  --bg: {m['bg']}; --text: {m['text']}; --muted: {m['muted']};
  --card: {m['card']}; --border: {m['border']}; --input: {m['input']};
  --pop: {m['pop']}; --shadow: {m['shadow']}; --sidebar: {m['sidebar']};
  --blob: {m['blob']};
  transition: --a .9s ease, --b .9s ease, --c .9s ease, --bg .9s ease, --text .9s ease;
}}

html, body, .stApp, .stApp * {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
/* Icons must keep their own font, otherwise the ligature name (e.g. "arrow_right")
   is printed as plain text on top of the label. Monospace stays monospace. */
.stApp [data-testid="stIconMaterial"], .stApp .material-icons,
.stApp [class*="material-symbols"] {{
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}}
.stApp code, .stApp pre, .stApp pre *, .stApp code * {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important;
}}

.stApp {{ background-color: var(--bg); color: var(--text); }}

/* Drifting colour blobs behind everything */
.stApp::before {{
  content: ""; position: fixed; inset: -10%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(520px circle at 12% 18%, color-mix(in srgb, var(--a) calc(var(--blob) * 100%), transparent), transparent 62%),
    radial-gradient(620px circle at 88% 12%, color-mix(in srgb, var(--b) calc(var(--blob) * 100%), transparent), transparent 62%),
    radial-gradient(700px circle at 55% 105%, color-mix(in srgb, var(--c) calc(var(--blob) * 100%), transparent), transparent 62%);
  animation: drift 20s ease-in-out infinite alternate;
}}
@keyframes drift {{
  0%   {{ transform: translate3d(0,0,0) scale(1); }}
  50%  {{ transform: translate3d(2%, -2%, 0) scale(1.06); }}
  100% {{ transform: translate3d(-2%, 2%, 0) scale(1.02); }}
}}

[data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {{
  background: transparent; position: relative; z-index: 1;
}}
[data-testid="stSidebar"] {{
  background: var(--sidebar); backdrop-filter: blur(18px);
  border-right: 1px solid var(--border); z-index: 2;
  transition: background .8s ease;
}}

/* Sidebar must scroll when its content is taller than the window */
[data-testid="stSidebar"] {{ height: 100vh; }}
[data-testid="stSidebar"] > div:first-child, [data-testid="stSidebarContent"] {{
  height: 100vh !important; max-height: 100vh !important;
  overflow-y: auto !important; overflow-x: hidden !important;
}}
[data-testid="stSidebarUserContent"] {{ padding-bottom: 4rem; }}
[data-testid="stSidebarContent"]::-webkit-scrollbar {{ width: 8px; }}
[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 8px; }}

/* Text colours (inline styles on my own HTML still win) */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"] p, label, h1, h2, h3, h4, h5,
[data-testid="stMetricValue"], [data-testid="stExpander"] summary p,
.stTabs [data-baseweb="tab"] p {{ color: var(--text); transition: color .8s ease; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {{ color: var(--text) !important; }}
[data-testid="stCaptionContainer"], [data-testid="stMetricLabel"] p {{ color: var(--muted) !important; }}
[data-testid="stAlert"] * {{ color: var(--text); }}

/* Hero title */
.fw-hero {{ text-align: center; padding: 1.2rem 0 .4rem; animation: fadeUp .8s both; }}
.stApp .fw-hero h1 {{
  font-size: clamp(2.2rem, 5vw, 3.6rem); font-weight: 800; margin: 0;
  background: linear-gradient(90deg, var(--a), var(--b), var(--c), var(--a));
  background-size: 300% 100%; -webkit-background-clip: text; background-clip: text;
  color: transparent !important; -webkit-text-fill-color: transparent;
  animation: shine 7s linear infinite;
}}
.stApp .fw-hero p {{ color: var(--muted) !important; }}
.stApp .fw-card h4, .stApp .fw-card p {{ color: var(--text) !important; }}
.stApp .fw-badge, .stApp .fw-badge * {{ color: #fff !important; }}
.stApp .fw-pill {{ color: var(--muted) !important; }}
.stApp .fw-hero p {{ color: var(--muted); margin: .3rem 0 0; font-size: 1.05rem; }}
.fw-coin {{ display: inline-block; font-size: 2.6rem; animation: bob 3s ease-in-out infinite; }}
@keyframes shine {{ to {{ background-position: 300% 0; }} }}
@keyframes bob {{ 0%,100% {{ transform: translateY(0) rotate(-6deg); }} 50% {{ transform: translateY(-10px) rotate(6deg); }} }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(18px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes pop {{ 0% {{ transform: scale(.85); opacity: 0; }} 100% {{ transform: scale(1); opacity: 1; }} }}

/* Cards */
.fw-card {{
  background: var(--card); border: 1px solid var(--border); border-radius: 20px;
  padding: 1.1rem 1.3rem; backdrop-filter: blur(16px); margin-bottom: .9rem;
  box-shadow: 0 10px 30px -14px var(--shadow); animation: fadeUp .6s both;
  transition: transform .25s ease, box-shadow .25s ease, background .8s ease, border-color .8s ease;
}}
.fw-card:hover {{ transform: translateY(-3px); box-shadow: 0 18px 40px -14px var(--shadow); }}
.stApp .fw-card h4 {{ margin: 0 0 .5rem; }}
.stApp .fw-card ul {{ margin: .2rem 0 0 1.1rem; padding: 0; }}
.stApp .fw-card li {{ margin-bottom: .35rem; color: var(--text); }}

.fw-gate {{ max-width: 560px; margin: 1.2rem auto; }}
.stApp .fw-badge {{
  display: inline-block; padding: .25rem .8rem; border-radius: 999px; font-weight: 700;
  font-size: .85rem; color: #fff; animation: pop .5s both;
}}
.stApp .fw-pill {{
  display: inline-block; padding: .2rem .7rem; border-radius: 999px; font-size: .8rem;
  border: 1px solid var(--border); background: var(--card); color: var(--muted); margin-right: .3rem;
}}
.fw-disclaimer {{
  border-left: 4px solid #f59e0b; background: rgba(245,158,11,.12);
  padding: .6rem .9rem; border-radius: 10px; font-size: .85rem; color: var(--text);
  animation: fadeUp .6s both;
}}

/* Animated score ring */
.fw-ring {{ width: 190px; height: 190px; display: block; margin: 0 auto; }}
.fw-ring .bg {{ fill: none; stroke: var(--border); stroke-width: 12; }}
.fw-ring .fg {{
  fill: none; stroke-width: 12; stroke-linecap: round; stroke-dasharray: 339.29;
  stroke-dashoffset: var(--off); transform: rotate(-90deg); transform-origin: 70px 70px;
  animation: ringIn 1.7s cubic-bezier(.2,.8,.2,1) both;
  filter: drop-shadow(0 0 6px currentColor);
}}
.fw-ring text {{ fill: var(--text); font-weight: 800; }}
@keyframes ringIn {{ from {{ stroke-dashoffset: 339.29; }} }}

/* Metrics */
[data-testid="stMetric"] {{
  background: var(--card); border: 1px solid var(--border); border-radius: 18px;
  padding: 14px 18px; backdrop-filter: blur(14px); animation: fadeUp .6s both;
  transition: transform .25s ease, box-shadow .25s ease, background .8s ease;
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-3px); box-shadow: 0 14px 30px -14px var(--shadow); }}

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  background: linear-gradient(120deg, var(--a), var(--b), var(--c)); background-size: 220% 220%;
  color: #fff; border: 0; border-radius: 14px; font-weight: 700; padding: .55rem 1.1rem;
  transition: transform .2s ease, box-shadow .25s ease, background-position .7s ease;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
  background-position: 100% 100%; transform: translateY(-2px);
  box-shadow: 0 10px 24px -8px var(--a); color: #fff;
}}
.stButton > button:active, .stFormSubmitButton > button:active {{ transform: scale(.97); }}
.stButton > button p, .stFormSubmitButton > button p, .stDownloadButton > button p {{ color: #fff; }}

/* Widgets (inputs, selects, dropdowns, uploader) are left to Streamlit's native
   theme, which now matches the chosen mode, so nothing is forced here. */
.stApp [data-baseweb="input"]:focus-within, .stApp [data-baseweb="select"]:focus-within {{
  box-shadow: 0 0 0 2px var(--a) !important;
}}

[data-testid="stForm"], [data-testid="stExpander"] {{
  background: var(--card); border: 1px solid var(--border); border-radius: 18px;
  backdrop-filter: blur(12px); transition: background .8s ease;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; flex-wrap: wrap; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 12px 12px 0 0; transition: background .25s ease; }}
.stTabs [data-baseweb="tab"]:hover {{ background: var(--card); }}
.stTabs [data-baseweb="tab-highlight"] {{ background: linear-gradient(90deg, var(--a), var(--b)); height: 3px; }}
.stTabs [data-baseweb="tab-panel"] {{ animation: fadeUp .45s both; }}

/* Progress bars */
.stProgress > div > div > div > div {{ background: linear-gradient(90deg, var(--a), var(--c)); transition: width 1s ease; }}

hr {{ border-color: var(--border); }}
::selection {{ background: var(--a); color: #fff; }}
</style>
"""
