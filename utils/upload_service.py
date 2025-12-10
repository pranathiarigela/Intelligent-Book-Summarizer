# utils/upload_service.py
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

from utils.file_storage import (
    allowed_file,
    file_size_ok,
    file_hash_bytes,
    save_file_bytes,
    MAX_FILE_BYTES,
)
from utils.database_sqlalchemy import DB_URL, SessionLocal
from utils import crud

# Try to import the new extractor meta function
extractor_meta = None
try:
    from backend.text_extractor import extract_text_from_path_meta  # type: ignore
    extractor_meta = extract_text_from_path_meta
except Exception:
    extractor_meta = None

# Pasted text limits
PASTED_TEXT_CHAR_LIMIT = 500_000  # 500k chars, configurable


def handle_file_upload(
    file_bytes: bytes,
    original_filename: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    file_type: Optional[str] = None,
    extra_meta: Optional[dict] = None,
    allow_ocr_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Validates, saves, extracts, and inserts book record.
    Returns dict: {"ok": bool, "message": str, "book_id": int (if ok), "duplicate": bool, ...}
    """
    # Validation
    if not original_filename:
        return {"ok": False, "message": "Missing filename."}
    if not allowed_file(original_filename):
        return {"ok": False, "message": "Unsupported file type."}
    if not file_size_ok(file_bytes):
        return {"ok": False, "message": f"File exceeds maximum size of {MAX_FILE_BYTES} bytes."}

    # Hash for duplicate detection
    fhash = file_hash_bytes(file_bytes)
    db = SessionLocal()
    try:
        # Simple duplicate detection by extra JSON file_hash field (fallback scanning)
        existing = None
        try:
            # If Book.extra is JSON type and supports lookup, use it; otherwise fallback
            existing = (
                db.query(crud.Book)
                .filter(crud.Book.extra["file_hash"].as_string() == fhash)
                .first()
            )
        except Exception:
            # fallback: scan small number of books for matching extra
            all_books = db.query(crud.Book).filter(crud.Book.extra != None).limit(200).all()
            for b in all_books:
                try:
                    if (b.extra or {}).get("file_hash") == fhash:
                        existing = b
                        break
                except Exception:
                    continue
        if existing:
            return {"ok": True, "message": "Duplicate file detected", "book_id": existing.id, "duplicate": True}
    finally:
        db.close()

    # Save file to disk
    stored_path = save_file_bytes(file_bytes, original_filename)

    # Extract text (prefer extractor_meta if available)
    extracted_text = ""
    word_count = 0
    pages = 0
    scanned = False
    ocr_performed = False

    if extractor_meta:
        try:
            meta = extractor_meta(stored_path, ocr=allow_ocr_fallback)
            extracted_text = meta.get("text", "") or ""
            pages = int(meta.get("pages", 0) or 0)
            scanned = bool(meta.get("scanned", False))
            ocr_performed = bool(meta.get("ocr_performed", False))
        except Exception:
            # fallback naive extraction for txt
            try:
                if stored_path.lower().endswith(".txt"):
                    with open(stored_path, "r", encoding="utf-8", errors="ignore") as f:
                        extracted_text = f.read()
                else:
                    extracted_text = ""
            except Exception:
                extracted_text = ""
    else:
        # No advanced extractor available: attempt basic reading for .txt else leave empty
        try:
            if stored_path.lower().endswith(".txt"):
                with open(stored_path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
            else:
                extracted_text = ""
        except Exception:
            extracted_text = ""

    word_count = len(extracted_text.split()) if extracted_text else 0

    if scanned and not ocr_performed:
        # OCR is required but was not performed (likely missing libs), return instructive message
        return {
            "ok": False,
            "message": "PDF appears to be scanned (image-only). OCR is required to extract text. "
            "Install pytesseract and pdf2image (and Poppler) on the server or enable OCR fallback.",
            "ocr_required": True,
            "stored_path": stored_path,
        }

    # Persist book record via crud.create_book
        # Persist book record via crud.create_book (do NOT pass word_count if crud.create_book doesn't accept it)
    db = SessionLocal()
    try:
        # Call create_book without word_count to avoid signature mismatch
        book = crud.create_book(
            db=db,
            user_id=user_id,
            title=title or os.path.splitext(original_filename)[0],
            author=author,
            filename=stored_path,
            file_type=file_type or os.path.splitext(original_filename)[1].lstrip("."),
            original_text=extracted_text,
            extra={**(extra_meta or {}), "file_hash": fhash, "ocr_performed": ocr_performed, "pages": pages},
            # do NOT include word_count here
        )

        # If create_book returned an ORM object, attempt to set/update word_count and commit
        try:
            if book is not None:
                # Some crud implementations return the created object or a dict; handle both
                if hasattr(book, "word_count"):
                    book.word_count = word_count
                    db.add(book)
                    db.commit()
                else:
                    # If it's a dict-like response, try updating via query by book id
                    book_id = getattr(book, "id", None) or (book.get("id") if isinstance(book, dict) else None)
                    if book_id:
                        db.query(crud.Book).filter(crud.Book.id == book_id).update({"word_count": word_count})
                        db.commit()
        except Exception:
            # If updating word_count fails for any reason, rollback that change but keep the book
            try:
                db.rollback()
            except Exception:
                pass

        # Return success with created book id if available
        created_id = None
        if hasattr(book, "id"):
            created_id = book.id
        elif isinstance(book, dict):
            created_id = book.get("id")

        return {"ok": True, "message": "Uploaded and extracted", "book_id": created_id, "duplicate": False, "word_count": word_count}
    except Exception as e:
        # ensure DB rollback and return an error
        try:
            db.rollback()
        except Exception:
            pass
        return {"ok": False, "message": f"Failed to save book: {e}"}
    finally:
        try:
            db.close()
        except Exception:
            pass


def handle_pasted_text(
    pasted_text: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    extra_meta: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Validates pasted text and creates a book entry storing the text.
    """
    if not pasted_text or not isinstance(pasted_text, str) or not pasted_text.strip():
        return {"ok": False, "message": "Pasted text cannot be empty."}
    if len(pasted_text) > PASTED_TEXT_CHAR_LIMIT:
        return {"ok": False, "message": f"Pasted text exceeds limit of {PASTED_TEXT_CHAR_LIMIT} characters."}

    db = SessionLocal()
    try:
        book = crud.create_book(
            db=db,
            user_id=user_id,
            title=title or "Pasted text",
            author=author,
            filename=None,
            file_type="text",
            original_text=pasted_text,
            extra=extra_meta or {},
            # do not pass word_count here
        )
        # set word_count post-create
        try:
            if book is not None and hasattr(book, "word_count"):
                book.word_count = len(pasted_text.split())
                db.add(book)
                db.commit()
            else:
                book_id = getattr(book, "id", None) or (book.get("id") if isinstance(book, dict) else None)
                if book_id:
                    db.query(crud.Book).filter(crud.Book.id == book_id).update({"word_count": len(pasted_text.split())})
                    db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        word_count = len(pasted_text.split())
        created_id = getattr(book, "id", None) if book else None
        if isinstance(book, dict):
            created_id = book.get("id")

        return {"ok": True, "message": "Text saved", "book_id": created_id, "word_count": word_count}
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        return {"ok": False, "message": f"Failed to save pasted text: {e}"}
    finally:
        try:
            db.close()
        except Exception:
            pass
