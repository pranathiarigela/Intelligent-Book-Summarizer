# utils/db_hooks.py
import sqlite3
import json
from typing import Optional, Dict, Any

DB_PATH = "data/app.db"  # change to your DB path

def _get_conn():
    # use detect_types if you later want to store JSON natively
    return sqlite3.connect(DB_PATH, timeout=30)

def ensure_books_table():
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                file_path TEXT,
                raw_text TEXT,
                word_count INTEGER,
                char_count INTEGER,
                status TEXT,
                extraction_time REAL,
                extra TEXT
            )
            """
        )
        conn.commit()

def update_book_text(
    book_id: str,
    raw_text: str,
    word_count: int,
    char_count: int,
    status: str,
    extraction_time: float,
    extra: Optional[Dict[str, Any]] = None,
):
    """
    Hook used by backend.text_extractor.extract_text

    - Inserts or updates the books table with extraction results.
    """
    ensure_books_table()
    extra_json = json.dumps(extra or {})
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO books (id, raw_text, word_count, char_count, status, extraction_time, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                raw_text=excluded.raw_text,
                word_count=excluded.word_count,
                char_count=excluded.char_count,
                status=excluded.status,
                extraction_time=excluded.extraction_time,
                extra=excluded.extra
            """,
            (book_id, raw_text, word_count, char_count, status, extraction_time, extra_json),
        )
        conn.commit()
