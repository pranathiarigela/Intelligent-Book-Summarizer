# utils/auth.py
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from utils import crud
from utils.database_sqlalchemy import SessionLocal

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 60  # change as desired

# ---------- Password helpers ----------
def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ---------- Registration / Authentication ----------
def register_user(username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
    db: Session = SessionLocal()
    try:
        existing = crud.get_user_by_username(db, username)
        if existing:
            return {"ok": False, "error": "username_taken"}
        # optional: check email uniqueness
        # existing_e = db.query(User).filter(User.email==email).first()
        # if existing_e: return {"ok":False, "error":"email_taken"}

        password_hash = hash_password(password)
        user = crud.create_user(db, username=username, email=email, password_hash=password_hash, role=role)
        return {"ok": True, "user": {"id": user.id, "username": user.username, "role": user.role}}
    finally:
        db.close()

def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
    """
    Try username first, then email.
    Returns dict: {"ok": True, "user": user_obj} or {"ok": False, "error": "invalid_credentials"}
    """
    db: Session = SessionLocal()
    try:
        # try username
        user = crud.get_user_by_username(db, username_or_email)
        if not user:
            # fallback by email
            user = db.query(crud.User).filter(crud.User.email == username_or_email).first()  # small fallback, avoid heavy queries
        if not user:
            return {"ok": False, "error": "invalid_credentials"}

        if not verify_password(password, user.password_hash):
            return {"ok": False, "error": "invalid_credentials"}

        # on success return minimal safe user info
        return {"ok": True, "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}
    finally:
        db.close()

# ---------- Session helpers (for Streamlit) ----------
def session_login_set(st, user_dict: dict):
    """
    store a minimal session for the logged-in user in st.session_state
    `st` is streamlit module, passed in so this file has no direct import of streamlit
    """
    st.session_state["user"] = {
        "id": user_dict["id"],
        "username": user_dict["username"],
        "email": user_dict.get("email"),
        "role": user_dict.get("role", "user"),
    }
    now = datetime.utcnow()
    st.session_state["session_started_at"] = now.isoformat()
    st.session_state["session_last_activity"] = now.isoformat()

def session_logout(st):
    # remove keys safely
    for k in ["user", "session_started_at", "session_last_activity"]:
        if k in st.session_state:
            del st.session_state[k]

def session_touch(st):
    """Update last activity time to now"""
    st.session_state["session_last_activity"] = datetime.utcnow().isoformat()

def session_is_active(st) -> bool:
    """Return False if session expired (based on last_activity)"""
    if "user" not in st.session_state:
        return False
    last = st.session_state.get("session_last_activity")
    if not last:
        return False
    last_dt = datetime.fromisoformat(last)
    if datetime.utcnow() - last_dt > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        # expired
        session_logout(st)
        return False
    return True

# ---------- Authorization helpers ----------
def require_login(st) -> Optional[dict]:
    """
    Call at top of each page. Returns user dict if logged-in and active, else None.
    Also updates last-activity timestamp if session active.
    """
    if not session_is_active(st):
        return None
    # refresh timestamp
    session_touch(st)
    return st.session_state.get("user")

def require_role(st, role: str) -> bool:
    """Return True if current user has at least the required role"""
    u = require_login(st)
    if not u:
        return False
    # simple role checks; for multi-level roles you may implement hierarchy
    return u.get("role") == role or u.get("role") == "admin"

# ---------- Admin-only check decorator (helper) ----------
def enforce_role_or_raise(st, role: str):
    """
    Use inside server-side actions. Raises ValueError if not allowed.
    """
    if not require_role(st, role):
        raise PermissionError("insufficient_permissions")
