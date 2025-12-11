# app.py
import streamlit as st

# initialize router early so history state exists
from utils.router import init_router, navigate
init_router(default_route=st.session_state.get("route", "landing"))

from frontend.styles import apply
apply()

# initialize DB (SQLAlchemy models -> creates users, books, summaries)
try:
    from utils.database_sqlalchemy import create_tables
    create_tables()
except Exception:
    # fallback to older init if present
    try:
        from utils.database_sqlalchemy import init_db
        init_db()
    except Exception:
        # if both fail, let pages handle missing DB errors but log to console
        import traceback
        print("Warning: DB init failed. Traceback:")
        traceback.print_exc()

# Import navigation and pages
from frontend import landing as landing_page
from frontend.navigation import render_topbar, sidebar_nav
import frontend.login as login_page
import frontend.register as register_page
import frontend.dashboard as dashboard_page
import frontend.upload as upload_page
import frontend.profile as profile_page
import frontend.book_detail as page

# optional pages (if present)
try:
    import frontend.dashboard_search as dashboard_search_page
except Exception:
    dashboard_search_page = None

# mapping route keys to page modules (each module exposes a main() function)
ROUTES = {
    "landing": landing_page,  # default landing page
    "login": login_page,
    "register": register_page,
    "dashboard": dashboard_page,
    "upload": upload_page,
    "profile": profile_page,
    "search": dashboard_search_page,        # may be None
    # placeholder keys your UI uses:
    "book_detail": page,
    "generate_summary": None,
    "manage_users": None,
}

# ensure a route is set (init_router already set default), keep this for safety
if "route" not in st.session_state:
    navigate("landing")

def safe_render_topbar():
    try:
        render_topbar()
    except Exception:
        # if topbar fails, continue — don't crash entire app
        st.error("Topbar failed to render. Check navigation module.")
        import traceback
        traceback.print_exc()

def render_page(route_key: str):
    """
    Render the page associated with route_key.
    Each page module is expected to expose main(). 
    If route_key maps to None, show a placeholder message.
    """
    mod = ROUTES.get(route_key)
    if mod is None:
        # Check common placeholders
        if route_key in ("book_detail", "generate_summary", "manage_users"):
            st.markdown(f"# {route_key.replace('_', ' ').title()}")
            st.info("This page is not yet implemented or uses a different module name.")
            return
        st.error(f"No page found for route: {route_key}")
        return

    try:
        # Each module has a main() function that renders the page
        if hasattr(mod, "main"):
            mod.main()
        else:
            st.error(f"Page module for '{route_key}' has no main() function.")
    except Exception as e:
        st.error(f"Failed to render page {route_key}: {e}")
        import traceback
        st.text(traceback.format_exc())

def main():
    st.set_page_config(page_title="Intelligent Book Summarizer", layout="wide")

    # Render consistent topbar and sidebar (they handle session checks)
    safe_render_topbar()
    try:
        sidebar_nav()
    except Exception:
        # if sidebar fails, continue
        pass

    # Render the selected page
    route = st.session_state.get("route", "dashboard")
    render_page(route)

    # small footer / debug info
    with st.expander("App info", expanded=False):
        st.markdown("**Route:** " + str(st.session_state.get("route")))
        if "user" in st.session_state:
            st.markdown(f"**User:** {st.session_state['user'].get('username')} ({st.session_state['user'].get('role')})")

if __name__ == "__main__":
    main()
