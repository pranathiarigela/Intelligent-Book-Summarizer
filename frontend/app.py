import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Intelligent Book Summarizer",
    layout="wide",
)

# Load CSS
css_path = Path("frontend/styles/main.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------- LANDING PAGE --------
st.markdown("""
<div class="card">
  <h1>📘 Intelligent Book Summarizer</h1>
  <p>
    Upload books or text and generate AI-powered summaries.
    Built for students and researchers.
  </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔐 Sign In", use_container_width=True):
        st.switch_page("pages/1_Login.py")

with col2:
    if st.button("📝 Register", use_container_width=True):
        st.switch_page("pages/2_Register.py")
