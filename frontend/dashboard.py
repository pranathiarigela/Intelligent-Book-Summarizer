from utils.router import navigate
# frontend/dashboard.py
import io
import time
import streamlit as st
from datetime import datetime
from frontend.styles import apply

from utils.auth import require_login, session_is_active
from utils.database_sqlalchemy import SessionLocal
from utils import crud
from utils.streamlit_helpers import safe_rerun

_upload_backend_fn = None
try:
    # common candidate locations
    from backend.upload import upload_file as _upload_backend_fn  # type: ignore
except Exception:
    try:
        from backend.upload import create_book as _upload_backend_fn  # type: ignore
    except Exception:
        _upload_backend_fn = None


apply()

def _safe_rerun():
    """Robust rerun helper: try safe_rerun, fallback to experimental rerun, fallback to tiny state bump."""
    try:
        safe_rerun()
        return
    except Exception:
        pass
    try:
        st.experimental_rerun()
        return
    except Exception:
        # Last resort: change a harmless session key so the app visibly updates.
        st.session_state["_force_rerun_marker"] = st.session_state.get("_force_rerun_marker", 0) + 1


def render_inline_upload(max_file_size_mb: int = 10):
    """
    Inline upload card to appear on dashboard above book list.
    Accepts PDF/TXT or pasted text. Tries to call backend upload function if available.
    """
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-weight:700; font-size:16px;'>Upload a new book</div>", unsafe_allow_html=True)
    st.markdown("<div class='helper'>PDF or TXT. Max size: {} MB.</div>".format(max_file_size_mb), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        uploaded = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"], key="dashboard_inline_file_uploader")
        pasted = st.text_area("Or paste text directly (optional)", height=200, key="dashboard_inline_pasted")
        title = st.text_input("Title (optional)", key="dashboard_inline_title")
        author = st.text_input("Author (optional)", key="dashboard_inline_author")
    with col2:
        st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
        st.markdown("<div class='helper'>You can either upload a file or paste text. The paste option is useful for excerpts.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Submit handling
    if st.button("Upload", key="dashboard_inline_upload_btn"):
        # Validation
        if not uploaded and not (pasted and pasted.strip()):
            st.error("Please upload a file or paste text to upload.")
            return

        # File size validation if a file was provided
        if uploaded:
            try:
                uploaded.seek(0, io.SEEK_END)
                size_bytes = uploaded.tell()
                uploaded.seek(0)
            except Exception:
                size_bytes = None

            if size_bytes and (size_bytes > max_file_size_mb * 1024 * 1024):
                st.error(f"File too large — maximum allowed is {max_file_size_mb} MB.")
                return

        # Prepare payload
        payload = {
            "title": (title.strip() if title else None),
            "author": (author.strip() if author else None),
            "file_type": None,
            "raw_bytes": None,
            "text": None,
        }

        if uploaded:
            name = uploaded.name.lower()
            payload["file_type"] = "pdf" if name.endswith(".pdf") else "txt"
            payload["raw_bytes"] = uploaded.read()
        else:
            payload["file_type"] = "text"
            payload["text"] = pasted.strip()

        # Try backend upload if available
        if _upload_backend_fn:
            with st.spinner("Uploading and extracting..."):
                try:
                    result = None
                    if payload["raw_bytes"] is not None:
                        # prefer bytes upload API
                        try:
                            result = _upload_backend_fn(file_bytes=payload["raw_bytes"],
                                                        filename=uploaded.name if uploaded else None,
                                                        title=payload["title"],
                                                        author=payload["author"])
                        except TypeError:
                            # fallback positional
                            result = _upload_backend_fn(payload["raw_bytes"], uploaded.name if uploaded else None, payload["title"], payload["author"])
                    else:
                        # text-only upload
                        try:
                            result = _upload_backend_fn(text=payload["text"], title=payload["title"], author=payload["author"])
                        except TypeError:
                            result = _upload_backend_fn(payload["text"], payload["title"], payload["author"])

                    # Interpret result
                    if isinstance(result, dict):
                        if result.get("ok") or result.get("success"):
                            st.success(result.get("message", "Uploaded successfully."))
                            # refresh dashboard book list
                            time.sleep(0.5)
                            # force refresh
                            navigate("dashboard")
                        else:
                            st.error(result.get("message", "Upload failed. Check server logs."))
                    else:
                        # If backend returns truthy value (like new book id)
                        st.success("Uploaded successfully.")
                        _safe_rerun()

                except Exception as e:
                    st.error(f"Upload failed: {e}")
                    st.text(str(e))
        else:
            # No backend upload function available — redirect to upload page
            st.info("Upload handler not found in backend. Redirecting to Upload page for full upload flow.")
            navigate("upload")

    st.markdown("</div>", unsafe_allow_html=True)


def format_datetime(dt):
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)

def draw_metrics(db, user):
    """Top metrics (no topbar rendering here)."""
    with db.begin():
        total_books = db.query(crud.Book).filter(crud.Book.user_id == user["id"]).count()
        total_summaries = db.query(crud.Summary).filter(crud.Summary.user_id == user["id"]).count()

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            "<div class='metric-box'><div style='font-size:18px;font-weight:700'>{}</div>"
            "<div class='helper'>Your books</div></div>".format(total_books),
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            "<div class='metric-box'><div style='font-size:18px;font-weight:700'>{}</div>"
            "<div class='helper'>Summaries</div></div>".format(total_summaries),
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            "<div class='metric-box'><div style='font-size:18px;font-weight:700'>{}</div>"
            "<div class='helper'>Last updated</div></div>".format(format_datetime(datetime.utcnow())),
            unsafe_allow_html=True,
        )

