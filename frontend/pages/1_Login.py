import streamlit as st
from utils.api import post

st.title("Sign In")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Sign In"):
    res = post("/login", {
        "email": email,
        "password": password
    })

    if res.status_code == 200:
        st.session_state.logged_in = True
        st.success("Login successful")
        st.switch_page("pages/4_Dashboard.py")
    else:
        st.error("Invalid credentials")
if st.button("Forgot password?"):
    st.switch_page("pages/5_Forgot_Password.py")
