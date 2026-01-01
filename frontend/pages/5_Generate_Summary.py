import streamlit as st
from utils.api import get, post,BASE_URL,get_file
import streamlit.components.v1 as components

st.set_page_config(page_title="Generate Summary", layout="wide")
st.title("🧠 Generate Summary")

# ---------------- AUTH CHECK ----------------
auth = get("/me")
if auth.status_code != 200:
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

# ---------------- INPUT MODE ----------------
st.subheader("Input Source")

input_mode = st.radio(
    "Choose how you want to generate a summary:",
    ["📚 Uploaded Book", "✍️ Paste Text"]
)

book_id = None
text_to_summarize = None

# ---------------- BOOK SELECTION ----------------
if input_mode == "📚 Uploaded Book":
    books_res = get("/books")
    books = books_res.json().get("books", [])

    if not books:
        st.info("No uploaded books found.")
        st.stop()

    book_map = {
        f"{b['title']} (ID {b['book_id']})": b["book_id"]
        for b in books
    }

    default_index = 0
    if "selected_book_id" in st.session_state:
        for i, (_, bid) in enumerate(book_map.items()):
            if bid == st.session_state["selected_book_id"]:
                default_index = i
                break

    selected_book = st.selectbox(
        "Select a book",
        list(book_map.keys()),
        index=default_index
    )

    book_id = book_map[selected_book]

# ---------------- TEXT INPUT ----------------
if input_mode == "✍️ Paste Text":
    text_to_summarize = st.text_area(
        "Paste text to summarize",
        height=250
    )

# ---------------- SUMMARY OPTIONS ----------------
st.subheader("Summary Options")

col1, col2, col3 = st.columns(3)

with col1:
    summary_length = st.selectbox("Length", ["Short", "Medium", "Long"])

with col2:
    summary_style = st.selectbox("Style", ["Paragraph", "Bullet Points"])

with col3:
    detail_level = st.selectbox("Detail Level", ["Concise", "Detailed"])

length_map = {
    "Short": 80,
    "Medium": 150,
    "Long": 250
}

detail_map = {
    "Concise": 1.0,
    "Detailed": 1.5
}

# ---------------- GENERATE ----------------
st.divider()

if st.button("🚀 Generate Summary", use_container_width=True):

    if input_mode == "✍️ Paste Text" and not text_to_summarize:
        st.error("Please paste some text.")
        st.stop()

    payload = {
        "max_length": length_map[summary_length],
        "detail_level": detail_map[detail_level],
        "style": summary_style.lower()
    }

    with st.spinner("Generating summary, please wait..."):
        if input_mode == "📚 Uploaded Book":
            response = post(f"/books/{book_id}/summarize", data=payload)
        else:
            response = post("/summarize-text", data={
                **payload,
                "text": text_to_summarize
            })

    if response.status_code != 200:
        st.error("Failed to generate summary")
        st.code(response.text)
        st.stop()

    result = response.json()
    summary_text = result.get("summary")

    if not summary_text:
        st.error("Summary not returned by server.")
        st.stop()

    # ---------------- DISPLAY ----------------
    st.subheader("📄 Generated Summary")

    st.text_area(
        "Summary",
        summary_text,
        height=250,
        label_visibility="collapsed"
    )

    summary_id = result.get("summary_id")

    if not summary_id:
        st.warning("Export options unavailable (summary ID missing).")
        st.stop()

    st.divider()
    st.subheader("⬇️ Export Options")

    col1, col2, col3 = st.columns(3)

    # ---------- DOWNLOAD TXT ----------
    with col1:
        txt_res = get_file(
            f"/summaries/{summary_id}/export?format=txt"
        )
        st.download_button(
            label="📄 Download TXT",
            data=txt_res.content,
            file_name="summary.txt",
            mime="text/plain",
            use_container_width=True
        )

    # ---------- DOWNLOAD PDF ----------
    with col2:
        pdf_res = get_file(
            f"/summaries/{summary_id}/export?format=pdf"
        )
        st.download_button(
            label="📕 Download PDF",
            data=pdf_res.content,
            file_name="summary.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # ---------- COPY TO CLIPBOARD (PURE JS – NO STREAMLIT BUTTON) ----------
    with col3:
        copy_html = f"""
        <button 
            onclick="navigator.clipboard.writeText(`{summary_text}`)"
            style="
                width:100%;
                padding:0.5rem;
                font-size:1rem;
                border-radius:8px;
                border:none;
                background-color:#4CAF50;
                color:white;
                cursor:pointer;
            "
        >
            📋 Copy Summary
        </button>
        """
        components.html(copy_html, height=60)