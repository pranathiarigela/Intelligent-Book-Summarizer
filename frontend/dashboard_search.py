# frontend/dashboard_search.py
import streamlit as st
import sqlite3
import math
import pandas as pd
from datetime import datetime
from frontend.styles import apply
from utils.streamlit_helpers import safe_rerun
from utils.auth import require_login

apply()

DB_PATH = "data/app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def get_books(q="", search_by="title,author", date_from=None, date_to=None,
              status=None, sort_by="uploaded_at", order="desc",
              page=1, per_page=10, only_my_books=False, my_user_id=None):
    conn = get_conn()
    cur = conn.cursor()

    filters = []
    params = []

    # optional user restriction
    if only_my_books and my_user_id:
        filters.append("user_id = ?")
        params.append(str(my_user_id))

    # search
    if q:
        parts = [s.strip() for s in search_by.split(",")]
        clauses = []

        if "title" in parts:
            clauses.append("title LIKE ?")
            params.append(f"%{q}%")

        if "author" in parts:
            clauses.append("author LIKE ?")
            params.append(f"%{q}%")

        if "date" in parts:
            # If user typed a YYYY-MM-DD, match uploaded_at date
            try:
                dt = datetime.strptime(q, "%Y-%m-%d").date()
                filters.append("date(uploaded_at) = date(?)")
                params.append(str(dt))
            except Exception:
                # leave it as free text if parsing fails
                pass

        if clauses:
            filters.append("(" + " OR ".join(clauses) + ")")

    # date range filters
    if date_from:
        filters.append("date(uploaded_at) >= date(?)")
        params.append(date_from)

    if date_to:
        filters.append("date(uploaded_at) <= date(?)")
        params.append(date_to)

    # status filter
    if status:
        filters.append("status = ?")
        params.append(status)

    where_sql = " WHERE " + " AND ".join(filters) if filters else ""

    if sort_by not in ("uploaded_at", "title"):
        sort_by = "uploaded_at"
    order_sql = "ASC" if order == "asc" else "DESC"

    offset = (page - 1) * per_page

    # total
    cur.execute(f"SELECT COUNT(*) AS cnt FROM books {where_sql}", params)
    total = cur.fetchone()["cnt"] or 0

    cur.execute(
        f"""
        SELECT book_id, user_id, title, author, uploaded_at, status
        FROM books
        {where_sql}
        ORDER BY {sort_by} {order_sql}
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset]
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    total_pages = math.ceil(total / per_page) if per_page > 0 else 1
    return rows, total, total_pages

def delete_book(book_id):
    conn = get_conn()
    cur = conn.cursor()
    # optionally, fetch and delete file on disk if filepath column exists - keep simple here
    cur.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
    conn.commit()
    conn.close()

def mark_processing(book_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE books SET status='processing' WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()

def _init_state():
    defaults = {
        "search_q": "",
        "search_by": "title,author",
        "date_from": None,
        "date_to": None,
        "status_filter": "",
        "sort_by": "uploaded_at",
        "order": "desc",
        "per_page": 10,
        "page": 1,
        "only_my_books": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_filters():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.search_q = st.text_input("Search", value=st.session_state.search_q, placeholder="Title, Author or YYYY-MM-DD", key="search_q_dashboard")
    with col2:
        st.session_state.search_by = st.selectbox("Search by", ["title,author", "title", "author", "date"], index=["title,author","title","author","date"].index(st.session_state.search_by) if st.session_state.search_by in ["title,author","title","author","date"] else 0, key="search_by_dashboard")

    c1, c2, c3 = st.columns(3)
    with c1:
        # store dates as ISO strings or None
        date_from_val = None
        if st.session_state.date_from:
            try:
                date_from_val = datetime.strptime(st.session_state.date_from, "%Y-%m-%d").date()
            except Exception:
                date_from_val = None
        d1 = st.date_input("From", value=date_from_val, key="search_date_from")
        st.session_state.date_from = d1.strftime("%Y-%m-%d") if d1 else None

    with c2:
        date_to_val = None
        if st.session_state.date_to:
            try:
                date_to_val = datetime.strptime(st.session_state.date_to, "%Y-%m-%d").date()
            except Exception:
                date_to_val = None
        d2 = st.date_input("To", value=date_to_val, key="search_date_to")
        st.session_state.date_to = d2.strftime("%Y-%m-%d") if d2 else None

    with c3:
        st.session_state.status_filter = st.selectbox("Status", ["", "uploaded", "processing", "completed", "failed"], index=["","uploaded","processing","completed","failed"].index(st.session_state.status_filter) if st.session_state.status_filter in ["","uploaded","processing","completed","failed"] else 0, key="search_status")

    c4, c5 = st.columns([2, 1])
    with c4:
        st.session_state.only_my_books = st.checkbox("Only my books", value=st.session_state.only_my_books, key="only_my_books_dashboard")
    with c5:
        st.session_state.per_page = st.selectbox("Per page", [5, 10, 20, 50], index=[5,10,20,50].index(st.session_state.per_page) if st.session_state.per_page in [5,10,20,50] else 1, key="search_per_page")

    c6, c7 = st.columns([1.5, 1.5])
    with c6:
        st.session_state.sort_by = st.selectbox("Sort by", ["uploaded_at", "title"], index=["uploaded_at","title"].index(st.session_state.sort_by) if st.session_state.sort_by in ["uploaded_at","title"] else 0, key="search_sort")
    with c7:
        st.session_state.order = st.selectbox("Order", ["desc", "asc"], index=["desc","asc"].index(st.session_state.order) if st.session_state.order in ["desc","asc"] else 0, key="search_order")

    # Search button
    col_search = st.columns([1,3])[0]
    if col_search.button("Search", key="search_dashboard_btn"):
        st.session_state.page = 1
        safe_rerun()

def render_table_view(rows):
    if rows:
        df = pd.DataFrame(rows)
        # make sure uploaded_at is human-friendly
        if "uploaded_at" in df.columns:
            try:
                df["uploaded_at"] = pd.to_datetime(df["uploaded_at"]).dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        st.dataframe(df)
        # export button
        csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
        st.download_button("Export CSV", data=csv, file_name="books_search_results.csv", mime="text/csv", key="export_search_csv")
    else:
        st.info("No results found.")

def render_cards(rows, my_user_id=None):
    if not rows:
        st.info("No results found.")
        return

    for b in rows:
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.markdown(f"### {b.get('title') or 'Untitled'}")
        st.markdown(f"<div class='helper'>Author: {b.get('author') or '—'}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='helper'>Status: <strong>{b.get('status')}</strong> • Uploaded: {b.get('uploaded_at')}</div>", unsafe_allow_html=True)

        colA, colB, colC = st.columns([0.6, 0.6, 0.6])
        with colA:
            if st.button("View", key=f"search_view_{b['book_id']}"):
                st.write(b)
        with colB:
            if st.button("Generate summary", key=f"search_gen_{b['book_id']}"):
                mark_processing(b["book_id"])
                st.success("Summary generation started.")
        with colC:
            # show delete only if viewer is owner or admin
            current_user_id = st.session_state.get("user_id")
            current_role = st.session_state.get("user_role", "user")
            allowed = (str(current_user_id) == str(b.get("user_id"))) or (current_role == "admin")
            if allowed:
                if st.button("Delete", key=f"search_del_{b['book_id']}"):
                    st.session_state["_confirm_delete"] = b["book_id"]
        st.markdown("</div>", unsafe_allow_html=True)

    # handle confirmation outside loop to avoid nested widget collisions
    if st.session_state.get("_confirm_delete"):
        bid = st.session_state.get("_confirm_delete")
        st.warning("Are you sure you want to permanently delete this book?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", key="confirm_search_delete_yes"):
                delete_book(bid)
                st.session_state.pop("_confirm_delete", None)
                st.success("Book deleted.")
                safe_rerun()
        with c2:
            if st.button("Cancel", key="confirm_search_delete_no"):
                st.session_state.pop("_confirm_delete", None)
                safe_rerun()

def render_pagination(total_pages):
    colP1, colP2, colP3 = st.columns([0.2, 0.6, 0.2])
    if st.session_state.page > 1:
        if colP1.button("Previous", key="search_prev_btn"):
            st.session_state.page -= 1
            safe_rerun()
    colP2.write(f"Page {st.session_state.page}/{max(1, total_pages)}")
    if st.session_state.page < total_pages:
        if colP3.button("Next", key="search_next_btn"):
            st.session_state.page += 1
            safe_rerun()

def main():
    _init_state()
    st.title("Search & Filter Books")

    user = None
    try:
        user = require_login(st)
    except Exception:
        user = None

    # render filters
    render_filters()

    # fetch data
    rows, total, total_pages = get_books(
        q=st.session_state.search_q,
        search_by=st.session_state.search_by,
        date_from=st.session_state.date_from,
        date_to=st.session_state.date_to,
        status=st.session_state.status_filter if st.session_state.status_filter else None,
        sort_by=st.session_state.sort_by,
        order=st.session_state.order,
        page=st.session_state.page,
        per_page=st.session_state.per_page,
        only_my_books=st.session_state.only_my_books,
        my_user_id=st.session_state.get("user_id")
    )

    st.markdown(f"**Total results:** {total}")

    # layout selector
    layout = st.radio("Layout", ["Table", "Cards"], index=0, key="search_layout")

    if layout == "Table":
        render_table_view(rows)
    else:
        render_cards(rows, my_user_id=st.session_state.get("user_id"))

    render_pagination(total_pages)

if __name__ == "__main__":
    main()
