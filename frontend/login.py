from utils.router import navigate
# frontend/login.py
import time
import streamlit as st
import re
import traceback
from typing import Optional
from utils.auth import authenticate_user, session_login_set
from frontend.styles import apply
from utils.streamlit_helpers import safe_rerun

apply()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

def validate_email(email: str) -> str:
    if not email or not email.strip():
        return "Email cannot be empty."
    if not EMAIL_REGEX.match(email.strip()):
        return "Enter a valid email address."
    return ""

def validate_password(password: str) -> str:
    if not password:
        return "Password cannot be empty."
    return ""

# optional backend reset function
password_reset_backend = None
try:
    from backend.auth import initiate_password_reset  # type: ignore
    password_reset_backend = initiate_password_reset
except Exception:
    password_reset_backend = None

st.title("Sign in")

def forgot_password_flow():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Reset password")
    st.markdown('<div class="helper">Enter your email to receive password reset instructions.</div>', unsafe_allow_html=True)
    with st.form("forgot_form"):
        fp_email = st.text_input("Email", key="fp_email", placeholder="you@example.com")
        submit_fp = st.form_submit_button("Send reset link", key="forgot_send_btn")
    if submit_fp:
        err = validate_email(fp_email)
        if err:
            st.markdown(f'<div class="field-error">{err}</div>', unsafe_allow_html=True)
            return
        with st.spinner("Sending reset instructions..."):
            time.sleep(0.6)
            if password_reset_backend:
                try:
                    res = password_reset_backend(fp_email.strip().lower())
                    if isinstance(res, dict):
                        if res.get("success"):
                            st.success(res.get("message", "Reset instructions sent."))
                        else:
                            st.error(res.get("message", "Could not send reset instructions."))
                    else:
                        st.success("If that email exists, reset instructions were sent.")
                except Exception:
                    st.error("Failed to initiate password reset. See server logs.")
                    st.text(traceback.format_exc())
            else:
                st.success("If that email exists in our system, a reset link has been sent.")
                st.info("This is a simulated flow because no backend reset function is available.")
    st.markdown("</div>", unsafe_allow_html=True)

def login_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Welcome back")
    st.markdown('<div class="helper">Enter your credentials to continue.</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password")
        remember = st.checkbox("Remember me", key="login_remember")
        login_btn = st.form_submit_button("Login", key="login_submit_btn")

    if login_btn:
        email_err = validate_email(email)
        pw_err = validate_password(password)

        if email_err:
            st.markdown(f'<div class="field-error">{email_err}</div>', unsafe_allow_html=True)
            return

        if pw_err:
            st.markdown(f'<div class="field-error">{pw_err}</div>', unsafe_allow_html=True)
            return

        with st.spinner("Checking your credentials..."):
            time.sleep(0.6)
            try:
                auth_result = authenticate_user(email.lower().strip(), password)
            except Exception as e:
                st.error(f"Authentication service error: {e}")
                st.text(traceback.format_exc())
                return

            # Expected auth_result: {"ok": True, "user": {...}} on success
            if isinstance(auth_result, dict) and auth_result.get("ok"):
                user = auth_result.get("user", {})

                # Prefer centralized session setter if available, otherwise set session vars
                try:
                    session_login_set(st, user)
                except Exception:
                    st.session_state["user_email"] = user.get("email", email)
                    st.session_state["user_name"] = user.get("username", email.split("@")[0] if email else "user")
                    st.session_state["user_role"] = user.get("role", "user")
                    st.session_state["logged_in"] = True

                # ensure canonical keys exist
                if "user_id" not in st.session_state and user.get("id") is not None:
                    st.session_state["user_id"] = user.get("id")
                if "user_name" not in st.session_state and user.get("username"):
                    st.session_state["user_name"] = user.get("username")
                if "user_email" not in st.session_state and user.get("email"):
                    st.session_state["user_email"] = user.get("email")
                if "user_role" not in st.session_state and user.get("role"):
                    st.session_state["user_role"] = user.get("role")

                st.success("Logged in successfully.")
                # Professional redirect: always send user to dashboard after login
                navigate("dashboard")
                # use safe rerun helper so navigation updates cleanly
                safe_rerun()
            else:
                msg = "Invalid credentials."
                if isinstance(auth_result, dict) and auth_result.get("error"):
                    msg = auth_result.get("error") or msg
                st.error(msg)
                return

    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>", unsafe_allow_html=True)
    if st.button("Create an account", key="login_create_account_btn"):
        navigate("register")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Forgot password?", key="login_forgot_btn"):
        st.session_state["show_forgot"] = True

    if st.session_state.get("show_forgot"):
        with st.expander("Forgot password", expanded=True):
            forgot_password_flow()

def main():
    if "show_forgot" not in st.session_state:
        st.session_state["show_forgot"] = False
    login_form()

if __name__ == "__main__":
    main()
