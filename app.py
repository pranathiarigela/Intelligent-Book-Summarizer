# app.py
"""
Single-entry router for the app (no pages/ folder required).

Run:
    streamlit run app.py
"""
import streamlit as st

# Import page main() functions from frontend files.
# These files must expose `main()` and not auto-run UI at import time.
from frontend.login import main as login_page
from frontend.register import main as register_page
from frontend.dashboard import main as dashboard_page
from frontend.upload import main as upload_page

st.set_page_config(page_title="BookSummarizer", layout="wide")

# Initialize routing key
if "route" not in st.session_state:
    st.session_state["route"] = "login"

# If user already logged in, send to dashboard by default
if st.session_state.get("logged_in"):
    st.session_state["route"] = "dashboard"

# Small nav bar for dev convenience
cols = st.columns([1, 4, 1])
with cols[0]:
    if st.button("Login"):
        st.session_state["route"] = "login"
        st.rerun()
with cols[2]:
    if st.button("Dashboard"):
        st.session_state["route"] = "dashboard"
        st.rerun()

# Render the active route
route = st.session_state["route"]

if route == "login":
    login_page()
elif route == "register":
    register_page()
elif route == "dashboard":
    dashboard_page()
elif route == "upload":
    upload_page()
else:
    st.error(f"Unknown route: {route}")
