"""
backend/text_extractor.py
Robust text extraction for TXT, PDF and DOCX files.

Dependencies (pip):
    pip install chardet python-docx pypdf pdfplumber

Optional (for OCR detection/helpful messaging):
    pip install pillow pytesseract

Notes:
- Database hook: expects a function `update_book_text(book_id, raw_text, word_count,
  char_count, status, extraction_time, extra=None)` available from your utils/database.py.
  Replace with your project's DB API.
"""

import os
import re
import time
import logging
from typing import Dict, Any, Optional

import chardet
from docx import Document

# pypdf (formerly PyPDF2). Try import; if missing fallbacks are handled below.
try:
    from pypdf import PdfReader # type: ignore
except Exception:
    PdfReader = None

# pdfplumber fallback
try:
    import pdfplumber
except Exception:
    pdfplumber = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ExtractionError(Exception):
    pass


class PasswordProtectedError(ExtractionError):
    pass


def _detect_encoding_and_read(path: str) -> str:
    """
    Detect text file encoding and return decoded content.
    Tries: UTF-8, detected encoding by chardet, latin-1 as fallback.
    """
    with open(path, "rb") as f:
        raw = f.read()

    # fast try utf-8
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # chardet detection
    result = chardet.detect(raw)
    encoding = result.get("encoding")
    if encoding:
        try:
            return raw.decode(encoding)
        except Exception:
            logger.warning("chardet suggested encoding %s but decode failed", encoding)

    # final fallback
    try:
        return raw.decode("latin-1")
    except Exception as e:
        raise ExtractionError(f"Unable to decode text file: {e}")


