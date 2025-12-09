# frontend/dashboard.py
import streamlit as st
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List

# Import navigation helpers (shared UI + session)
from frontend.navigation import (
    ensure_session_state_keys,
    header,
    sidebar_nav,
    set_page,
    pretty_time_ago,
)

# Import DB helpers from your upload module (re-uses its init/db functions)
# upload.py provides: init_db, get_all_books, insert_book, get_recent etc.
try:
    from frontend import upload as upload_mod
except Exception:
    # Fallback if import path differs
    import upload as upload_mod  # type: ignore

# Ensure the DB exists (upload.py already calls init_db when run directly;
# calling again is idempotent)
try:
    if hasattr(upload_mod, "init_db"):
        upload_mod.init_db()
except Exception:
    # ignore DB init errors here; upload page will show DB errors as needed
    pass

def backend_get_current_user() -> Dict[str, Any] | None:
    """Return user dict from session or None if not logged in."""
    if st.session_state.get("logged_in"):
        return {
            "user_id": st.session_state.get("user_id"),
            "name": st.session_state.get("user_name") or st.session_state.get("user_email", "User"),
            "email": st.session_state.get("user_email"),
            "role": st.session_state.get("user_role", "user"),
        }
    return None

def backend_get_stats(user_id: str) -> Dict[str, Any]:
    """Generate quick stats from the upload DB. Keeps graceful fallbacks."""
    stats = {"total_books": 0, "total_summaries": 0, "last_upload": None, "last_summary": None, "storage_used_mb": 0.0}
    try:
        rows = upload_mod.get_all_books()
        stats["total_books"] = len(rows)
        # Count summaries where summary_id is not null
        stats["total_summaries"] = sum(1 for r in rows if r[8])  # summary_id index in select
        if rows:
            # rows are ordered by uploaded_at DESC in upload.get_all_books()
            try:
                last_upload_raw = rows[0][6]  # uploaded_at column
                # uploaded_at in upload.py is stored as ISO string; try parse
                if isinstance(last_upload_raw, str):
                    stats["last_upload"] = datetime.fromisoformat(last_upload_raw)
                else:
                    stats["last_upload"] = last_upload_raw
            except Exception:
                stats["last_upload"] = None
        # approximate storage used by summing filesize
        try:
            stats["storage_used_mb"] = sum((r[5] or 0) for r in rows) / (1024 * 1024)
        except Exception:
            stats["storage_used_mb"] = 0.0
    except Exception:
        # DB error — keep defaults and show message in UI
        pass
    return stats

