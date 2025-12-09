# utils/database.py
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_UPLOADS_DB = "data/uploads.db"
DEFAULT_SUMMARIZER_DB = "data/summarizer.db"


def _connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_uploads_db(db_path: str = DEFAULT_UPLOADS_DB) -> None:
    """
    Ensure the uploads DB and the 'books' table have the columns frontend expects.
    This function is safe to call repeatedly.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        # Create base table (matches frontend/upload.py) if missing
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
                summary_id TEXT
            )
            """
        )
        conn.commit()

        # Add optional extraction columns if they don't exist:
        existing_cols = {row["name"] for row in cur.execute("PRAGMA table_info(books)").fetchall()}
        # desired extra columns
        extras = {
            "raw_text": "TEXT",
            "word_count": "INTEGER",
            "char_count": "INTEGER",
            "extraction_time": "REAL",
            "extra": "TEXT"
        }
        for col, coltype in extras.items():
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE books ADD COLUMN {col} {coltype}")
        conn.commit()
    finally:
        conn.close()


def init_summarizer_db(db_path: str = DEFAULT_SUMMARIZER_DB) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                user_id TEXT,
                summary_text TEXT,
                summary_length TEXT,
                summary_style TEXT,
                chunk_summaries TEXT,
                created_at TEXT,
                processing_time REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
