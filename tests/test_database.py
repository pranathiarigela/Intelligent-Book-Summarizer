import sqlite3
import json
import pytest
from pathlib import Path

from utils import database as dbmod

# --- Fixtures ---------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Return a path to a temporary sqlite file for each test run."""
    p = tmp_path / "test_summarizer.db"
    return str(p)

@pytest.fixture
def conn(db_path: str):
    """Initialize DB schema and provide a connection; close at teardown."""
    # create file parent dir if needed (tmp_path already exists)
    dbmod.init_db(db_path)
    conn = dbmod.connect_db(db_path)
    try:
        yield conn
    finally:
        conn.close()

# --- Tests -----------------------------------------------------------------
def test_init_db_creates_tables(db_path: str):
    """init_db should create the expected tables and indexes."""
    dbmod.init_db(db_path)
    conn = dbmod.connect_db(db_path)
    cur = conn.cursor()

    # check tables exist by querying sqlite_master
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cur.fetchall()}
    assert "Users" in tables, "Users table not created"
    assert "Books" in tables, "Books table not created"
    assert "Summaries" in tables, "Summaries table not created"

    # check indexes exist (at least one known index)
    cur.execute("PRAGMA index_list('Users');")
    user_indexes = cur.fetchall()
    assert any("idx_users_email" in (row[1] or "") for row in user_indexes), "Users email index missing"

    conn.close()

def test_create_user_and_unique_email(conn):
    """create_user should return an id and enforce unique email constraint."""
    # create first user
    user_id = dbmod.create_user(conn, "Test User", "test@example.com", "password123", role="user")
    assert isinstance(user_id, int) and user_id > 0

    # fetching by email should work
    user = dbmod.get_user_by_email(conn, "test@example.com")
    assert user is not None
    assert user["user_id"] == user_id
    assert user["email"] == "test@example.com"

    # creating another user with same email should raise sqlite3.IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        dbmod.create_user(conn, "Other", "test@example.com", "different", role="user")

def test_verify_user_password(conn):
    """verify_user_password should return True for correct password, False otherwise."""
    email = "pwtest@example.com"
    pw = "My$ecret"
    user_id = dbmod.create_user(conn, "PW Tester", email, pw)
    assert dbmod.verify_user_password(conn, email, pw) is True
    assert dbmod.verify_user_password(conn, email, "wrongpassword") is False
    # non-existing user should return False
    assert dbmod.verify_user_password(conn, "noone@example.com", "whatever") is False

def test_create_book_and_update_status(conn):
    """create_book should insert a book row and update_book_status should change status."""
    # prepare user
    user_id = dbmod.create_user(conn, "Book Owner", "owner@example.com", "pass")
    # create book
    book_id = dbmod.create_book(conn, user_id, title="Sample Book", author="Author Name")
    assert isinstance(book_id, int) and book_id > 0

    # verify initial status is 'uploaded' (default)
    cur = conn.cursor()
    cur.execute("SELECT status, title, user_id FROM Books WHERE book_id = ?;", (book_id,))
    row = cur.fetchone()
    assert row is not None
    assert row["status"] == "uploaded"
    assert row["title"] == "Sample Book"
    assert row["user_id"] == user_id

    # update status
    dbmod.update_book_status(conn, book_id, "processing")
    cur.execute("SELECT status FROM Books WHERE book_id = ?;", (book_id,))
    row2 = cur.fetchone()
    assert row2["status"] == "processing"

    # try invalid book id update (should not raise, but no rows change)
    dbmod.update_book_status(conn, 99999, "failed")  # harmless

def test_create_summary_and_get_summaries_by_user(conn):
    """create_summary should insert a summary and get_summaries_by_user should return it."""
    # prepare user and book
    user_id = dbmod.create_user(conn, "Summary User", "summ@example.com", "pwd")
    book_id = dbmod.create_book(conn, user_id, title="Book For Summary", author="Auth")
    # create a summary with chunk_summaries list
    chunks = ["chunk one", "chunk two"]
    summary_id = dbmod.create_summary(
        conn,
        book_id=book_id,
        user_id=user_id,
        summary_text="This is the summary.",
        summary_length="short",
        summary_style="paragraphs",
        chunk_summaries=chunks,
        processing_time=1.23
    )
    assert isinstance(summary_id, int) and summary_id > 0

    # retrieve summaries
    summaries = dbmod.get_summaries_by_user(conn, user_id)
    assert isinstance(summaries, list)
    assert any(s["summary_id"] == summary_id for s in summaries), "Created summary not found for user"

    # find the created summary and verify fields
    s = next(s for s in summaries if s["summary_id"] == summary_id)
    assert s["summary_text"] == "This is the summary."
    assert s["summary_length"] == "short"
    assert s["summary_style"] == "paragraphs"
    assert isinstance(s.get("chunk_summaries"), list)
    assert s["chunk_summaries"] == chunks

    # check processing_time is stored (within tolerance)
    assert abs(float(s["processing_time"]) - 1.23) < 1e-6
