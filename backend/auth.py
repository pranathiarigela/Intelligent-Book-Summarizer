# backend/auth.py
import sqlite3
import bcrypt
import re
import logging
import time
from datetime import datetime, timedelta, UTC,UTC

# Only import streamlit in functions that are used from the UI code.
import streamlit as st  # used only for session_state helpers

# Configure logger
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# Simple in-memory rate limiter and failed-attempts log.
# Note: this is process-local. For multi-process deployment use Redis or DB-backed counters.
_failed_attempts = {}
LOCKOUT_SECONDS = 300  # lock out for 5 minutes after hitting max attempts
MAX_ATTEMPTS = 5


# -------------------------
# Database helpers
# -------------------------
def get_db_connection(db_path="data/app.db"):
    """
    Returns a sqlite3.Connection with rows as dicts.
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.exception("Database connection failed")
        raise


def init_user_table(db_path="data/app.db"):
    """
    Create users table if it doesn't exist.
    Call this at app startup or migration step.
    """
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
# Validation helpers
# -------------------------
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$")


def validate_name(name: str) -> (bool, str): # type: ignore
    if not name or not isinstance(name, str):
        return False, "Name is required."
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    if not re.fullmatch(r"[A-Za-z ]+", name):
        return False, "Name may contain only letters and spaces."
    return True, ""


def validate_email(email: str) -> (bool, str): # type: ignore
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email = email.strip()
    if not EMAIL_RE.match(email):
        return False, "Invalid email format."
    return True, ""


def validate_password(password: str) -> (bool, str): # type: ignore
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
# Rate limiting helpers
# -------------------------
def _record_failed_attempt(key: str):
    now = int(time.time())
    entry = _failed_attempts.get(key, {"count": 0, "first": now, "locked_until": 0})
    if entry.get("locked_until", 0) > now:
        # still locked
        _failed_attempts[key] = entry
        return

    entry["count"] = entry.get("count", 0) + 1
    if entry["count"] >= MAX_ATTEMPTS:
        entry["locked_until"] = now + LOCKOUT_SECONDS
        logger.warning(f"Locking out {key} until {entry['locked_until']}")
    _failed_attempts[key] = entry


def _check_locked(key: str) -> (bool, int): # type: ignore
    """
    Returns (is_locked, seconds_remaining)
    """
    now = int(time.time())
    entry = _failed_attempts.get(key)
    if not entry:
        return False, 0
    locked_until = entry.get("locked_until", 0)
    if locked_until > now:
        return True, locked_until - now
    # not locked, but stale counts older than LOCKOUT_SECONDS can be reset
    first = entry.get("first", now)
    if now - first > LOCKOUT_SECONDS:
        _failed_attempts.pop(key, None)
        return False, 0
    return False, 0


# -------------------------
# Core auth functions
# -------------------------
def register_user(name: str, email: str, password: str, db_path="data/app.db", role="user"):
    """
    Register a new user.
    Returns: dict {success: bool, message: str, user_id: int|None}
    """
    # Validate inputs server-side
    ok, msg = validate_name(name)
    if not ok:
        return {"success": False, "message": msg}
    ok, msg = validate_email(email)
    if not ok:
        return {"success": False, "message": msg}
    ok, msg = validate_password(password)
    if not ok:
        return {"success": False, "message": msg}

    # Hash password with bcrypt (work factor ~12)
    try:
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
    except Exception as e:
        logger.exception("Password hashing failed")
        return {"success": False, "message": "Internal error during password hashing."}

    conn = None
    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        # Check duplicate email
        cur.execute("SELECT user_id FROM users WHERE email = ?", (email.strip().lower(),))
        if cur.fetchone():
            return {"success": False, "message": "An account with that email already exists."}

        created_at = datetime.now(UTC).isoformat()
        with conn:
            cur.execute(
                "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash, role, created_at),
            )
            user_id = cur.lastrowid
        logger.info(f"User registered: {email} (id={user_id})")
        return {"success": True, "message": "Registration successful.", "user_id": user_id}
    except sqlite3.IntegrityError as ie:
        logger.exception("Database integrity error during registration")
        return {"success": False, "message": "Registration failed. Email may already exist."}
    except Exception as e:
        logger.exception("Registration failed")
        return {"success": False, "message": "Registration failed due to server error."}
    finally:
        if conn:
            conn.close()


def login_user(email: str, password: str, db_path="data/app.db"):
    """
    Verify credentials. Does not reveal whether email or password was incorrect.
    Returns: dict {success: bool, message: str, user: dict|None}
    On success: user contains keys user_id, name, email, role, created_at
    """
    # basic validation
    ok, msg = validate_email(email)
    if not ok:
        # Keep message generic for login operations
        return {"success": False, "message": "Invalid credentials."}

    # Check lockout
    locked, remaining = _check_locked(email.strip().lower())
    if locked:
        return {"success": False, "message": f"Too many failed attempts. Try again in {remaining} seconds."}

    conn = None
    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email, password_hash, role, created_at FROM users WHERE email = ?", (email.strip().lower(),))
        row = cur.fetchone()
        if not row:
            _record_failed_attempt(email.strip().lower())
            logger.warning(f"Failed login attempt for unknown email: {email}")
            # generic message
            return {"success": False, "message": "Invalid credentials."}

        stored_hash = row["password_hash"]
        # bcrypt wants bytes; stored_hash will be bytes when stored properly
        try:
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode("utf-8")
            password_ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash)
        except Exception:
            # If hash format is wrong, treat as failure but log internally
            logger.exception("Password verification failed due to unexpected hash format")
            password_ok = False

        if not password_ok:
            _record_failed_attempt(email.strip().lower())
            logger.info(f"Failed password for user_id={row['user_id']}")
            return {"success": False, "message": "Invalid credentials."}

        # Success: clear any failed attempts
        _failed_attempts.pop(email.strip().lower(), None)

        user = {
            "user_id": row["user_id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
            "created_at": row["created_at"],
        }
        logger.info(f"User logged in: {user['email']} (id={user['user_id']})")
        return {"success": True, "message": "Login successful.", "user": user}
    except Exception:
        logger.exception("Login operation failed")
        return {"success": False, "message": "Login failed due to server error."}
    finally:
        if conn:
            conn.close()


# -------------------------
# Streamlit session helpers
# -------------------------
SESSION_KEYS = ["logged_in", "user_id", "user_name", "user_email", "user_role", "login_time", "session_expires_at"]


def login_to_session(user: dict, session_duration_minutes: int = 60):
    """
    After authentication success, call this to populate Streamlit session_state.
    Example:
        login_to_session(user)
    user must be the dict returned under 'user' in login_user result.
    """
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["user_id"]
    st.session_state["user_name"] = user["name"]
    st.session_state["user_email"] = user["email"]
    st.session_state["user_role"] = user.get("role", "user")
    st.session_state["login_time"] = datetime.now(UTC).isoformat()
    expires = datetime.now(UTC) + timedelta(minutes=session_duration_minutes)
    st.session_state["session_expires_at"] = expires.isoformat()
    logger.info(f"Session started for user_id={user['user_id']}")


def is_logged_in() -> bool:
    """
    Check authentication state in Streamlit session.
    Also checks session expiration if set.
    """
    if not st.session_state.get("logged_in"):
        return False
    expires = st.session_state.get("session_expires_at")
    if expires:
        if datetime.now(UTC) > datetime.fromisoformat(expires):
            logout()
            return False
    return True


def get_current_user(db_path="data/app.db"):
    """
    Returns the current user info from DB based on session_state user_id.
    Returns dict or None.
    """
    if not st.session_state.get("logged_in"):
        return None
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    conn = None
    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email, role, created_at FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {"user_id": row["user_id"], "name": row["name"], "email": row["email"], "role": row["role"], "created_at": row["created_at"]}
    except Exception:
        logger.exception("Failed to fetch current user")
        return None
    finally:
        if conn:
            conn.close()


def logout(redirect_to_login: bool = False):
    """
    Clears session state and optionally redirect to login page.
    Use streamlit.experimental_rerun and st.experimental_set_query_params for page flow as needed.
    """
    for k in SESSION_KEYS:
        if k in st.session_state:
            del st.session_state[k]
    logger.info("Session cleared (logout)")

    # Optionally show a confirmation message in UI code that called this function.
    if redirect_to_login:
        # Basic redirect - depends on how you manage pages. A common pattern:
        try:
            st.experimental_set_query_params(page="login")
        except Exception:
            pass
        st.experimental_rerun()
