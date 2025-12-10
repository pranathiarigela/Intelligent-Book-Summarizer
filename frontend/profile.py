from utils.router import navigate
# frontend/profile.py
import streamlit as st
from frontend.styles import apply
from utils.streamlit_helpers import safe_rerun
from utils.auth import require_login

apply()

def main():
    # Page-level: do NOT render the topbar here. navigation.render_topbar() handles that.
    user = require_login(st)
    if not user:
        st.warning("You must be logged in to view your profile.")
        if st.button("Go to Login", key="profile_go_login_btn"):
            navigate("login")
        return

    st.title("My Profile")
    st.subheader("Account Information")

    # Read values from the canonical session keys (set by auth/session helpers)
    st.write(f"**Name:** {st.session_state.get('user_name', user.get('username') or 'N/A')}")
    st.write(f"**Email:** {st.session_state.get('user_email', user.get('email') or 'N/A')}")
    st.write(f"**Role:** {st.session_state.get('user_role', user.get('role', 'user')).capitalize()}")

    st.markdown("---")
    st.subheader("Update Profile")

    # Local form for updates (no topbar duplication)
    new_name = st.text_input("Update Name", value=st.session_state.get("user_name", user.get("username", "")), key="profile_new_name")
    new_email = st.text_input("Update Email", value=st.session_state.get("user_email", user.get("email", "")), key="profile_new_email")

    if st.button("Save Changes", key="profile_save_btn"):
        # In this simple implementation we only update session state.
        # Hook this to your DB update function if you want persistence.
        st.session_state["user_name"] = new_name
        st.session_state["user_email"] = new_email
        st.success("Profile updated successfully.")
        safe_rerun()

    st.markdown("---")
    if st.button("Back to Dashboard", key="profile_back_btn"):
        navigate("dashboard")

if __name__ == "__main__":
    main()
