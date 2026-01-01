import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:5000"

def get_session():
    if "http_session" not in st.session_state:
        st.session_state.http_session = requests.Session()
    return st.session_state.http_session

def post(endpoint, data=None, files=None):
    session = get_session()
    return session.post(
        f"{BASE_URL}{endpoint}",
        json=data,
        files=files
    )

def get(endpoint, params=None):
    session = get_session()
    return session.get(
        f"{BASE_URL}{endpoint}",
        params=params
    )

def get_file(endpoint, params=None):
    session = get_session()
    response = session.get(
        f"{BASE_URL}{endpoint}",
        params=params,
        stream=True
    )
    return response
