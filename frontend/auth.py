# frontend/auth.py
import re
import time
import streamlit as st

# ---------------------------
# Styles (custom CSS)
# ---------------------------
PAGE_CSS = """
    <style>
        .reportview-container .main {
            max-width: 820px;
            margin: 0 auto;
            padding-top: 24px;
            padding-bottom: 40px;
        }
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
            .small-link {
                color: #0b66c3;
                text-decoration: none;
                font-weight: 500;
            }
        </style>
    """


st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ---------------------------
# Helper: Validation functions
# ---------------------------
NAME_REGEX = re.compile(r"^[A-Za-z ]{2,}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")

def validate_name(name: str) -> str:
    if not name or not name.strip():
        return "Name cannot be empty."
    if len(name.strip()) < 2:
        return "Name must be at least 2 characters."
    if not NAME_REGEX.match(name.strip()):
        return "Name may contain only letters and spaces."
    return ""

def validate_email(email: str) -> str:
    if not email or not email.strip():
        return "Email cannot be empty."
    if not EMAIL_REGEX.match(email.strip()):
        return "Enter a valid email address."
    return ""

def validate_password(password: str) -> str:
    if not password:
        return "Password cannot be empty."
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not PASSWORD_REGEX.match(password):
        return (
            "Password must include at least one uppercase letter, "
            "one lowercase letter, one number, and one special character."
        )
    return ""

def validate_confirm_password(password: str, confirm: str) -> str:
    if confirm != password:
        return "Passwords do not match."
    return ""

# ---------------------------
# Session state initial
# ---------------------------
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

for key in [
    "reg_name_err",
    "reg_email_err",
    "reg_password_err",
    "reg_confirm_err",
    "login_email_err",
    "login_password_err",
]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------------------------
# Try to import backend functions (optional)
# ---------------------------
register_user_backend = None
login_user_backend = None
try:
    from backend.auth import register_user, login_user  # type: ignore
    register_user_backend = register_user
    login_user_backend = login_user
except Exception:
    register_user_backend = None
    login_user_backend = None

# ---------------------------
# UI: Header
# ---------------------------
st.title("Welcome")
st.write("Create an account or sign in to continue.")

# ---------------------------
# Small navigation (login / register)
# ---------------------------
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Login"):
        st.session_state.auth_page = "login"
with col2:
    if st.button("Register"):
        st.session_state.auth_page = "register"

st.write("")  # spacer

# ---------------------------
# Registration form
# ---------------------------
def registration_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Create an account")
    st.markdown('<div class="helper">Fill the fields below to create an account.</div>', unsafe_allow_html=True)

    with st.form(key="register_form", clear_on_submit=False):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            name = st.text_input("Full name", key="reg_name", placeholder="First Last")
        with col_b:
            st.write("")
            st.write("")

        email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
        pw_col1, pw_col2 = st.columns([1, 1])
        with pw_col1:
            password = st.text_input("Password", type="password", key="reg_password", help="Minimum 8 characters")
        with pw_col2:
            confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm")

        # Real-time validations (performed when the form is submitted/interacted with)
        st.session_state.reg_name_err = validate_name(name)
        st.session_state.reg_email_err = validate_email(email)
        st.session_state.reg_password_err = validate_password(password)
        st.session_state.reg_confirm_err = validate_confirm_password(password, confirm_password)

        # Display field-level errors
        if st.session_state.reg_name_err:
            st.markdown(f'<div class="field-error">{st.session_state.reg_name_err}</div>', unsafe_allow_html=True)
        if st.session_state.reg_email_err:
            st.markdown(f'<div class="field-error">{st.session_state.reg_email_err}</div>', unsafe_allow_html=True)
        if st.session_state.reg_password_err:
            st.markdown(f'<div class="field-error">{st.session_state.reg_password_err}</div>', unsafe_allow_html=True)
        if st.session_state.reg_confirm_err:
            st.markdown(f'<div class="field-error">{st.session_state.reg_confirm_err}</div>', unsafe_allow_html=True)

        st.write("")  # small spacer
        register_btn = st.form_submit_button("Register")

    st.markdown("</div>", unsafe_allow_html=True)

    if register_btn:
        name_err = validate_name(st.session_state.reg_name)
        email_err = validate_email(st.session_state.reg_email)
        password_err = validate_password(st.session_state.reg_password)
        confirm_err = validate_confirm_password(st.session_state.reg_password, st.session_state.reg_confirm)

        if name_err or email_err or password_err or confirm_err:
            st.session_state.reg_name_err = name_err
            st.session_state.reg_email_err = email_err
            st.session_state.reg_password_err = password_err
            st.session_state.reg_confirm_err = confirm_err
            st.error("Please fix the errors above and try again.")
            return

        with st.spinner("Creating your account..."):
            time.sleep(0.9)
            if register_user_backend:
                try:
                    result = register_user_backend(
                        name=st.session_state.reg_name.strip(),
                        email=st.session_state.reg_email.strip().lower(),
                        password=st.session_state.reg_password,
                    )
                    if isinstance(result, dict) and result.get("success"):
                        st.success(result.get("message", "Account created successfully."))
                        st.session_state.auth_page = "login"
                    else:
                        msg = result.get("message") if isinstance(result, dict) else "Registration failed."
                        st.error(msg)
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
            else:
                st.success("Form validated. Backend registration not connected.")
                st.info("Hook `backend.auth.register_user(name, email, password)` to complete registration.")
                st.session_state.auth_page = "login"

