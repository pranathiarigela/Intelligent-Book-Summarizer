import streamlit as st
from utils.api import post

st.title("Create Account")

username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Register"):
    res = post("/register", {
        "username": username,
        "email": email,
        "password": password
    })

    if res.status_code == 200:
        st.success("Account created. Please login.")
        st.switch_page("pages/1_Login.py")
    else:
        st.error("User already exists")
