from utils.router import navigate
# frontend/register.py
import time
import streamlit as st
import re
import traceback
from utils.auth import register_user
from frontend.styles import apply
from utils.streamlit_helpers import safe_rerun
apply()

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}$")

def validate_username(username: str) -> str:
    if not username or not username.strip():
        return "Username cannot be empty."
    if not USERNAME_REGEX.match(username.strip()):
        return "Username must be 3–32 characters, letters, numbers, ., _, or -."
    return ""

def validate_email(email: str) -> str:
    if not email or not email.strip():
        return "Email cannot be empty."
    if not EMAIL_REGEX.match(email.strip()):
        return "Enter a valid email address."
    return ""

def validate_passwords(pw: str, pw2: str) -> str:
    if not pw:
        return "Password cannot be empty."
    if len(pw) < 6:
        return "Password should be at least 6 characters."
    if pw != pw2:
        return "Passwords do not match."
    return ""

st.title("Create account")

def register_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Sign up")
    st.markdown('<div class="helper">Create a free account to upload books and generate summaries.</div>', unsafe_allow_html=True)

    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username", placeholder="your-username")
        email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="reg_password")
        password2 = st.text_input("Confirm password", type="password", key="reg_password2")
        agree = st.checkbox("I agree to the terms and privacy policy", key="reg_terms")
        submit = st.form_submit_button("Create account", key="register_submit_btn")

    if submit:
        un_err = validate_username(username)
        email_err = validate_email(email)
        pw_err = validate_passwords(password, password2)
        if not agree:
            st.markdown(f'<div class="field-error">You must agree to the terms.</div>', unsafe_allow_html=True)
            return
        if un_err:
            st.markdown(f'<div class="field-error">{un_err}</div>', unsafe_allow_html=True)
            return
        if email_err:
            st.markdown(f'<div class="field-error">{email_err}</div>', unsafe_allow_html=True)
            return
        if pw_err:
            st.markdown(f'<div class="field-error">{pw_err}</div>', unsafe_allow_html=True)
            return

        with st.spinner("Creating your account..."):
            time.sleep(0.8)
            try:
                res = register_user(username=username.strip(), email=email.strip().lower(), password=password)
            except Exception as e:
                st.error(f"Registration failed: {e}")
                st.text(traceback.format_exc())
                return

            if isinstance(res, dict):
                if res.get("ok"):
                    st.success("Account created successfully. Please sign in.")
                    try:
                        navigate("login")
                    except Exception:
                        pass
                else:
                    err = res.get("error") or res.get("message") or "Registration failed."
                    if err == "username_taken":
                        st.error("That username is already taken. Try another.")
                    elif err == "email_taken":
                        st.error("An account with that email already exists.")
                    else:
                        st.error(err)
            else:
                st.error("Registration failed. Please try again later.")

    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>", unsafe_allow_html=True)
    if st.button("Back to login", key="register_back_btn"):
        navigate("login")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    register_form()

if __name__ == "__main__":
    main()
