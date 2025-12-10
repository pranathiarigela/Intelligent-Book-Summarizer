from utils.router import navigate
# frontend/navigation.py
import streamlit as st
from typing import Optional
from frontend.styles import apply
from utils.auth import require_login, session_logout, session_is_active
from utils.streamlit_helpers import safe_rerun

apply()

def render_topbar(app_title: str = "Intelligent Book Summarizer"):
    # Keep session tracking alive
    session_is_active(st)

    # Two-column layout: title centered, user controls right
    cols = st.columns([0.75, 0.25])

    # CENTERED TITLE + SUBTITLE
    with cols[0]:
        st.markdown(
            """
            <div style="text-align:center;">
                <div style="font-size:22px; font-weight:700; margin-bottom:2px;">
                    Intelligent Book Summarizer
                </div>
                <div style="color:#6b6b6b; font-size:13px;">
                    Upload books and generate clean, structured summaries.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # RIGHT-SIDE USER AREA
        # RIGHT-SIDE USER AREA
    with cols[1]:
        # determine current route (if any)
        current_route = st.session_state.get("route", "landing")

        # if we're on landing page, do not show duplicate small auth buttons
        if current_route == "landing":
            # keep a small placeholder so topbar height is consistent
            st.markdown("<div style='height:52px;'></div>", unsafe_allow_html=True)
        else:
            # existing behavior on non-landing pages
            user = require_login(st)

            if user:
                st.markdown(
                    f"""
                    <div style='text-align:right; font-size:12px; color:#222'>
                        <strong>{user.get('username','')}</strong><br>
                        <span style='color:#6b6b6b'>{user.get('email','')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns([0.6, 0.4])
                with col_a:
                    if st.button("Profile", key="nav_profile_topbar_btn"):
                        navigate("profile")
                with col_b:
                    if st.button("Logout", key="nav_logout_topbar_btn"):
                        session_logout(st)
                        safe_rerun()

            else:
                col_a, col_b = st.columns([0.55, 0.45])
                with col_a:
                    if st.button("Sign in", key="nav_signin_topbar_btn"):
                        navigate("login")
                with col_b:
                    if st.button("Register", key="nav_register_topbar_btn"):
                        navigate("register")



def sidebar_nav():
    st.sidebar.markdown("## Navigation")
    pages = [
        ("Dashboard", "dashboard"),
        ("Upload", "upload"),
        ("My Profile", "profile"),
    ]

    for label, route in pages:
        if st.sidebar.button(label, key=f"nav_{route}_sidebar_btn"):
            st.session_state["route"] = route
            safe_rerun()

    st.sidebar.markdown("---")
    user = require_login(st)
    if user and user.get("role") == "admin":
        st.sidebar.markdown("**Admin**")
        if st.sidebar.button("Manage users", key="nav_manage_users_sidebar_btn"):
            navigate("manage_users")
