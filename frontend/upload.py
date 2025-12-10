from utils.router import navigate
# frontend/upload.py
import os
import time
from typing import Optional
import streamlit as st
from datetime import datetime

from frontend.styles import apply
apply()

from utils.auth import require_login
from utils.upload_service import handle_file_upload, handle_pasted_text, MAX_FILE_BYTES
from utils.database_sqlalchemy import SessionLocal
from utils import crud
from utils.streamlit_helpers import safe_rerun

# ---------------------------
# Upload page UI
# ---------------------------
st.title("Upload book")

def human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.2f}TB"

def recent_uploads_list(db, user_id: int, limit: int = 8):
    try:
        items = db.query(crud.Book).filter(crud.Book.user_id == user_id).order_by(crud.Book.upload_date.desc()).limit(limit).all()
    except Exception:
        items = []
    if not items:
        st.info("No uploads yet.")
        return
    st.markdown("### Recent uploads")
    for b in items:
        uploaded_at = getattr(b, "upload_date", None)
        word_count = getattr(b, "word_count", None)
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.markdown(f"**{b.title or 'Untitled'}**")
        st.markdown(f"<div class='helper'>Author: {b.author or '—'} • Uploaded: {uploaded_at}</div>", unsafe_allow_html=True)
        if word_count:
            st.markdown(f"<div class='helper'>Words: {word_count}</div>", unsafe_allow_html=True)
        cols = st.columns([0.6, 0.4])
        with cols[0]:
            if st.button("View", key=f"view_recent_{b.id}"):
                st.session_state["selected_book_id"] = b.id
                navigate("book_detail")
        with cols[1]:
            if st.button("Generate summary", key=f"gen_recent_{b.id}"):
                st.session_state["selected_book_id"] = b.id
                navigate("generate_summary")
        st.markdown("</div>", unsafe_allow_html=True)


def _get_current_user_id(user: dict) -> Optional[int]:
    """
    Robustly return the numeric user id from session/user object.
    Tries common keys: 'id', 'user_id', session_state['user_id'].
    """
    if not user:
        return None
    uid = None
    try:
        uid = user.get("id") or user.get("user_id") or user.get("user_id")
    except Exception:
        uid = None
    if not uid:
        uid = st.session_state.get("user_id")
    # ensure integer or None
    try:
        if uid is not None:
            return int(uid)
    except Exception:
        return None
    return None


def file_upload_section(user):
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Upload file")
    st.markdown('<div class="helper">Upload a PDF or TXT file (max 10 MB). We will extract text and store it for summarization.</div>', unsafe_allow_html=True)

    with st.form("file_upload_form"):
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
        title = st.text_input("Title (optional)", value="")
        author = st.text_input("Author (optional)", value="")
        submit = st.form_submit_button("Upload and extract", key="upload_submit_btn")

    if submit:
        if not uploaded_file:
            st.error("Please choose a file first.")
            return

        # read bytes
        try:
            file_bytes = uploaded_file.read()
        except Exception as e:
            st.error(f"Failed to read file: {e}")
            return

        try:
            size_bytes = len(file_bytes)
            st.markdown(f"<div class='helper'>File size: {human_size(size_bytes)}</div>", unsafe_allow_html=True)
            if size_bytes > MAX_FILE_BYTES:
                st.error(f"File exceeds max allowed size of {human_size(MAX_FILE_BYTES)}.")
                return
        except Exception:
            pass

        # determine user id
        user_id = _get_current_user_id(user)

        # call upload service
        with st.spinner("Uploading and extracting text... (this may take a few seconds)"):
            res = handle_file_upload(
                file_bytes=file_bytes,
                original_filename=uploaded_file.name,
                user_id=user_id,
                title=title.strip() or None,
                author=author.strip() or None,
            )

        if not isinstance(res, dict):
            st.error("Unexpected response from upload service.")
            return

        if res.get("ok"):
            if res.get("duplicate"):
                st.info("This file appears to be a duplicate of an existing upload.")
                existing_id = res.get("book_id")
                if existing_id:
                    st.markdown(f"[Open existing book](:#{existing_id})")
            else:
                st.success("Upload and extraction complete.")
                wc = res.get("word_count")
                if wc is not None:
                    st.markdown(f"<div class='helper'>Words extracted: <strong>{wc}</strong></div>", unsafe_allow_html=True)
                navigate("dashboard")
        else:
            # handle OCR required case specially
            if res.get("ocr_required"):
                st.error("This PDF appears to be scanned (image-only). OCR is required to extract text.")
                st.markdown(
                    "To enable OCR, install the following on the server/development machine:<ul>"
                    "<li><code>pip install pytesseract pdf2image</code></li>"
                    "<li>Install Poppler (OS package) and ensure `pdftoppm` is on PATH</li>"
                    "</ul>",
                    unsafe_allow_html=True,
                )
                st.info(f"Saved file path: {res.get('stored_path')}")
                return
            st.error(res.get("message", "Upload failed."))

    st.markdown("</div>", unsafe_allow_html=True)


def pasted_text_section(user):
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.subheader("Paste text")
    st.markdown('<div class="helper">If you have text to paste (for short excerpts or chapters), paste it here. We store it as a book record.</div>', unsafe_allow_html=True)

    pasted = st.text_area("Paste text", height=240, key="pasted_text_area")
    title = st.text_input("Title for pasted text (optional)", key="pasted_title")
    if st.button("Save pasted text", key="pasted_save_btn"):
        if not pasted or not pasted.strip():
            st.error("Pasted text cannot be empty.")
        else:
            user_id = _get_current_user_id(user)
            with st.spinner("Saving text..."):
                res = handle_pasted_text(
                    pasted_text=pasted,
                    user_id=user_id,
                    title=title.strip() or "Pasted text",
                    author=None,
                )
            if res.get("ok"):
                st.success("Text saved successfully.")
                navigate("dashboard")
            else:
                st.error(res.get("message", "Failed to save pasted text."))

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    user = require_login(st)
    if not user:
        st.warning("Please sign in to upload files.")
        if st.button("Go to sign in", key="upload_goto_signin_btn"):
            navigate("login")
        return

    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown(f"<h2>Upload</h2><div class='helper'>Logged in as <strong>{user.get('username') or st.session_state.get('user_name','')}</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    file_upload_section(user)
    st.markdown("---")
    pasted_text_section(user)

    db = SessionLocal()
    try:
        recent_uploads_list(db, user_id=_get_current_user_id(user), limit=8)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
