from utils.router import navigate
# frontend/landing.py
import streamlit as st
from frontend.styles import apply
from utils.streamlit_helpers import safe_rerun

apply()

def hero_ctas():
    # layout: left spacer | Get Started | spacer | Sign in | right spacer
    cols = st.columns([0.35, 0.22, 0.06, 0.15, 0.22])

    with cols[1]:
        # unique key to avoid any collision with previous buttons
        if st.button("Get started — Create account", key="landing_cta_register_v3"):
            navigate("register")
            # try safe rerun, fallback to experimental rerun for compatibility
            try:
                safe_rerun()
            except Exception:
                try:
                    st.experimental_rerun()
                except Exception:
                    # last resort: force a minor state change and let user click once more
                    st.session_state["_force_rerun_marker"] = st.session_state.get("_force_rerun_marker", 0) + 1

    # spacer in cols[2]

    with cols[3]:
        if st.button("Sign in", key="landing_cta_signin_v3"):
            navigate("login")
            try:
                safe_rerun()
            except Exception:
                try:
                    st.experimental_rerun()
                except Exception:
                    st.session_state["_force_rerun_marker"] = st.session_state.get("_force_rerun_marker", 0) + 1


def main():
    st.markdown(
        """
        <div style="text-align:center; margin-top:60px; margin-bottom:26px;">
          <div style="font-size:48px; font-weight:800; line-height:1.0; margin-bottom:8px;">
            Intelligent Book Summarizer
          </div>
          <div style="font-size:16px; color:#9ca3af; max-width:740px; margin:0 auto;">
            Upload books, extract clean text, and generate concise chapter and book-level summaries — fast.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered CTAs
    st.write("")  # small spacer
    hero_ctas()

    # short features row below hero
    st.markdown("<div style='margin-top:28px;'>", unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("### Extract & Clean")
        st.write("Robust PDF / DOCX extraction with OCR fallback.")
    with cols[1]:
        st.markdown("### Chunking")
        st.write("Sentence-aware chunking preserves context across long texts.")
    with cols[2]:
        st.markdown("### Summarize")
        st.write("Chapter-level and book-level summaries.")
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
