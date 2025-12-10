# utils/router.py
import streamlit as st
from typing import Optional

# Try to reuse your safe rerun helper if present
try:
    from utils.streamlit_helpers import safe_rerun as _safe_rerun_fn
except Exception:
    _safe_rerun_fn = None

def _safe_rerun():
    """Robust rerun helper (tries safe_rerun then experimental rerun then small state bump)."""
    if _safe_rerun_fn:
        try:
            _safe_rerun_fn()
            return
        except Exception:
            pass
    try:
        st.experimental_rerun()
        return
    except Exception:
        # last resort: nudge a session key
        st.session_state["_router_force_refresh"] = st.session_state.get("_router_force_refresh", 0) + 1

# Initialize router state (call once at app start)
def init_router(default_route: str = "landing"):
    if "route" not in st.session_state:
        st.session_state["route"] = default_route
    if "route_history" not in st.session_state:
        st.session_state["route_history"] = [st.session_state.get("route", default_route)]

def current_route() -> str:
    return st.session_state.get("route", "landing")

def navigate(route: str, push: bool = True):
    """
    Navigate to `route`.
    If push is True (default), current route is pushed onto history before navigation.
    If push is False, the current route is replaced (no history push).
    """
    if push:
        hist = st.session_state.setdefault("route_history", [])
        # avoid pushing duplicate consecutive routes
        if not hist or hist[-1] != st.session_state.get("route"):
            hist.append(st.session_state.get("route"))
        st.session_state["route_history"] = hist
    else:
        # replace current route in the history stack's last element if exists
        hist = st.session_state.setdefault("route_history", [])
        if hist:
            hist[-1] = route
            st.session_state["route_history"] = hist

    st.session_state["route"] = route
    _safe_rerun()

def replace(route: str):
    """Replace current route without adding to history."""
    st.session_state["route"] = route
    _safe_rerun()

def can_go_back() -> bool:
    hist = st.session_state.get("route_history", [])
    return bool(hist)

def go_back(default: Optional[str] = "landing"):
    """
    Pop the last route from history and navigate to it.
    If history empty, navigate to `default`.
    """
    hist = st.session_state.get("route_history", [])
    if hist:
        prev = hist.pop()  # last pushed route
        st.session_state["route_history"] = hist
        st.session_state["route"] = prev
        _safe_rerun()
    else:
        st.session_state["route"] = default
        _safe_rerun()
