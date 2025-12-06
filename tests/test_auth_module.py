# tests/test_auth_module.py
import os
import sqlite3
import tempfile
from backend import auth

def setup_function():
    global DB
    fd, DB = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    auth.init_user_table(DB)

def teardown_function():
    global DB
    try:
        os.remove(DB)
    except Exception:
        pass

def test_register_and_login_success():
    r = auth.register_user("Test User", "test1@example.com", "Abc@12345", db_path=DB)
    assert r["success"] is True
    assert "user_id" in r

    l = auth.login_user("test1@example.com", "Abc@12345", db_path=DB)
    assert l["success"] is True
    assert "user" in l
    assert l["user"]["email"] == "test1@example.com"

def test_duplicate_email_fails():
    auth.register_user("T", "dup@example.com", "Abc@12345", db_path=DB)
    r2 = auth.register_user("T", "dup@example.com", "Abc@12345", db_path=DB)
    assert r2["success"] is False

def test_invalid_password_rejected():
    r = auth.register_user("T", "p@example.com", "weak", db_path=DB)
    assert r["success"] is False
