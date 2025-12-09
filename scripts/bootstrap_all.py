# utils/db_hooks.py
import sqlite3
import json
from typing import Optional, Dict, Any
from pathlib import Path

# write to uploads DB (frontend uses data/uploads.db)
DB_PATH = "data/uploads.db"

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=30)


def ensure_books_table():
    # delegates to utils.database migration logic if available; otherwise basic create
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                title TEXT,
                author TEXT,
                chapter TEXT,
                filename TEXT,
                filepath TEXT,
                filesize INTEGER,
                filehash TEXT,
                pages INTEGER,
                uploaded_at TIMESTAMP,
                status TEXT,
                summary_id TEXT,
                raw_text TEXT,
                word_count INTEGER,
                char_count INTEGER,
                extraction_time REAL,
                extra TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def update_book_text(
    book_id: int,
    raw_text: str,
    word_count: int,
    char_count: int,
    status: str,
    extraction_time: float,
    extra: Optional[Dict[str, Any]] = None,
):
    """
    Update the matching book row in data/uploads.db with extraction results.
    If the book id doesn't exist, insert a minimal row so UI can display it.
    """
    ensure_books_table()
    extra_json = json.dumps(extra or {})
    conn = _get_conn()
    try:
        cur = conn.cursor()
        # Check if book exists (id column is integer in uploads.db)
        cur.execute("SELECT 1 FROM books WHERE id = ?", (book_id,))
        if cur.fetchone():
            cur.execute(
                """
                UPDATE books
                SET raw_text = ?, word_count = ?, char_count = ?, status = ?, extraction_time = ?, extra = ?
                WHERE id = ?
                """,
                (raw_text, word_count, char_count, status, extraction_time, extra_json, book_id),
            )
        else:
            # insert a minimal placeholder record (keeps id deterministic with explicit id insert not supported for autoinc)
            cur.execute(
                """
                INSERT INTO books (id, raw_text, word_count, char_count, status, extraction_time, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (book_id, raw_text, word_count, char_count, status, extraction_time, extra_json),
            )
        conn.commit()
    finally:
        conn.close()
