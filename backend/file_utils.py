import pdfplumber
from PyPDF2 import PdfReader
from docx import Document


MAX_TEXT_LENGTH = 200_000  # safety limit


def extract_text_from_txt(file):
    return file.read().decode("utf-8", errors="ignore")


def extract_text_from_pdf(file):
    text = []

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception:
        file.seek(0)
        reader = PdfReader(file)
        for page in reader.pages:
            text.append(page.extract_text() or "")

    return "\n\n".join(text)


def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])


def validate_extracted_text(text):
    if not text or len(text.strip()) == 0:
        raise ValueError("No readable text found")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError("Extracted text too large")

    return text.strip()