def book_card(book, is_owner, is_admin):
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown(f"### {book.title or 'Untitled'}")
    st.markdown(f"<div class='helper'>Author: {book.author or '—'}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='helper'>Status: <strong>{getattr(book,'status','unknown')}</strong> • Uploaded: {format_datetime(getattr(book,'upload_date', ''))}</div>",
        unsafe_allow_html=True,
    )
    if getattr(book, "word_count", None):
        st.markdown(f"<div class='helper'>Words: {book.word_count}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([0.6, 0.4])

    with col1:
        # unique keys per book
        if st.button("View details", key=f"dashboard_view_{book.id}"):
            st.session_state["selected_book_id"] = book.id
            navigate("book_detail")

        if st.button("Generate summary", key=f"dashboard_gen_{book.id}"):
            st.session_state["selected_book_id"] = book.id
            navigate("generate_summary")

    with col2:
        if (is_owner or is_admin) and st.button("Delete", key=f"dashboard_del_{book.id}"):
            st.session_state["confirm_delete_book"] = book.id
            _safe_rerun()

    if st.session_state.get("confirm_delete_book") == book.id:
        st.error(f"Are you sure you want to delete **{book.title}**?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete permanently", key=f"dashboard_yes_del_{book.id}"):
                try:
                    db = SessionLocal()
                    obj = db.query(crud.Book).get(book.id)
                    if obj:
                        db.delete(obj)
                        db.commit()
                        db.close()
                        st.success("Book deleted.")
                        st.session_state.pop("confirm_delete_book", None)
                        _safe_rerun()
                    else:
                        st.error("Book not found.")
                except Exception as e:
                    st.error(f"Failed to delete: {e}")
        with c2:
            if st.button("Cancel", key=f"dashboard_cancel_del_{book.id}"):
                st.session_state.pop("confirm_delete_book", None)
                _safe_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

def render_book_list(db, user):
    st.subheader("Your Books")

    # widget keys namespaced to dashboard to avoid collisions
    q = st.text_input("Search by title or author", key="dashboard_search_q")
    status_filter = st.selectbox(
        "Filter by status", ["all", "uploaded", "text_extracted", "summarized"], key="dashboard_status_filter"
    )
    per_page = st.selectbox("Items per page", [5, 10, 20], index=1, key="dashboard_per_page")

    query = db.query(crud.Book).filter(crud.Book.user_id == user["id"])
    if q:
        like = f"%{q.lower().strip()}%"
        query = query.filter((crud.Book.title.ilike(like)) | (crud.Book.author.ilike(like)))
    if status_filter != "all":
        query = query.filter(crud.Book.status == status_filter)

    page = st.session_state.get("dashboard_books_page", 0)
    total = query.count()
    books = query.order_by(crud.Book.upload_date.desc()).offset(page * per_page).limit(per_page).all()

    for book in books:
        is_owner = (book.user_id == user["id"])
        is_admin = (user.get("role") == "admin")
        book_card(book, is_owner, is_admin)

    c1, c2, c3 = st.columns([0.2, 0.6, 0.2])
    with c1:
        if st.button("Prev", key="dashboard_prev_books"):
            if page > 0:
                st.session_state["dashboard_books_page"] = page - 1
                _safe_rerun()
    with c3:
        if st.button("Next", key="dashboard_next_books"):
            if (page + 1) * per_page < total:
                st.session_state["dashboard_books_page"] = page + 1
                _safe_rerun()

    st.markdown(f"<br><div class='helper'>Showing {len(books)} of {total}</div>", unsafe_allow_html=True)

def main():
    # Do NOT render topbar/sidebar here — app.py already does that once
    # Enforce session and get user
    _ = session_is_active(st)
    user = require_login(st)
    if not user:
        st.warning("Please sign in to access your dashboard.")
        if st.button("Go to Sign in", key="dashboard_go_signin_btn"):
            navigate("login")
        return

    # Header (page content only)
    st.markdown("<div class='app-card'>", unsafe_allow_html=True)
    st.markdown(f"<h2>Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='helper'>Welcome back, <strong>{user['username']}</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Database session and main content
    db = SessionLocal()
    try:
        # --- Metrics at the top ---
        draw_metrics(db, user)

        # --- INLINE UPLOAD SECTION (added here) ---
        render_inline_upload()

        # --- Book list below upload section ---
        render_book_list(db, user)

    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
