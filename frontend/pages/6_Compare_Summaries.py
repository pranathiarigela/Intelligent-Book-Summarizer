import streamlit as st
from utils.api import get, post

st.title("🔍 Compare Summary Versions")

books = get("/books").json()["books"]
book = st.selectbox("Select Book", books, format_func=lambda x: x["title"])

history = get(f"/books/{book['book_id']}/summary-history").json()["summaries"]

col1, col2 = st.columns(2)

with col1:
    s1 = st.selectbox("Version A", history, format_func=lambda x: f"v{x['version']}")

with col2:
    s2 = st.selectbox("Version B", history, format_func=lambda x: f"v{x['version']}")

if st.button("Compare"):
    diff = get(
        f"/summaries/compare?id1={s1['summary_id']}&id2={s2['summary_id']}"
    ).json()

    st.components.v1.html(diff["diff_html"], height=500, scrolling=True)
