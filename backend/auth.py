from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db
from .db_models import User


# ---------- REGISTER ----------
def register_user(username, email, password, role="user"):
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return False, "User already exists"

    password_hash = generate_password_hash(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role
    )

    db.session.add(user)
    db.session.commit()
    return True, "User registered successfully"


# ---------- LOGIN ----------
def login_user(email, password):
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return False, "Invalid credentials"

    session["user_id"] = user.user_id
    session["role"] = user.role
    session.permanent = True

    return True, "Login successful"


# ---------- LOGOUT ----------
def logout_user():
    session.clear()


# ---------- SESSION HELPERS ----------
def is_logged_in():
    return "user_id" in session


def current_user_id():
    return session.get("user_id")


def is_admin():
    return session.get("role") == "admin"
