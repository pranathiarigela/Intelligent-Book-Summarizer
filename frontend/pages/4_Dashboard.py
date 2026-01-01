import streamlit as st
from utils.api import get, post

# ---------------- AUTH VERIFICATION ----------------
me = get("/me")

if me.status_code != 200:
    st.session_state.logged_in = False
    st.warning("Session expired. Please login again.")
    st.switch_page("app.py")
    st.stop()

# Restore login state
st.session_state.logged_in = True

# ---------------- PAGE TITLE ----------------
st.title("📚 Dashboard")

# ---------- TOP ACTION BUTTON ----------
col_left, col_right = st.columns([8, 2])

with col_right:
    if st.button("📤 Upload Book"):
        st.switch_page("pages/3_Upload.py")

st.markdown("### 🔍 Search & Filter")

col1, col2, col3 = st.columns(3)

with col1:
    search_query = st.text_input("Search by title or author")

with col2:
    sort_option = st.selectbox(
        "Sort by",
        ["Newest", "Oldest", "Title A-Z", "Title Z-A"]
    )

with col3:
    summary_filter = st.selectbox(
        "Summary status",
        ["All", "Summarized", "Not summarized"]
    )

sort_map = {
    "Newest": "date_desc",
    "Oldest": "date_asc",
    "Title A-Z": "title_asc",
    "Title Z-A": "title_desc"
}

summary_map = {
    "All": "all",
    "Summarized": "summarized",
    "Not summarized": "not_summarized"
}

# ---------------- FETCH BOOKS ----------------
res = get("/books",
          params={
                "search": search_query,
                "sort": sort_map[sort_option],
                "summary": summary_map[summary_filter],
                "page": 1,
                "per_page": 10
            }
        )

if res.status_code != 200:
    st.error("Failed to load books.Status code:{res.status_code}")
    st.text(res.text)
    st.stop()

books = res.json().get("books", [])

if not books:
    st.info("No books uploaded yet.")
    st.stop()

# ---------------- BOOK LIST ----------------
for book in books:
    st.markdown(
        f"""
        <div class="card">
            <strong>{book['title']}</strong><br>
            <small>Status: {"✅ Summarized" if book["has_summary"] else "⏳ Not summarized"}</small>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    # -------- VIEW DETAILS --------
    with c1:
        if st.button("👁 View Details", key=f"d_{book['book_id']}"):
            details_res = get(f"/books/{book['book_id']}/details")

            if details_res.status_code == 200:
                details = details_res.json()
                st.info(
                    f"""
                    **File Type:** {details['file_type']}  
                    **Uploaded Date:** {details['uploaded_date']}  
                    **Words:** {details['word_count']}  
                    **Characters:** {details['char_count']}  
                    **Lines:** {details['line_count']}
                    """
                )
            else:
                st.error("Unable to fetch details")

    # -------- GENERATE SUMMARY --------
    with c2:
        if st.button("🧠 Generate Summary", key=f"s_{book['book_id']}"):
            st.session_state["selected_book_id"] = book["book_id"]
            st.switch_page("pages/5_Generate_Summary.py")
            if res.status_code == 200:
                st.success("Summary generated successfully")
            else:
                st.error("Failed to generate summary")

    # -------- DELETE BOOK --------
    with c3:
        if st.button("🗑 Delete", key=f"x_{book['book_id']}"):
            del_res = post(f"/books/{book['book_id']}/delete")

            if del_res.status_code == 200:
                st.warning("Book deleted")
                st.rerun()
            else:
                try:
                    st.error(del_res.json())
                except:
                    st.error(f"Delete failed (status {del_res.status_code})")

    st.markdown("---")
