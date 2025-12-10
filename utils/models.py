# utils/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    func,
    Float,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import expression

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    books = relationship("Book", back_populates="owner", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="creator")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(500), nullable=True, index=True)
    author = Column(String(255), nullable=True, index=True)
    filename = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    original_text = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="uploaded", server_default="uploaded")
    extra = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="books")
    summaries = relationship("Summary", back_populates="book", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_books_title_author", "title", "author"),
    )

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    summary_text = Column(Text, nullable=False)
    summary_length = Column(Integer, nullable=True)  # number of words/characters
    model_used = Column(String(255), nullable=True)
    generation_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float, nullable=True)
    chunk_summaries = Column(JSON, nullable=True)

    book = relationship("Book", back_populates="summaries")
    creator = relationship("User", back_populates="summaries")
