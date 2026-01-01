import streamlit as st
from utils.api import post

if not st.session_state.get("logged_in"):
    st.switch_page("app.py")

st.title("📤 Upload Book")

title = st.text_input("Book Title")
author = st.text_input("Author (optional)")
file = st.file_uploader("Choose file", type=["pdf", "docx", "txt"])

if file and st.button("Upload"):
    with st.spinner("Uploading..."):
        files = {"file": (file.name, file, file.type)}
        data = {"title": title, "author": author}
        res = post("/upload/file", data=data, files=files)

    if res.status_code == 200:
        st.success("File uploaded successfully")
    else:
        try:
            st.error(res.json().get("error"))
        except:
            st.error("Upload failed")
