# frontend/navigation.py
import streamlit as st
from frontend.styles import apply
from utils.auth import require_login, session_logout, session_is_active
from utils.router import can_go_back, go_back, navigate, replace

apply()

def render_topbar(app_title: str = "Intelligent Book Summarizer"):
    """
    Topbar layout (three columns):
      [0] back button area (small)
      [1] centered title (large)
      [2] user controls (small)
    - On landing: hide everything on the right and leave space for visual balance.
    - On login/register: show left Back button, hide right auth controls.
    - On other pages: show left Back (when history exists), centered title, right user controls.
    """
    session_is_active(st)

    route = st.session_state.get("route", "landing")

    # left | center | right
    cols = st.columns([0.08, 0.72, 0.20])

    # LEFT column: Back button when appropriate
    with cols[0]:
        # No back on landing
        if route == "landing":
            st.markdown("<div style='height:46px;'></div>", unsafe_allow_html=True)
        else:
            # If there's history, show a back button that uses go_back(); else provide a fallback to landing
            if can_go_back():
                if st.button("← Back", key=f"nav_back_btn_left"):
                    go_back()
            else:
                # If there's no history, clicking back brings user to landing
                if st.button("← Back", key=f"nav_back_btn_left_default"):
                    navigate("landing")

    # CENTER column: Title & subtitle (centered)
    with cols[1]:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <div style="font-size:20px; font-weight:700; margin-bottom:2px;">{app_title}</div>
                <div style="color:#6b6b6b; font-size:13px; margin-top:2px;">Upload books and generate clean, structured summaries.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # RIGHT column: user controls (hidden on landing; hidden on login/register)
    with cols[2]:
        if route == "landing":
            # keep the column height consistent
            st.markdown("<div style='height:46px;'></div>", unsafe_allow_html=True)
            return

        if route in ("login", "register"):
            # For login/register, only show the left back button; hide sign-in/register/profile on right
            st.markdown("<div style='height:46px;'></div>", unsafe_allow_html=True)
            return

        # Normal pages (not landing, not login/register)
        user = require_login(st)
        if user:
            st.markdown(
                f"<div style='text-align:right; font-size:12px; color:#222'><strong>{user.get('username','')}</strong><br><span style='color:#6b6b6b'>{user.get('email','')}</span></div>",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns([0.6, 0.4])
            with c1:
                if st.button("Profile", key="nav_profile_topbar_btn"):
                    navigate("profile")
            with c2:
                if st.button("Logout", key="nav_logout_topbar_btn"):
                    try:
                        session_logout(st)
                    except Exception:
                        pass
                    # clear history and send user to landing
                    st.session_state["route_history"] = []
                    replace("landing")
        else:
            # Signed-out users: show sign in / register on right (only on non-landing pages)
            c1, c2 = st.columns([0.55, 0.45])
            with c1:
                if st.button("Sign in", key="nav_signin_topbar_btn"):
                    navigate("login")
            with c2:
                if st.button("Register", key="nav_register_topbar_btn"):
                    navigate("register")


def sidebar_nav():
    """
    Sidebar navigation — hidden on landing page (keeps landing minimal).
    """
    route = st.session_state.get("route", "landing")
    if route == "landing":
        return

    st.sidebar.markdown("## Navigation")
    pages = [
        ("Dashboard", "dashboard"),
        ("Upload", "upload"),
        ("My Profile", "profile"),
    ]

    for label, r in pages:
        if st.sidebar.button(label, key=f"nav_{r}_sidebar_btn"):
            navigate(r)

    st.sidebar.markdown("---")
    user = require_login(st)
    if user and user.get("role") == "admin":
        st.sidebar.markdown("**Admin**")
        if st.sidebar.button("Manage users", key="nav_manage_users_sidebar_btn"):
            navigate("manage_users")
