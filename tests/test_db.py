# tests/test_db.py
import pytest
from utils.database import create_user, get_user_by_email, create_book, verify_user_password

def test_create_user_and_book(db_conn):
    """
    Verify we can create a user and a book using the db_conn fixture.
    """
    # create user
    user_id = create_user(db_conn, name="Ammu Tester", email="ammu@example.com", password="Abc@12345!")
    assert isinstance(user_id, int) and user_id > 0

    # fetch user (excluding hash)
    user = get_user_by_email(db_conn, "ammu@example.com")
    assert user is not None
    assert user["email"] == "ammu@example.com"
    assert user["name"] == "Ammu Tester"

    # create a book for that user
    book_id = create_book(db_conn, user_id=user_id, title="AI Book")
    assert isinstance(book_id, int) and book_id > 0

def test_duplicate_email_fails(db_conn):
    """
    Creating the same email twice should raise sqlite3.IntegrityError.
    """
    create_user(db_conn, name="User1", email="dup@example.com", password="Abc@12345!")
    with pytest.raises(Exception):
        # create_user raises sqlite3.IntegrityError (a subclass of Exception) on duplicate
        create_user(db_conn, name="User2", email="dup@example.com", password="Abc@12345!")

def test_verify_password(db_conn):
    """
    verify_user_password should return True for correct password and False for wrong password.
    """
    email = "pwtest@example.com"
    password = "StrongP@ss1!"
    create_user(db_conn, name="Pw Tester", email=email, password=password)

    ok = verify_user_password(db_conn, email=email, password=password)
    assert ok is True

    wrong = verify_user_password(db_conn, email=email, password="wrongpass")
    assert wrong is False
