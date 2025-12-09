# frontend/login.py
import time
import streamlit as st
import re

# ---------------------------
# Styles (reuse from old file)
# ---------------------------
PAGE_CSS = """
<style>
    .auth-card {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        padding: 20px;
        margin-bottom: 18px;
    }
    .field-error {
        color: #d93025;
        font-size: 0.9rem;
        margin-top: 6px;
    }
    .helper {
        color: #6b6b6b;
        font-size: 0.9rem;
    }
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ---------------------------
# Validation helpers
# ---------------------------
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

# ---------------------------
# Optional backend function import
# ---------------------------
try:
    from backend.auth import login_user  # type: ignore
    login_user_backend = login_user
except:
    login_user_backend = None

# ---------------------------
# UI: Login Page
# ---------------------------
st.title("Sign in")

def login_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Welcome back")
    st.markdown('<div class="helper">Enter your credentials to continue.</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password")
        remember = st.checkbox("Remember me", key="login_remember")
        login_btn = st.form_submit_button("Login")

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
            time.sleep(0.8)

            if login_user_backend:
                try:
                    result = login_user_backend(email=email.lower().strip(), password=password)
                    if result.get("success"):
                        user = result.get("user", {})
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user.get("user_id")
                        st.session_state["user_name"] = user.get("name")
                        st.session_state["user_email"] = user.get("email")
                        st.session_state["user_role"] = user.get("role", "user")
                        st.success("Logged in successfully.")
                        st.query_params.update({"page": "dashboard"})
                        st.rerun()
                    else:
                        st.error(result.get("message", "Invalid credentials."))
                        return
                except Exception as e:
                    st.error(f"Login failed: {e}")
                    return
            else:
                # No backend yet → simulate success
                st.success("Login validated (backend not connected).")
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.session_state["user_name"] = email.split("@")[0]
                st.session_state["user_role"] = "user"
                st.rerun()

    st.info("Don't have an account?")
    if st.button("Create an account"):
        st.session_state["route"] = "register"
        st.rerun()

def main():
    login_form()

if __name__ == "__main__":
    main()
