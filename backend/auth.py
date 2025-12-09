# backend/auth.py
import sqlite3
import bcrypt
import re
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("auth")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Defaults — keep these paths in sync with other modules
DEFAULT_DB = "data/app.db"

# Simple in-process rate limiting (keeps your previous behavior)
_failed_attempts = {}
LOCKOUT_SECONDS = 300
MAX_ATTEMPTS = 5

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}$")


def get_db_connection(db_path: str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_table(db_path: str = DEFAULT_DB) -> None:
    """Create users table if missing (idempotent)."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash BLOB NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL
                );
                """
            )
    finally:
        conn.close()


# -------------------------
# Validation helpers (same behaviour)
# -------------------------
def validate_name(name: str) -> (bool, str): # pyright: ignore[reportInvalidTypeForm]
    if not name or not isinstance(name, str):
        return False, "Name is required."
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    if not re.fullmatch(r"[A-Za-z ]+", name):
        return False, "Name may contain only letters and spaces."
    return True, ""


def validate_email(email: str) -> (bool, str): # pyright: ignore[reportInvalidTypeForm]
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email = email.strip()
    if not EMAIL_RE.match(email):
        return False, "Invalid email format."
    return True, ""


def validate_password(password: str) -> (bool, str): # pyright: ignore[reportInvalidTypeForm]
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include a lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must include a digit."
    if not re.search(r"[^\w\s]", password):
        return False, "Password must include a special character."
    return True, ""


# -------------------------
# Registration / Login API (frontend expects these)
# -------------------------
def register_user(
    name: str,
    email: str,
    password: str,
    db_path: str = DEFAULT_DB,
    role: str = "user",
) -> Dict[str, Any]:
    """Create new user. Returns dict with success/message."""
    ok, msg = validate_name(name)
    if not ok:
        return {"success": False, "message": msg}
    ok, msg = validate_email(email)
    if not ok:
        return {"success": False, "message": msg}
    ok, msg = validate_password(password)
    if not ok:
        return {"success": False, "message": msg}

    init_user_table(db_path)

    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email = ?", (email.strip().lower(),))
            if cur.fetchone():
                return {"success": False, "message": "Email already registered."}
            salt = bcrypt.gensalt()
            pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), email.strip().lower(), pw_hash, role, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return {"success": True, "message": "User registered."}
    except Exception as e:
        logger.exception("Registration failed")
        return {"success": False, "message": "Registration failed."}
    finally:
        conn.close()


def login_user(email: str, password: str, db_path: str = DEFAULT_DB) -> Dict[str, Any]:
    """
    Check credentials. Returns {'success': True, 'user': {...}} on success,
    or {'success': False, 'message': '...'} on failure.
    """
    key = f"login:{email}"
    now = int(time.time())
    # simple rate-limit
    attempts = _failed_attempts.get(key, {"count": 0, "first": now})
    if attempts["count"] >= MAX_ATTEMPTS and now - attempts["first"] < LOCKOUT_SECONDS:
        return {"success": False, "message": "Too many attempts. Try later."}

    if not email or not password:
        return {"success": False, "message": "Invalid credentials."}

    init_user_table(db_path)
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email, password_hash, role, created_at FROM users WHERE email = ?", (email.strip().lower(),))
        row = cur.fetchone()
        if not row:
            # record failed attempt
            _failed_attempts.setdefault(key, {"count": 0, "first": now})["count"] += 1
            return {"success": False, "message": "Invalid credentials."}

        pw_hash = row["password_hash"]
        if isinstance(pw_hash, str):
            # stored as hex string — try bytes
            pw_hash = pw_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), pw_hash):
            # success — reset attempts
            if key in _failed_attempts:
                _failed_attempts.pop(key, None)
            user = {
                "user_id": row["user_id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "created_at": row["created_at"],
            }
            return {"success": True, "user": user}
        else:
            _failed_attempts.setdefault(key, {"count": 0, "first": now})["count"] += 1
            return {"success": False, "message": "Invalid credentials."}
    except Exception:
        logger.exception("Login operation failed")
        return {"success": False, "message": "Login failed."}
    finally:
        conn.close()
