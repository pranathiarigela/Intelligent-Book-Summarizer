# frontend/navigation.py
import streamlit as st
from typing import Dict, Any
from datetime import datetime

# Session keys used across the app:
SESSION_KEYS = ["logged_in", "user_id", "user_name", "user_email", "user_role", "page"]

def ensure_session_state_keys():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        # respect query param if present
        params = st.query_params
        if "page" in params:
            st.session_state["page"] = params["page"]
        else:
            st.session_state["page"] = "dashboard"

def set_page(page_name: str):
    """Set current page and push to query params (back/forward friendly)."""
    st.session_state["page"] = page_name
    st.query_params.update({"page": page_name})
    st.rerun()

def logout():
    """Clear auth/session keys and navigate to login."""
    for k in SESSION_KEYS:
        st.session_state.pop(k, None)
    # clear query params and rerun
    st.query_params.clear()
    st.rerun()

def header(user: Dict[str, Any], app_title: str = "Book Summarizer", logo_src: str | None = None):
    """Top header with logo, title, role badge and simple profile actions."""
    cols = st.columns([0.12, 0.6, 0.28])
    #with cols[0]:
     #   src = logo_src or "https://via.placeholder.com/64"
     #   st.image(src, width=48)
    with cols[1]:
        st.markdown(f"## {app_title}")
        st.markdown(f"Welcome, **{user.get('name', 'User')}**")
    with cols[2]:
        role = user.get("role", "user")
        st.markdown(f"**Role:** `{role}`")
        with st.expander("Profile"):
            if st.button("View Profile"):
                st.info("Profile page: implement in frontend/profile.py")
            if st.button("Settings"):
                set_page("settings")
            if st.button("Logout"):
                logout()

def sidebar_nav(user: Dict[str, Any]):
    """Render sidebar navigation and set st.session_state['page'] when changed."""
    st.sidebar.title("Navigation")
    nav_items = [
        ("dashboard", "Home"),
        ("upload", "Upload Book"),
        ("my_books", "My Books"),
        ("summaries", "Summaries"),
        ("settings", "Settings"),
        ("help", "Help / Docs"),
    ]
    if user.get("role") == "admin":
        nav_items.insert(4, ("manage_users", "Manage Users"))

    # Determine initial index using current page
    current_key = st.session_state.get("page", "dashboard")
    key_to_label = {k: label for k, label in nav_items}
    labels = [label for _, label in nav_items]
    init_index = 0
    try:
        init_index = labels.index(key_to_label.get(current_key, labels[0]))
    except Exception:
        init_index = 0

    selected_label = st.sidebar.radio("Go to", labels, index=init_index)
    label_to_key = {label: key for key, label in nav_items}
    chosen_key = label_to_key[selected_label]
    if st.session_state.get("page") != chosen_key:
        set_page(chosen_key)

# Replace the existing pretty_time_ago function with this version
def pretty_time_ago(dt: datetime | None) -> str:
    """
    Robust 'time ago' helper that accepts:
      - None -> "Never"
      - datetime (naive or tz-aware)
      - ISO-format strings produced by datetime.isoformat()

    It normalizes times to UTC-aware datetimes before computing the delta.
    """
    import datetime as _dt

    if dt is None:
        return "Never"

    # If dt is a string, try to parse ISO format first
    if isinstance(dt, str):
        try:
            # fromisoformat handles both naive and offset-aware ISO strings
            dt = _dt.datetime.fromisoformat(dt)
        except Exception:
            # fallback: try common format
            try:
                dt = _dt.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return "Unknown"

    # Ensure dt is a datetime now
    if not isinstance(dt, _dt.datetime):
        return "Unknown"

    # Normalize both times to UTC-aware datetimes
    now = _dt.datetime.now(_dt.timezone.utc)

    if dt.tzinfo is None:
        # assume naive datetimes are stored in UTC — attach UTC tzinfo
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    else:
        # convert aware datetime to UTC
        dt = dt.astimezone(_dt.timezone.utc)

    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if seconds < 86400:
        hrs = int(seconds // 3600)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    days = int(seconds // 86400)
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"
