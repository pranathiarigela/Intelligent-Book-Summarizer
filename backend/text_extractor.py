# backend/text_extractor.py
"""
Text extraction utilities for TXT, PDF, DOCX.
Provides OCR fallback for scanned PDFs (uses pytesseract + pdf2image if available).

Public functions:
- extract_text_from_path(path) -> str
- extract_text_from_path_meta(path, ocr=True) -> dict with keys:
    - text (str), pages (int), scanned (bool), ocr_performed (bool)
"""

import os
import io
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("text_extractor")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)

# Try optional dependencies
HAS_PDFPLUMBER = False
HAS_PYPDF2 = False
HAS_PYTESSERACT = False
HAS_PDF2IMAGE = False
HAS_DOCX = False
try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except Exception:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2

    HAS_PYPDF2 = True
except Exception:
    HAS_PYPDF2 = False

try:
    import pytesseract

    HAS_PYTESSERACT = True
except Exception:
    HAS_PYTESSERACT = False

try:
    from pdf2image import convert_from_path, convert_from_bytes

    HAS_PDF2IMAGE = True
except Exception:
    HAS_PDF2IMAGE = False

try:
    import docx  # python-docx

    HAS_DOCX = True
except Exception:
    HAS_DOCX = False


# -------------------------
# Helpers
# -------------------------
def _read_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        # fallback to latin1
        try:
            with open(path, "r", encoding="latin1") as f:
                return f.read()
        except Exception:
            return ""


def _extract_docx(path: str) -> str:
    if not HAS_DOCX:
        return ""
    try:
        doc = docx.Document(path)
        paras = [p.text for p in doc.paragraphs if p.text]
        return "\n\n".join(paras)
    except Exception as e:
        logger.exception("DOCX extraction failed")
        return ""


def _pdf_with_pdfplumber(path: str) -> Tuple[str, int]:
    text_chunks = []
    pages = 0
    try:
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            for p in pdf.pages:
                try:
                    txt = p.extract_text() or ""
                except Exception:
                    txt = ""
                text_chunks.append(txt)
    except Exception:
        logger.exception("pdfplumber failed")
        return "", 0
    return "\n".join(text_chunks), pages


def _pdf_with_pypdf2(path: str) -> Tuple[str, int]:
    text_chunks = []
    pages = 0
    try:
        with open(path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            pages = len(reader.pages)
            for p in reader.pages:
                try:
                    txt = p.extract_text() or ""
                except Exception:
                    txt = ""
                text_chunks.append(txt)
    except Exception:
        logger.exception("PyPDF2 failed")
        return "", 0
    return "\n".join(text_chunks), pages


def _needs_ocr(text: str, pages: int) -> bool:
    """
    Heuristic: if overall text is very short relative to number of pages,
    or virtually empty, consider OCR.
    """
    if not text:
        return True
    chars = len(text.strip())
    if pages <= 0:
        # unknown pages — decide based on chars
        return chars < 200
    avg = chars / max(1, pages)
    # if less than ~50 chars per page, likely scanned
    return avg < 60


def _ocr_pdf(path: str, use_poppler_path: str = None) -> Tuple[str, int]:
    """
    OCR entire PDF using pdf2image -> pytesseract.
    Returns (text, pages). Requires HAS_PDF2IMAGE and HAS_PYTESSERACT.
    """
    if not (HAS_PDF2IMAGE and HAS_PYTESSERACT):
        raise RuntimeError("OCR dependencies not available (pdf2image + pytesseract required).")

    images = None
    text_chunks = []
    pages = 0
    # prefer convert_from_path when possible
    try:
        # If convert_from_path fails because poppler not installed, convert_from_bytes may work if passed bytes
        images = convert_from_path(path, dpi=300)
    except Exception:
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            images = convert_from_bytes(data, dpi=300)
        except Exception:
            logger.exception("pdf2image conversion failed for OCR")
            raise

    pages = len(images)
    for im in images:
        try:
            txt = pytesseract.image_to_string(im)
        except Exception:
            txt = ""
        text_chunks.append(txt)
    return "\n".join(text_chunks), pages


# -------------------------
# Public API
# -------------------------
def extract_text_from_path_meta(path: str, ocr: bool = True) -> Dict[str, Any]:
    """
    Extract text from a file and return metadata.

    Returns:
      {"text": str, "pages": int, "scanned": bool, "ocr_performed": bool}
    - scanned: True if detection heuristics think it's a scanned PDF
    - ocr_performed: True if OCR was actually executed
    """
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    text = ""
    pages = 0
    ocr_performed = False
    scanned = False

    try:
        if ext == ".txt":
            text = _read_txt(path)
            pages = max(1, text.count("\n") // 50 + 1)
            scanned = False
            return {"text": text, "pages": pages, "scanned": False, "ocr_performed": False}

        if ext in (".docx",):
            text = _extract_docx(path)
            pages = max(1, text.count("\n") // 50 + 1)
            scanned = False
            return {"text": text, "pages": pages, "scanned": False, "ocr_performed": False}

        if ext == ".pdf":
            # Try pdfplumber first, then PyPDF2
            if HAS_PDFPLUMBER:
                text, pages = _pdf_with_pdfplumber(path)
            elif HAS_PYPDF2:
                text, pages = _pdf_with_pypdf2(path)
            else:
                # no pdf text libs available — consider as scanned
                text = ""
                pages = 0

            # decide if OCR needed
            need_ocr = _needs_ocr(text, pages)
            if need_ocr:
                scanned = True
            # If OCR desired and available, perform
            if ocr and need_ocr:
                try:
                    if not (HAS_PDF2IMAGE and HAS_PYTESSERACT):
                        # OCR tools missing; return scanned flag so caller can decide
                        return {"text": text, "pages": pages, "scanned": True, "ocr_performed": False}
                    ocr_text, ocr_pages = _ocr_pdf(path)
                    ocr_performed = True
                    # prefer OCR text if it has significant content
                    if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        pages = ocr_pages
                        scanned = False
                    else:
                        # keep original text but mark OCR performed
                        text = ocr_text or text
                        scanned = False if ocr_text.strip() else True
                    return {"text": text, "pages": pages or ocr_pages, "scanned": scanned, "ocr_performed": ocr_performed}
                except Exception:
                    logger.exception("OCR attempt failed")
                    # return metadata telling OCR failed
                    return {"text": text, "pages": pages, "scanned": scanned, "ocr_performed": False}
            return {"text": text, "pages": pages, "scanned": scanned, "ocr_performed": False}

        # unknown extension fallback
        return {"text": "", "pages": 0, "scanned": False, "ocr_performed": False}
    except Exception:
        logger.exception("Extraction failure")
        return {"text": "", "pages": 0, "scanned": False, "ocr_performed": False}


def extract_text_from_path(path: str) -> str:
    """
    Backwards compatible: returns only text string.
    Tries meta extractor with OCR allowed; if OCR needed but unavailable, returns extracted text (may be empty).
    """
    meta = extract_text_from_path_meta(path, ocr=True)
    return meta.get("text", "")