def extract_text_from_txt(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise ExtractionError("TXT file not found")

    text = _detect_encoding_and_read(file_path)
    return text


def _pdf_text_with_pypdf(file_path: str) -> Optional[str]:
    if PdfReader is None:
        return None

    try:
        reader = PdfReader(file_path)
    except Exception as e:
        # pypdf raises for password protected or corrupted files
        msg = str(e).lower()
        if "password" in msg or getattr(reader, "is_encrypted", False):
            raise PasswordProtectedError("PDF is password protected")
        raise ExtractionError(f"pypdf failed to open PDF: {e}")

    # If encrypted attribute exists
    if getattr(reader, "is_encrypted", False):
        # attempt to decrypt with empty password
        try:
            reader.decrypt("")
        except Exception:
            raise PasswordProtectedError("PDF is password protected")

    page_texts = []
    for page in reader.pages:
        try:
            txt = page.extract_text()
        except Exception:
            txt = None
        if txt:
            page_texts.append(txt)
        else:
            page_texts.append("")  # keep page slot for structure

    return "\n\n".join(page_texts)


def _pdf_text_with_pdfplumber(file_path: str) -> Optional[str]:
    if pdfplumber is None:
        return None

    texts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    t = page.extract_text()
                except Exception:
                    t = None
                if t:
                    texts.append(t)
                else:
                    texts.append("")  # preserve page break slots
    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect:
        raise PasswordProtectedError("PDF is password protected")
    except Exception as e:
        raise ExtractionError(f"pdfplumber failed: {e}")

    return "\n\n".join(texts)


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Try pypdf first; fall back to pdfplumber. Detect scanned PDFs and password protection.
    Returns a dict:
        {
            "text": "<extracted text>",
            "pages": int,
            "scanned": bool,   # True if looks like image-only PDF
            "password_protected": bool
        }
    """
    if not os.path.exists(file_path):
        raise ExtractionError("PDF file not found")

    # Attempt with pypdf
    try:
        text = _pdf_text_with_pypdf(file_path)
    except PasswordProtectedError:
        raise
    except Exception as e:
        logger.warning("pypdf extraction failed: %s", e)
        text = None

    # If pypdf returned None or empty, try pdfplumber
    if not text:
        try:
            text = _pdf_text_with_pdfplumber(file_path)
        except PasswordProtectedError:
            raise
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)
            text = None

    # If still no text, mark as scanned/image-based PDF
    scanned = False
    if not text or len(text.strip()) < 50:
        # try heuristic: check with pdfplumber for page images if available
        if pdfplumber is not None:
            try:
                with pdfplumber.open(file_path) as pdf:
                    page_count = len(pdf.pages)
                    image_pages = 0
                    for p in pdf.pages:
                        try:
                            if p.images:
                                image_pages += 1
                        except Exception:
                            pass
                    # if most pages have images and text is tiny, consider scanned
                    if page_count > 0 and image_pages / page_count > 0.5:
                        scanned = True
            except Exception:
                pass
        else:
            scanned = True

    pages = None
    # try to get page count
    try:
        if PdfReader is not None:
            reader = PdfReader(file_path)
            pages = len(reader.pages)
        elif pdfplumber is not None:
            with pdfplumber.open(file_path) as pdf:
                pages = len(pdf.pages)
    except Exception:
        pages = None

    return {"text": text or "", "pages": pages, "scanned": scanned, "password_protected": False}


def extract_text_from_docx(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise ExtractionError("DOCX file not found")

    try:
        doc = Document(file_path)
    except Exception as e:
        raise ExtractionError(f"python-docx failed to open file: {e}")

    parts = []

    # Extract headers and footers if present
    try:
        for section in doc.sections:
            hdr = section.header
            if hdr:
                for p in hdr.paragraphs:
                    if p.text:
                        parts.append(p.text)
    except Exception:
        # header extraction is optional; ignore failures
        pass

    # Paragraphs
    for para in doc.paragraphs:
        if para.text and para.text.strip():
            parts.append(para.text)

    # Tables
    for table in doc.tables:
        # each row -> join cells with ' | ' so we keep structure
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text)
            if row_text:
                parts.append(row_text)

    # Footers (optional)
    try:
        for section in doc.sections:
            ftr = section.footer
            if ftr:
                for p in ftr.paragraphs:
                    if p.text:
                        parts.append(p.text)
    except Exception:
        pass

    # Preserve section breaks by doubling newlines between parts
    return "\n\n".join(parts)


# Cleaning utilities
def _clean_text(raw: str) -> str:
    if raw is None:
        return ""

    # Normalize line breaks
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple blank lines with two (preserve paragraph spacing)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove control characters except newline and common whitespace
    text = "".join(ch for ch in text if (ch == "\n" or ch == "\t" or (32 <= ord(ch) <= 0x10FFFF)))

    # Trim trailing spaces on each line
    text = "\n".join(line.rstrip() for line in text.splitlines())

    # Collapse repeated spaces within lines to single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Strip leading/trailing
    text = text.strip("\n ")

    return text


def _calculate_stats(text: str) -> Dict[str, int]:
    words = re.findall(r"\S+", text)
    return {"word_count": len(words), "char_count": len(text)}


def extract_text(file_path: str, book_id: Optional[str] = None, db_update_hook=None) -> Dict[str, Any]:
    """
    Unified extraction entry point.

    Arguments:
        file_path: path to uploaded file
        book_id: optional id to update DB record
        db_update_hook: optional callable to update DB:
            db_update_hook(book_id, raw_text, word_count, char_count, status, extraction_time, extra=None)

    Returns:
        dict with keys:
          - success: bool
          - text: cleaned text (may be empty)
          - stats: {word_count, char_count}
          - meta: additional metadata (pages, scanned, source)
          - error: optional error message
    """
    start = time.perf_counter()
    result = {"success": False, "text": "", "stats": {"word_count": 0, "char_count": 0}, "meta": {}, "error": None}

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == ".txt":
            raw = extract_text_from_txt(file_path)
            source = "txt"
            meta = {}
        elif ext == ".pdf":
            pdf_res = extract_text_from_pdf(file_path)
            raw = pdf_res.get("text", "")
            meta = {"pages": pdf_res.get("pages"), "scanned": pdf_res.get("scanned")}
            source = "pdf"
            if pdf_res.get("password_protected"):
                raise PasswordProtectedError("PDF is password protected")
        elif ext in (".docx",):
            raw = extract_text_from_docx(file_path)
            meta = {}
            source = "docx"
        else:
            raise ExtractionError(f"Unsupported extension {ext}")

        cleaned = _clean_text(raw)

        if not cleaned:
            # empty after cleaning may mean scanned PDF or image-only doc
            # mark as extraction failure but provide helpful meta
            result["meta"] = meta
            result["error"] = "No extractable text found. Document may be image-only and require OCR."
            result["success"] = False
            status = "extraction_failed"
        else:
            stats = _calculate_stats(cleaned)
            result.update({"success": True, "text": cleaned, "stats": stats, "meta": meta})
            status = "text_extracted"

        # call DB hook if provided
        elapsed = time.perf_counter() - start
        result["meta"].update({"source": source, "extraction_time_s": round(elapsed, 3)})

        if db_update_hook and callable(db_update_hook) and book_id is not None:
            try:
                db_update_hook(
                    book_id=book_id,
                    raw_text=result["text"],
                    word_count=result["stats"]["word_count"],
                    char_count=result["stats"]["char_count"],
                    status=status,
                    extraction_time=round(elapsed, 3),
                    extra=result["meta"],
                )
            except Exception as e:
                logger.exception("Database update hook failed: %s", e)
                # not fatal to extraction result; still report it
                result.setdefault("warnings", []).append(f"db_update_failed: {e}")

    except PasswordProtectedError as e:
        logger.info("Password protected: %s", e)
        result["error"] = str(e)
        result["meta"]["password_protected"] = True
        result["success"] = False
        # update DB with failure if hook provided
        if db_update_hook and callable(db_update_hook) and book_id is not None:
            try:
                db_update_hook(book_id, raw_text="", word_count=0, char_count=0, status="extraction_failed", extraction_time=round(time.perf_counter()-start, 3), extra={"password_protected": True})
            except Exception:
                pass

    except ExtractionError as e:
        logger.exception("ExtractionError: %s", e)
        result["error"] = str(e)
        result["success"] = False
        if db_update_hook and callable(db_update_hook) and book_id is not None:
            try:
                db_update_hook(book_id, raw_text="", word_count=0, char_count=0, status="extraction_failed", extraction_time=round(time.perf_counter()-start, 3), extra={"error": str(e)})
            except Exception:
                pass

    except Exception as e:
        logger.exception("Unhandled extraction error: %s", e)
        result["error"] = f"Unhandled error: {e}"
        result["success"] = False
        if db_update_hook and callable(db_update_hook) and book_id is not None:
            try:
                db_update_hook(book_id, raw_text="", word_count=0, char_count=0, status="extraction_failed", extraction_time=round(time.perf_counter()-start, 3), extra={"error": str(e)})
            except Exception:
                pass

    return result
