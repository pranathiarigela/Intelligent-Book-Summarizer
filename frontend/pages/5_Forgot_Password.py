import streamlit as st
from utils.api import post

st.title("🔑 Reset Password")

email = st.text_input("Enter your registered email")
new_password = st.text_input("New password", type="password")
confirm_password = st.text_input("Confirm new password", type="password")

if st.button("Reset Password"):
    if new_password != confirm_password:
        st.error("Passwords do not match")
        st.stop()

    # Step 1: verify user
    verify = post("/forgot-password", {"email": email})

    if verify.status_code != 200:
        st.error("Email not found")
        st.stop()

    # Step 2: reset password
    res = post("/reset-password", {
        "email": email,
        "new_password": new_password
    })

    if res.status_code == 200:
        st.success("Password reset successful. Please login.")
        st.switch_page("pages/1_Login.py")
    else:
        st.error("Failed to reset password")
