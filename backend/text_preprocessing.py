import re
from langdetect import detect, LangDetectException
from typing import List, Dict
from backend.text_chunker import chunk_text


# -------------------- CONSTANTS --------------------
DEFAULT_CHUNK_SIZE = 1200   # words
DEFAULT_OVERLAP = 150       # words


# -------------------- BASIC CLEANING --------------------
def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def remove_special_characters(text: str) -> str:
    # Keep punctuation needed for sentence structure
    return re.sub(r"[^\w\s.,;:!?()\-\n]", "", text)


def normalize_text(text: str) -> str:
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    return text

def clean_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove unwanted characters (keep punctuation)
    text = re.sub(r'[^\w\s\.\,\?\!\-\n]', '', text)

    return text.strip()

# -------------------- PDF NOISE REMOVAL --------------------
def remove_page_numbers(text: str) -> str:
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        if re.fullmatch(r"\s*\d+\s*", line):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def remove_footnotes(text: str) -> str:
    # Removes common footnote patterns like [1], (1)
    return re.sub(r"\[\d+\]|\(\d+\)", "", text)


def remove_citations(text: str) -> str:
    # Basic academic citation patterns
    text = re.sub(r"\([A-Za-z]+,\s*\d{4}\)", "", text)
    text = re.sub(r"\[[0-9,\s]+\]", "", text)
    return text


# -------------------- LANGUAGE DETECTION --------------------
def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


# -------------------- CHUNKING --------------------
def split_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[str]:
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap

    return chunks


# -------------------- FULL PIPELINE --------------------
def preprocess_text(text):
    cleaned_text = clean_text(text)
    language = detect_language(cleaned_text)

    # 🔹 Task 10: Chunking with context preservation
    chunks = chunk_text(
        cleaned_text,
        max_tokens=600,
        overlap_tokens=80
    )

    return {
        "cleaned_text": cleaned_text,
        "language": language,
        "chunks": chunks
    }
