# utils/database.py
import sqlite3
import re
import json
import bcrypt
from datetime import datetime,UTC
from typing import Optional, List, Dict, Any

EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')

def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

def connect_db(db_path: str) -> sqlite3.Connection:
    """
    Connects to SQLite DB. Enables foreign keys and returns a connection with row factory.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str) -> None:
    """
    Create tables and indexes. Safe to call multiple times.
    """
    conn = connect_db(db_path)
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash BLOB NOT NULL,
        created_at TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','user'))
    );
    """)

    # Books table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        author TEXT,
        chapter TEXT,
        file_path TEXT,
        raw_text TEXT,
        uploaded_at TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('uploaded','processing','completed','failed')),
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );
    """)

    # Summaries table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Summaries (
        summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        summary_text TEXT NOT NULL,
        summary_length TEXT NOT NULL CHECK(summary_length IN ('short','medium','long')),
        summary_style TEXT NOT NULL CHECK(summary_style IN ('paragraphs','bullets')),
        chunk_summaries TEXT,
        created_at TEXT NOT NULL,
        processing_time REAL,
        FOREIGN KEY(book_id) REFERENCES Books(book_id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );
    """)

    # Indexes for performance (frequently queried fields)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON Users(email);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_books_user_id ON Books(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON Summaries(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_summaries_book_id ON Summaries(book_id);")

    conn.commit()
    conn.close()

# ---------------------------
# Validation & helpers
# ---------------------------
def _validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))

def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

# ---------------------------
# User functions
# ---------------------------
def create_user(conn: sqlite3.Connection, name: str, email: str, password: str, role: str = "user") -> int:
    """
    Creates a new user. Returns user_id.
    Raises ValueError on invalid input or sqlite3.IntegrityError for duplicates.
    """
    if not name or len(name.strip()) < 2:
        raise ValueError("Name must be at least 2 characters.")
    if not _validate_email(email):
        raise ValueError("Invalid email format.")

    password_bytes = password.encode("utf-8")
    # bcrypt gensalt default rounds are secure; adjust if needed
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    cur = conn.cursor()
    created_at = _utc_now_iso()
    try:
        cur.execute("""
            INSERT INTO Users (name, email, password_hash, created_at, role)
            VALUES (?, ?, ?, ?, ?);
        """, (name.strip(), email.strip().lower(), hashed, created_at, role))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        # likely duplicate email
        raise

def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Returns user dict (excluding password_hash). If not found, returns None.
    """
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, created_at, role FROM Users WHERE email = ?;", (email.strip().lower(),))
    row = cur.fetchone()
    return _row_to_dict(row)

def _get_user_with_hash(conn: sqlite3.Connection, email: str) -> Optional[sqlite3.Row]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM Users WHERE email = ?;", (email.strip().lower(),))
    return cur.fetchone()

def verify_user_password(conn: sqlite3.Connection, email: str, password: str) -> bool:
    """
    Verifies a plaintext password against stored bcrypt hash. Returns True/False.
    """
    row = _get_user_with_hash(conn, email)
    if not row:
        return False
    stored_hash = row["password_hash"]
    # bcrypt requires bytes
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

# ---------------------------
# Book functions
# ---------------------------
def create_book(conn: sqlite3.Connection, user_id: int, title: str, author: Optional[str] = None,
                chapter: Optional[str] = None, file_path: Optional[str] = None,
                raw_text: Optional[str] = None, status: str = "uploaded") -> int:
    """
    Inserts a book record; returns book_id.
    """
    if not title or not title.strip():
        raise ValueError("Title is required.")

    cur = conn.cursor()
    uploaded_at = _utc_now_iso()
    cur.execute("""
        INSERT INTO Books (user_id, title, author, chapter, file_path, raw_text, uploaded_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (user_id, title.strip(), author, chapter, file_path, raw_text, uploaded_at, status))
    conn.commit()
    return cur.lastrowid

def update_book_status(conn: sqlite3.Connection, book_id: int, status: str) -> None:
    """
    Update book processing status.
    """
    cur = conn.cursor()
    cur.execute("UPDATE Books SET status = ? WHERE book_id = ?;", (status, book_id))
    conn.commit()

def get_book_by_id(conn: sqlite3.Connection, book_id: int) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM Books WHERE book_id = ?;", (book_id,))
    row = cur.fetchone()
    return _row_to_dict(row)

# ---------------------------
# Summary functions
# ---------------------------
def create_summary(conn: sqlite3.Connection, book_id: int, user_id: int,
                   summary_text: str, summary_length: str, summary_style: str,
                   chunk_summaries: Optional[List[str]] = None,
                   processing_time: Optional[float] = None) -> int:
    """
    Inserts a summary row. chunk_summaries should be a list; it will be serialized to JSON.
    Returns summary_id.
    """
    if summary_length not in ("short", "medium", "long"):
        raise ValueError("Invalid summary_length.")
    if summary_style not in ("paragraphs", "bullets"):
        raise ValueError("Invalid summary_style.")
    created_at = _utc_now_iso()
    cs_json = json.dumps(chunk_summaries) if chunk_summaries is not None else None

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Summaries (book_id, user_id, summary_text, summary_length, summary_style, chunk_summaries, created_at, processing_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (book_id, user_id, summary_text, summary_length, summary_style, cs_json, created_at, processing_time))
    conn.commit()
    return cur.lastrowid

def get_summaries_by_user(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, b.title as book_title
        FROM Summaries s
        JOIN Books b ON s.book_id = b.book_id
        WHERE s.user_id = ?
        ORDER BY s.created_at DESC;
    """, (user_id,))
    rows = cur.fetchall()
    results = []
    for r in rows:
        d = _row_to_dict(r)
        # parse chunk_summaries JSON if present
        if d.get("chunk_summaries"):
            try:
                d["chunk_summaries"] = json.loads(d["chunk_summaries"])
            except Exception:
                d["chunk_summaries"] = None
        results.append(d)
    return results

# ---------------------------
# Convenience: close connection
# ---------------------------
def close_db(conn: sqlite3.Connection) -> None:
    conn.close()