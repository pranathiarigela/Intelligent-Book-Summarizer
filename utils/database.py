import sqlite3
from sqlite3 import Connection, Row
from pathlib import Path
import os
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def connect_db() -> Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect_db()
    cur = conn.cursor()
    # Users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    # Books table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        author TEXT,
        chapter TEXT,
        file_path TEXT,
        raw_text TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'uploaded',
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    ''')
    # Summaries table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS summaries (
        summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        user_id INTEGER,
        summary_text TEXT,
        summary_length TEXT,
        summary_style TEXT,
        chunk_summaries TEXT,
        processing_time REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(book_id) REFERENCES books(book_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized:", DB_PATH)
