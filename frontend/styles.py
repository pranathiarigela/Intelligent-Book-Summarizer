# frontend/styles.py
import streamlit as st
from textwrap import dedent

# FULL DARK THEME (professionally balanced)
PRIMARY = "#38bdf8"      # bright cyan accent (good contrast)
ACCENT = "#0ea5e9"
BG = "#0d1117"           # dark navy/black
CARD = "#161b22"         # GitHub-dark style cards
TEXT = "#e6edf3"
MUTED = "#9ca3af"
ERROR = "#f87171"
SUCCESS = "#34d399"
BORDER = "rgba(255,255,255,0.08)"

BASE_CSS = dedent(f"""
:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
  --bg: {BG};
  --card: {CARD};
  --text: {TEXT};
  --muted: {MUTED};
  --error: {ERROR};
  --success: {SUCCESS};
  --border: {BORDER};
  --radius-lg: 16px;
  --radius-md: 10px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --shadow-sm: 0 4px 14px rgba(0,0,0,0.4);
}}

html, body, .stApp {{
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial;
}}

.app-card, .auth-card {{
  background: var(--card);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  margin-bottom: var(--space-md);
}}

.panel {{
  background: var(--card);
  padding: var(--space-sm);
  border-radius: 8px;
  border: 1px solid var(--border);
}}

.hero {{
  padding: 36px;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, rgba(56,189,248,0.10), rgba(14,165,233,0.05));
  margin-bottom: var(--space-md);
}}

.helper {{
  color: var(--muted);
  font-size: 13px;
  margin-top: 6px;
}}

.field-error {{
  color: var(--error);
  margin-top: 8px;
  font-size: 13px;
}}

button.stButton > button {{
  border-radius: 10px;
  padding: 8px 14px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  color: var(--text);
}}

button.stButton > button.primary {{
  background-color: var(--primary) !important;
  color: #000 !important;
  box-shadow: 0 6px 18px rgba(56,189,248,0.25);
}}

button.stButton > button.ghost {{
  background: transparent !important;
  color: var(--primary) !important;
  border: 1px solid rgba(56,189,248,0.25);
}}

input[type="text"], textarea, .stTextInput > div > input[type="text"] {{
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
}}

.stFileUploader > div > div {{
  border-radius: 10px;
  border: 1px dashed var(--border);
  background: var(--card);
  padding: 12px;
}}

.metric-box {{
  background: linear-gradient(180deg, rgba(56,189,248,0.10), transparent);
  padding: 12px;
  border-radius: 10px;
  text-align: left;
}}

.topbar {{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 12px;
  padding: 10px 8px;
  margin-bottom: var(--space-md);
  background: var(--card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}}

@media (max-width: 900px) {{
  .hero {{ padding: 18px; border-radius: 12px; }}
  .app-card {{ padding: 12px; }}
  button.stButton > button {{ padding: 8px 10px; font-size:14px; }}
}}

.badge {{
  display:inline-block;
  padding:4px 8px;
  border-radius:999px;
  font-size:12px;
  background: rgba(255,255,255,0.08);
  color: var(--muted);
}}

a {{
  color: var(--primary);
  text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}
""")

def apply():
    try:
        st.markdown(f"<style>{BASE_CSS}</style>", unsafe_allow_html=True)
    except Exception:
        pass
