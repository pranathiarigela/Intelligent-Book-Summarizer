# utils/crud.py
from sqlalchemy.orm import Session
from .models import User, Book, Summary
from datetime import datetime
from typing import Optional, List

# USERS
def create_user(db: Session, username: str, email: str, password_hash: str, role: str = "user") -> User:
    user = User(username=username, email=email, password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).get(user_id)

# BOOKS
def create_book(db: Session, user_id: Optional[int], title: str, author: str, filename: str, file_type: str, original_text: Optional[str]=None, extra: Optional[dict]=None) -> Book:
    book = Book(
        user_id=user_id,
        title=title,
        author=author,
        filename=filename,
        file_type=file_type,
        original_text=original_text,
        word_count=(len(original_text.split()) if original_text else None),
        upload_date=datetime.utcnow(),
        status="uploaded",
        extra=extra or {}
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.query(Book).filter(Book.id == book_id).first()

def update_book_text(db: Session, book_id: int, original_text: str, status: str = "text_extracted", extra: Optional[dict]=None):
    book = get_book(db, book_id)
    if not book:
        return None
    book.original_text = original_text
    book.word_count = len(original_text.split()) if original_text else None
    book.status = status
    if extra:
        book.extra = extra
    db.commit()
    db.refresh(book)
    return book

def list_books_for_user(db: Session, user_id: int, offset: int = 0, limit: int = 50) -> List[Book]:
    return db.query(Book).filter(Book.user_id == user_id).order_by(Book.upload_date.desc()).offset(offset).limit(limit).all()

# SUMMARIES
def create_summary(db: Session, book_id: int, user_id: Optional[int], summary_text: str, summary_length: Optional[int], model_used: Optional[str], processing_time: Optional[float], chunk_summaries: Optional[list]):
    summary = Summary(
        book_id=book_id,
        user_id=user_id,
        summary_text=summary_text,
        summary_length=summary_length,
        model_used=model_used,
        processing_time=processing_time,
        chunk_summaries=chunk_summaries
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

def get_summaries_for_book(db: Session, book_id: int):
    return db.query(Summary).filter(Summary.book_id == book_id).order_by(Summary.generation_date.desc()).all()
