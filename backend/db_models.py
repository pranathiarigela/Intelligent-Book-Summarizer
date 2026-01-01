from datetime import datetime
from .database import db

# -------------------- USERS --------------------
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    books = db.relationship("UserBook", backref="user", lazy=True)


# -------------------- BOOKS --------------------
class Book(db.Model):
    __tablename__ = "books"

    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    original_text = db.Column(db.Text, nullable=False)
    file_type = db.Column(db.String(20), nullable=False)

    content_hash = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("UserBook", backref="book", lazy=True)
    summaries = db.relationship("Summary", backref="book", lazy=True)


# -------------------- USER ↔ BOOK --------------------
class UserBook(db.Model):
    __tablename__ = "user_books"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "book_id", name="unique_user_book"),
    )


# -------------------- SUMMARIES (ONLY ONE) --------------------
class Summary(db.Model):
    __tablename__ = "summaries"
    __table_args__ = {"extend_existing": True}

    summary_id = db.Column(db.Integer, primary_key=True)

    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.book_id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    summary_text = db.Column(db.Text, nullable=False)
    summary_length = db.Column(db.Integer)

    model_used = db.Column(db.String(50))
    parameters = db.Column(db.JSON)
    version = db.Column(db.Integer, default=1)

    is_favorite = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
