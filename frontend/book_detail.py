# frontend/book_detail.py
import streamlit as st
from frontend.styles import apply
from utils.database_sqlalchemy import SessionLocal
from utils import crud
from utils.auth import require_login, session_is_active
from utils.router import navigate, go_back, can_go_back
from utils.streamlit_helpers import safe_rerun
from datetime import datetime

apply()

def format_dt(dt):
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt)

def compute_text_stats(text: str):
    if not text:
        return {"words": 0, "chars": 0, "lines": 0}
    # normalize newlines
    chars = len(text)
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    # simple word split (keeps it fast and robust)
    words = len([w for w in text.split() if w.strip()])
    return {"words": words, "chars": chars, "lines": lines}

def safe_get(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default

def main():
    # Ensure user is logged in
    _ = session_is_active(st)
    user = require_login(st)
    if not user:
        st.warning("Please sign in to view this page.")
        if st.button("Go to Sign in", key="book_detail_to_login_btn"):
            navigate("login")
        return

    # Check selected book id
    book_id = st.session_state.get("selected_book_id")
    if not book_id:
        st.error("No book selected.")
        if can_go_back() and st.button("← Back", key="book_detail_back_noid"):
            go_back()
        return

    db = SessionLocal()
    try:
        book = db.query(crud.Book).get(book_id)
        if not book:
            st.error("Book not found.")
            if can_go_back() and st.button("← Back", key="book_detail_back_notfound"):
                go_back()
            return

        # Top back button
        if can_go_back():
            if st.button("← Back", key="book_detail_back_btn"):
                go_back()

        # Header card
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.markdown(f"<h2>{safe_get(book, 'title') or 'Untitled Book'}</h2>", unsafe_allow_html=True)
        st.markdown(f"<div class='helper'>Author: <strong>{safe_get(book, 'author') or 'Unknown'}</strong></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Stats card
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        # filename: try multiple likely fields
        filename = safe_get(book, "filename") or safe_get(book, "file_name") or safe_get(book, "file") or None
        file_type = safe_get(book, "file_type") or safe_get(book, "mime_type") or "unknown"
        upload_dt = safe_get(book, "upload_date") or safe_get(book, "created_at") or None
        status = safe_get(book, "status") or "unknown"

        # compute stats from original_text if present
        original_text = safe_get(book, "original_text") or ""
        stats = compute_text_stats(original_text)

        # fallback to stored word_count if available
        stored_wc = safe_get(book, "word_count")
        if stored_wc:
            # prefer stored count if present but still show computed too
            wc_display = f"{stored_wc} (stored)"
        else:
            wc_display = f"{stats['words']}"

        st.markdown(f"<div style='display:flex; gap:20px; flex-wrap:wrap;'>", unsafe_allow_html=True)
        st.markdown(
            f"<div><strong>File name</strong><div class='helper'>{filename or '—'}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>Uploaded</strong><div class='helper'>{format_dt(upload_dt) if upload_dt else '—'}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>File type</strong><div class='helper'>{file_type}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>Status</strong><div class='helper'>{status}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>Words</strong><div class='helper'>{wc_display}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>Characters</strong><div class='helper'>{stats['chars']}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div><strong>Lines</strong><div class='helper'>{stats['lines']}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Action buttons
        cols = st.columns([0.5, 0.5])
        with cols[0]:
            if st.button("Generate Summary", key="book_detail_generate_btn"):
                st.session_state["selected_book_id"] = book.id
                navigate("generate_summary")
        with cols[1]:
            if st.button("Delete Book", key="book_detail_delete_btn"):
                st.session_state["confirm_delete_book_from_detail"] = book.id
                safe_rerun()

        # Confirm delete section
        if st.session_state.get("confirm_delete_book_from_detail") == book.id:
            st.error("Are you sure you want to delete this book?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete", key="yes_delete_detail"):
                    try:
                        db.delete(book)
                        db.commit()
                        st.success("Book deleted.")
                        st.session_state.pop("confirm_delete_book_from_detail", None)
                        navigate("dashboard")
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
            with c2:
                if st.button("Cancel", key="cancel_delete_detail"):
                    st.session_state.pop("confirm_delete_book_from_detail", None)
                    safe_rerun()

    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
