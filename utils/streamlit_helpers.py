# utils/streamlit_helpers.py
import time
import streamlit as st

def safe_rerun():
    """
    Try to call Streamlit's experimental rerun. If not available in this
    environment, fall back to toggling a harmless query param to force a rerun.
    This is safe for development and avoids AttributeError on older/newer builds.
    """
    try:
        # Preferred: native rerun when available
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
    except Exception:
        # fallthrough to fallback below
        pass

    # Fallback: toggle a dummy query param which will cause Streamlit to refresh UI
    try:
        # Using current timestamp to ensure value changes
        st.query_params(_rerun=int(time.time()))
    except Exception:
        # If experimental_set_query_params is unavailable, toggle a session_state flag
        try:
            st.session_state["_rerun_flag"] = not st.session_state.get("_rerun_flag", False)
        except Exception:
            # last resort: no-op
            return
