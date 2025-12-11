# utils/ui.py
from functools import partial
import streamlit as st
from typing import Callable, Optional

# Import router navigate here to keep callbacks small
try:
    from utils.router import navigate
except Exception:
    navigate = None

def action_button(label: str,
                  key: Optional[str] = None,
                  navigate_to: Optional[str] = None,
                  on_click: Optional[Callable] = None,
                  **kwargs):
    """
    Creates a Streamlit button that runs a callback. If `navigate_to` is set this will call
    utils.router.navigate(route) inside the callback (preferred).
    Use this instead of `if st.button(...): st.session_state[...] = ...` patterns.
    """
    def _callback():
        # user callback first
        if callable(on_click):
            try:
                on_click()
            except Exception:
                pass
        # then navigate if requested
        if navigate_to and navigate:
            try:
                navigate(navigate_to)
            except Exception:
                # best-effort: set session_state and hope for rerun
                st.session_state["route"] = navigate_to

    return st.button(label, key=key, on_click=_callback, **kwargs)
