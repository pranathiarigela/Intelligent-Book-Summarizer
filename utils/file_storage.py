# utils/file_storage.py
import os
import hashlib
import pathlib
import secrets
from typing import Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename: str) -> bool:
    if not filename:
        return False
    ext = pathlib.Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

def secure_filename(filename: str) -> str:
    # Create a short random prefix + original name sanitized
    name = pathlib.Path(filename).name
    rand = secrets.token_hex(8)
    safe = "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()
    return f"{rand}_{safe}"

def file_size_ok(file_bytes: bytes) -> bool:
    return len(file_bytes) <= MAX_FILE_BYTES

def file_hash_bytes(file_bytes: bytes, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    h.update(file_bytes)
    return h.hexdigest()

def save_file_bytes(file_bytes: bytes, original_filename: str) -> str:
    """Save bytes to uploads dir, return stored absolute path."""
    fname = secure_filename(original_filename)
    dest = os.path.join(UPLOADS_DIR, fname)
    # Avoid collisions by appending a short token if exists
    if os.path.exists(dest):
        base, ext = os.path.splitext(fname)
        dest = os.path.join(UPLOADS_DIR, f"{base}_{secrets.token_hex(6)}{ext}")
    with open(dest, "wb") as f:
        f.write(file_bytes)
    return dest
