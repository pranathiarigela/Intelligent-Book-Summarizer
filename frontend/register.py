# frontend/register.py
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
NAME_REGEX = re.compile(r"^[A-Za-z ]{2,}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")

def validate_name(name: str) -> str:
    if not name.strip():
        return "Name cannot be empty."
    if not NAME_REGEX.match(name.strip()):
        return "Enter a valid name."
    return ""

def validate_email(email: str) -> str:
    if not EMAIL_REGEX.match(email.strip()):
        return "Enter a valid email."
    return ""

def validate_password(password: str) -> str:
    if not PASSWORD_REGEX.match(password):
        return (
            "Password must contain uppercase, lowercase, digit, "
            "and special character (min 8 chars)."
        )
    return ""

def validate_confirm(pw, cpw):
    return "" if pw == cpw else "Passwords do not match."

# ---------------------------
# Optional backend function import
# ---------------------------
try:
    from backend.auth import register_user  # type: ignore
    register_user_backend = register_user
except:
    register_user_backend = None

# ---------------------------
# UI: Registration Page
# ---------------------------
st.title("Create an account")

def registration_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Register")
    st.markdown('<div class="helper">Fill in the details to get started.</div>', unsafe_allow_html=True)

    with st.form("register_form"):
        name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        pw = st.text_input("Password", type="password", key="reg_pw")
        cpw = st.text_input("Confirm Password", type="password", key="reg_cpw")
        submit_btn = st.form_submit_button("Register")

    if submit_btn:
        err_name = validate_name(name)
        err_email = validate_email(email)
        err_pw = validate_password(pw)
        err_cpw = validate_confirm(pw, cpw)

        errors = [err_name, err_email, err_pw, err_cpw]
        errors = [e for e in errors if e]

        if errors:
            for e in errors:
                st.markdown(f'<div class="field-error">{e}</div>', unsafe_allow_html=True)
            return

        with st.spinner("Creating your account..."):
            time.sleep(0.8)

            if register_user_backend:
                try:
                    result = register_user_backend(
                        name=name.strip(),
                        email=email.strip().lower(),
                        password=pw,
                    )
                    if result.get("success"):
                        st.success("Account created successfully.")
                        st.query_params.update({"page": "login"})
                        st.session_state["route"] = "login"
                        st.rerun()

                    else:
                        st.error(result.get("message", "Registration failed."))
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.success("Account validated (backend not connected).")
                st.session_state["route"] = "login"
                st.rerun()

    st.info("Already have an account?")
    if st.button("Sign in"):
        st.session_state["route"] = "login"
        st.rerun()

def main():
    registration_form()

if __name__ == "__main__":
    main()