# ---------------------------
# Login form
# ---------------------------
def login_form():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Sign in")
    st.markdown('<div class="helper">Enter your credentials to sign in.</div>', unsafe_allow_html=True)

    # Form: only inputs and submit button inside the form
    with st.form(key="login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="login_password")
        remember = st.checkbox("Remember me", key="login_remember")
        st.session_state.login_email_err = validate_email(email)
        st.session_state.login_password_err = "" if password else "Password cannot be empty."

        if st.session_state.login_email_err:
            st.markdown(f'<div class="field-error">{st.session_state.login_email_err}</div>', unsafe_allow_html=True)
        if st.session_state.login_password_err:
            st.markdown(f'<div class="field-error">{st.session_state.login_password_err}</div>', unsafe_allow_html=True)

        login_btn = st.form_submit_button("Login")

    # Navigation and auxiliary actions placed outside the form (this avoids the Streamlit API error)
    nav_col_l, nav_col_r = st.columns([1, 1])
    with nav_col_l:
        if st.button("Register instead"):
            st.session_state.auth_page = "register"
    with nav_col_r:
        if st.button("Forgot password?"):
            st.info("Password reset flow is a placeholder. Implement backend endpoint to send reset email.")

    st.markdown("</div>", unsafe_allow_html=True)

    if login_btn:
        email_err = validate_email(st.session_state.login_email)
        password_err = "" if st.session_state.login_password else "Password cannot be empty."

        if email_err or password_err:
            st.session_state.login_email_err = email_err
            st.session_state.login_password_err = password_err
            st.error("Please fix the errors above and try again.")
            return

        with st.spinner("Verifying credentials..."):
            time.sleep(0.9)
            if login_user_backend:
                try:
                    result = login_user_backend(
                        email=st.session_state.login_email.strip().lower(),
                        password=st.session_state.login_password,
                    )
                    if isinstance(result, dict) and result.get("success"):
                        st.success("Logged in successfully.")
                        user = result.get("user", {})
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user.get("user_id")
                        st.session_state["user_name"] = user.get("name")
                        st.session_state["user_email"] = user.get("email")
                        st.session_state["user_role"] = user.get("role", "user")
                        st.experimental_rerun()
                    else:
                        st.error(result.get("message", "Invalid credentials."))
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
            else:
                st.success("Credentials validated. Backend login not connected.")
                st.info("Hook `backend.auth.login_user(email, password)` to complete login.")
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = st.session_state.login_email
                st.session_state["user_name"] = st.session_state.login_email.split("@")[0]
                st.experimental_rerun()

# ---------------------------
# Render selected page
# ---------------------------
if st.session_state.auth_page == "register":
    registration_form()
else:
    login_form()

# ---------------------------
# Footer
# ---------------------------
st.write("")
st.markdown("---")
