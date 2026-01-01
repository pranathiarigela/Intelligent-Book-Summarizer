from functools import wraps
from flask import abort
from .auth import is_logged_in, is_admin


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            abort(401)
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in() or not is_admin():
            abort(403)
        return f(*args, **kwargs)
    return wrapper