def backend_get_recent_activity(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Build a simple recent activity feed from the DB rows (uploads/summaries/deletes)."""
    acts: List[Dict[str, Any]] = []
    try:
        rows = upload_mod.get_all_books()
        # Convert rows to activity entries (upload & summary existence)
        for r in rows[:limit]:
            book_id, title, author, chapter, filename, filesize, uploaded_at, status, summary_id = r
            ts = None
            try:
                ts = datetime.fromisoformat(uploaded_at) if isinstance(uploaded_at, str) else uploaded_at
            except Exception:
                ts = None
            acts.append({"type": "upload", "title": title or filename, "timestamp": ts})
            if summary_id:
                acts.append({"type": "summary", "title": title or filename, "timestamp": ts})
        # keep only the requested number of items
        acts = acts[:limit]
    except Exception:
        pass
    return acts

def backend_get_recent_books(user_id: str, limit: int = 3):
    """Return the last N uploaded books for quick cards."""
    try:
        rows = upload_mod.get_all_books()
        out = []
        for r in rows[:limit]:
            book_id, title, author, chapter, filename, filesize, uploaded_at, status, summary_id = r
            ts = None
            try:
                ts = datetime.fromisoformat(uploaded_at) if isinstance(uploaded_at, str) else uploaded_at
            except Exception:
                ts = None
            out.append({
                "book_id": book_id,
                "title": title or filename,
                "uploaded_at": ts,
                "has_summary": bool(summary_id),
                "summary_id": summary_id,
            })
        return out
    except Exception:
        return []

# -------------------------
# Dashboard UI
# -------------------------
def render_dashboard(user: Dict[str, Any]):
    st.title("Dashboard")

    # Quick stats with spinner
    with st.spinner("Loading stats..."):
        time.sleep(0.18)
        stats = backend_get_stats(user.get("user_id"))

    st.subheader("Quick Stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total books", stats.get("total_books", 0))
    c2.metric("Total summaries", stats.get("total_summaries", 0))
    c3.metric("Last upload", pretty_time_ago(stats.get("last_upload")))
    c4.metric("Storage used (MB)", f"{stats.get('storage_used_mb', 0):.1f}")

    st.markdown("---")
    st.subheader("Quick actions")
    a1, a2, a3 = st.columns([1, 1, 1])
    if a1.button("Upload new book"):
        set_page("upload")
    if a2.button("View all summaries"):
        set_page("summaries")
    if a3.button("My books"):
        set_page("my_books")

    st.markdown("### Recent books")
    recent_books = backend_get_recent_books(user.get("user_id"), limit=3)
    if not recent_books:
        st.info("You have no uploaded books yet. Click Upload new book to get started.")
    else:
        for b in recent_books:
            cols = st.columns([0.6, 0.2, 0.2])
            cols[0].markdown(f"**{b['title']}**  \n<small>Uploaded {pretty_time_ago(b['uploaded_at'])}</small>", unsafe_allow_html=True)
            if b.get("has_summary"):
                if cols[1].button("View summary", key=f"vs_{b['book_id']}"):
                    # store navigation payload for summary page (implement summary page to use this)
                    st.session_state["selected_summary_id"] = b.get("summary_id")
                    set_page("summaries")
            else:
                if cols[2].button("Generate", key=f"gen_{b['book_id']}"):
                    # Example placeholder: update DB status to 'processing' and instruct backend
                    try:
                        if hasattr(upload_mod, "update_book_status"):
                            upload_mod.update_book_status(b["book_id"], "processing")
                    except Exception:
                        pass
                    st.info("Triggered generation (implement backend job trigger).")

    st.markdown("---")
    st.subheader("Recent activity")
    with st.spinner("Fetching recent activity..."):
        time.sleep(0.12)
        activities = backend_get_recent_activity(user.get("user_id"), limit=10)

    if not activities:
        st.info("No recent activity. Try uploading a book.")
    else:
        for act in activities:
            icon = {"upload": "⬆️", "summary": "📝", "delete": "🗑️"}.get(act["type"], "ℹ️")
            st.markdown(f"{icon} **{act['type'].capitalize()}** — *{act['title']}*  \n<small>{pretty_time_ago(act['timestamp'])}</small>", unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("Quick tips and first-time user guide"):
        st.write(
            "• Upload books in PDF, DOCX, or TXT format.\n\n"
            "• If no summaries exist, open a book and click Generate summary.\n\n"
            "• Use Settings to adjust summary length and style."
        )

def main():
    ensure_session_state_keys()

    # Respect query params (back button friendly)
    params = st.query_params
    if "page" in params:
        st.session_state["page"] = params["page"]

    user = backend_get_current_user()
    if not user:
        st.warning("You must be logged in to view the dashboard.")
        if st.button("Go to Login"):
            # navigate to your auth page
            # if your auth page is at frontend/auth.py, set query param or rerun to show it.
            # simplest: clear page param and rerun; running streamlit with login file directly is common for dev.
            st.query_params.clear()
            st.rerun()
        st.stop()

    # header + sidebar
    header(user)
    sidebar_nav(user)

    page = st.session_state.get("page", "dashboard")
    if page == "dashboard":
        render_dashboard(user)
    elif page == "upload":
        # delegate to your upload page (you already have frontend/upload.py)
        st.title("Upload Book")
        st.info("Upload page is implemented in frontend/upload.py. Run that page directly or wire to a multipage app.")
    elif page == "my_books":
        st.title("My Books")
        st.info("This view can be implemented to list books and actions. Upload file provides DB helpers.")
    elif page == "summaries":
        st.title("Summaries")
        st.info("Implement summaries list and single-summary view.")
    elif page == "settings":
        st.title("Settings")
        st.info("User preferences page (implement).")
    elif page == "help":
        st.title("Help & Documentation")
        st.info("Add FAQs and docs here.")
    elif page == "manage_users":
        if user.get("role") != "admin":
            st.error("Access denied. Admins only.")
        else:
            st.title("Manage Users")
            st.info("Admin user management (implement).")
    else:
        st.error("Unknown page. Returning to dashboard.")
        set_page("dashboard")

if __name__ == "__main__":
    main()
