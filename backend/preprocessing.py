"""
backend/preprocessing.py

Text preprocessing pipeline for Intelligent Book Summarizer.

Features:
- clean_text: normalize whitespace and line breaks, remove control chars, keep punctuation
- segment_sentences: spaCy (preferred) or NLTK fallback; handles abbreviations and decimals
- detect_language: langdetect-based language detection
- calculate_text_stats: words, chars, sentences, avg sentence length, reading time
- chunk_text: chunk by ~N words, overlap (words), preserve sentence boundaries, record metadata
- remove_stopwords: optional, configurable stopword removal (NLTK)
- preprocess_for_summarization: pipeline orchestrator with validation and warnings

Author: Generated for your project
"""

from typing import List, Dict, Any, Optional
import re
import math
import logging

# Third-party libs (declare in requirements): nltk, spacy (optional), langdetect
try:
    import spacy
    _SPACY_AVAILABLE = True
except Exception:
    spacy = None
    _SPACY_AVAILABLE = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0  # reproducible results
    _LANGDETECT_AVAILABLE = True
except Exception:
    detect = None
    _LANGDETECT_AVAILABLE = False

# NLTK fallback
try:
    import nltk
    _NLTK_AVAILABLE = True
    # Try to ensure required resources exist. These calls are safe — they will no-op if present.
    try:
        nltk.data.find("tokenizers/punkt")
    except Exception:
        nltk.download("punkt", quiet=True)
    try:
        nltk.data.find("corpora/stopwords")
    except Exception:
        nltk.download("stopwords", quiet=True)
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords as _nltk_stopwords
except Exception:
    nltk = None
    sent_tokenize = None
    word_tokenize = None
    _nltk_stopwords = set()
    _NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


##############
# Cleaning
##############
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]+")
MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
MULTI_NEWLINE_RE = re.compile(r"\n{2,}")
WEIRD_SPACES_RE = re.compile(r"\u00A0")  # non-breaking space

def clean_text(text: str) -> str:
    """
    Improved cleaning that avoids breaking decimals and initials:
    - Normalize line endings
    - Remove control chars except newline and tab
    - Collapse multiple spaces/tabs
    - Keep paragraph breaks (max two newlines)
    - Ensure there's a space after sentence-ending punctuation only when the next
      character is an uppercase letter or a quote/bracket (likely a real sentence boundary).
    """
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            logger.exception("Failed converting text to str")
            return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]+", "", text)

    # Normalize NBSP
    text = WEIRD_SPACES_RE.sub(" ", text)

    # Collapse multiple spaces and tabs to single space (but not newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Collapse excessive newlines to max two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Only insert a space after punctuation if next char is an uppercase letter or a quote/bracket
    # This avoids adding spaces inside decimals (3.14) or initials (p.m.)
    text = re.sub(r'([.!?]["\']?)(?=[A-Z\"\'\(\[]|\n)', r"\1 ", text)

    text = text.strip()
    return text


##############
# Sentence segmentation
##############


def _spacy_segment(text: str, model_name: str = "en_core_web_sm") -> List[str]:
    """
    Use spaCy for sentence segmentation. If the pipeline lacks a sentencizer,
    add one (non-destructive). If the model cannot be loaded, raise.
    """
    try:
        nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "textcat"])
    except Exception:
        # If model not installed, use blank English pipeline
        try:
            nlp = spacy.blank("en")
        except Exception:
            logger.exception("spaCy blank model could not be created")
            raise

    # If pipeline does not produce .sents, add a sentencizer component
    if not any(pipe[0] in ("senter", "sentencizer") or pipe[0].startswith("senter") for pipe in nlp.pipeline):
        try:
            # spaCy v3+: use 'sentencizer' name
            nlp.add_pipe("sentencizer")
        except Exception:
            # older spaCy name fallback
            try:
                nlp.add_pipe(nlp.create_pipe("sentencizer"))
            except Exception:
                logger.warning("Unable to add sentencizer to spaCy pipeline; sentence boundaries may be unset")

    doc = nlp(text)
    # now doc.sents should be available
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences

def _nltk_segment(text: str) -> List[str]:
    """
    Use NLTK punkt sentence tokenizer as fallback.
    """
    if not _NLTK_AVAILABLE:
        raise RuntimeError("NLTK is not available for sentence segmentation.")
    # sent_tokenize from NLTK handles common abbreviations and decimals fairly well
    sentences = sent_tokenize(text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def segment_sentences(text: str, prefer_spacy: bool = True) -> List[str]:
    """
    Segment text into sentences. Prefer spaCy when available and configured,
    otherwise use NLTK. If both fail, use a robust regex fallback that attempts
    to avoid splitting on common decimal patterns and abbreviations.
    """
    if not text:
        return []

    # Try spaCy first if available and preferred
    if prefer_spacy and _SPACY_AVAILABLE:
        try:
            sents = _spacy_segment(text)
            if sents:
                return sents
        except Exception:
            logger.exception("spaCy segmentation failed, falling back to NLTK/regex")

    # Try NLTK if available
    if _NLTK_AVAILABLE:
        try:
            sents = _nltk_segment(text)
            if sents:
                return sents
        except Exception:
            logger.exception("NLTK segmentation failed")

    # Robust regex fallback:
    # - avoid splitting on numbers like 3.14 or 5.00
    # - avoid splitting after common abbreviations (Dr., Mr., Mrs., etc.)
    abbreviations = r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e|St|Co|Ltd)\."
    decimal_pattern = r"(?<=\d)\.(?=\d)"
    # Temporarily protect decimals and abbreviations
    protected = text
    # replace decimal dots with placeholder
    protected = re.sub(decimal_pattern, "<DOT_DECIMAL>", protected)
    protected = re.sub(abbreviations, lambda m: m.group(0).replace(".", "<DOT_ABBR>"), protected, flags=re.IGNORECASE)

    # split on punctuation followed by space+capital (common sentence boundary)
    parts = re.split(r'(?<=[\.\?\!]["\')\]]?)\s+(?=[A-Z0-9\"\'\(\[])', protected)
    # restore placeholders
    parts = [p.replace("<DOT_DECIMAL>", ".").replace("<DOT_ABBR>", ".") for p in parts]
    parts = [p.strip() for p in parts if p.strip()]
    return parts

##############
# Language detection
##############


def detect_language(text: str) -> Optional[str]:
    """
    Return ISO language code like 'en', 'fr', 'es'. If langdetect not available or fails, return None.
    """
    if not text or not _LANGDETECT_AVAILABLE:
        return None
    try:
        lang = detect(text)
        return lang
    except Exception:
        logger.exception("Language detection failed")
        return None


##############
# Stats
##############


def calculate_text_stats(text: str) -> Dict[str, Any]:
    """
    Compute basic stats:
     - word_count
     - char_count
     - sentence_count
     - avg_sentence_length (words)
     - est_reading_time_minutes (WPM default 200)
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "word_count": 0,
            "char_count": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0.0,
            "reading_time_minutes": 0.0,
        }

    # Use simple tokenization for counts
    words = re.findall(r"\S+", cleaned)
    word_count = len(words)
    char_count = len(cleaned)
    sentences = segment_sentences(cleaned)
    sentence_count = len(sentences)
    avg_sentence_length = (word_count / sentence_count) if sentence_count > 0 else float(word_count)
    reading_time_minutes = round(word_count / 200.0, 2)  # 200 WPM default

    return {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "reading_time_minutes": reading_time_minutes,
    }


##############
# Stopword handling (optional)
##############


def remove_stopwords_from_tokens(tokens: List[str], language: str = "en") -> List[str]:
    """
    Remove stopwords from a list of tokens. NLTK stopwords used if available.
    """
    if not _NLTK_AVAILABLE:
        return tokens

    try:
        sw = set(_nltk_stopwords.words(language))
    except Exception:
        sw = set()
    return [t for t in tokens if t.lower() not in sw]


def remove_stopwords(text: str, language: str = "en") -> str:
    """
    Remove stopwords from a text, preserving original spacing roughly.
    """
    if not text or not _NLTK_AVAILABLE:
        return text
    tokens = word_tokenize(text)
    filtered = remove_stopwords_from_tokens(tokens, language=language)
    # Rejoin with single spaces (will lose some original punctuation spacing; acceptable for optional preprocessing)
    return " ".join(filtered)


##############
# Chunking
##############


def _words_in_sentence(sentence: str) -> int:
    return len(re.findall(r"\S+", sentence))


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
    min_chunk_size: int = 200,
) -> List[Dict[str, Any]]:
    """
    Sentence-index based chunking.

    - Build chunks as contiguous sentence ranges.
    - chunk_size and overlap are measured in words.
    - Overlap is achieved by moving the next chunk's start index backward
      so the last `overlap` words of previous chunk appear at the start of
      the next chunk (by sentence granularity).
    """
    if not text:
        return []

    sentences = segment_sentences(text)
    if not sentences:
        return []

    # Precompute sentence word counts and start char offsets
    sent_word_counts = [_words_in_sentence(s) for s in sentences]
    cleaned = clean_text(text)
    sent_char_starts = []
    search_pos = 0
    for s in sentences:
        idx = cleaned.find(s, search_pos)
        if idx >= 0:
            sent_char_starts.append(idx)
            search_pos = idx + len(s)
        else:
            # fallback approximate
            sent_char_starts.append(search_pos)
            search_pos += len(s)

    n = len(sentences)
    chunks = []

    start_idx = 0
    chunk_id = 0
    while start_idx < n:
        # accumulate sentences until we reach or exceed chunk_size
        acc_words = 0
        end_idx = start_idx
        while end_idx < n and acc_words < chunk_size:
            acc_words += sent_word_counts[end_idx]
            end_idx += 1
        end_idx -= 1  # last included sentence index

        # if no progress (single sentence too large), force include at least one sentence
        if end_idx < start_idx:
            end_idx = start_idx
            acc_words = sent_word_counts[start_idx]

        # construct chunk text and metadata
        chunk_sentences = sentences[start_idx : end_idx + 1]
        chunk_text_str = " ".join(chunk_sentences).strip()
        start_char = sent_char_starts[start_idx] if start_idx < len(sent_char_starts) else None
        end_char = (
            sent_char_starts[end_idx] + len(sentences[end_idx])
            if end_idx < len(sent_char_starts)
            else None
        )

        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": chunk_text_str,
                "word_count": acc_words,
                "start_char": start_char,
                "end_char": end_char,
                "start_sentence_idx": start_idx,
                "end_sentence_idx": end_idx,
            }
        )
        chunk_id += 1

        # If we've reached the end, break
        if end_idx == n - 1:
            break

        # Compute overlap: find the earliest sentence index within [start_idx..end_idx]
        # such that sum of words from that index..end_idx >= overlap.
        if overlap <= 0:
            next_start = end_idx + 1
        else:
            back_sum = 0
            overlap_start = end_idx
            while overlap_start >= start_idx and back_sum < overlap:
                back_sum += sent_word_counts[overlap_start]
                overlap_start -= 1
            # overlap_start was decremented one extra in loop
            overlap_start += 1

            # If overlap would cause no forward progress, step forward by one sentence
            if overlap_start <= start_idx:
                # If the chunk is the entire remaining text, exit
                if end_idx == n - 1:
                    break
                # else, move to the sentence after start_idx to ensure progress
                next_start = min(start_idx + 1, n - 1)
            else:
                next_start = overlap_start

        # Safety guard: ensure we progress
        if next_start <= start_idx:
            next_start = end_idx + 1

        start_idx = next_start

    # Merge very small final chunk into previous if needed
    if len(chunks) >= 2 and chunks[-1]["word_count"] < min_chunk_size:
        last = chunks.pop()
        prev = chunks.pop()
        merged_text = f"{prev['text']} {last['text']}"
        merged_chunk = {
            "chunk_id": prev["chunk_id"],
            "text": merged_text,
            "word_count": prev["word_count"] + last["word_count"],
            "start_char": prev["start_char"],
            "end_char": last["end_char"],
            "start_sentence_idx": prev["start_sentence_idx"],
            "end_sentence_idx": last["end_sentence_idx"],
        }
        chunks.append(merged_chunk)

    # Reassign chunk ids sequentially
    for i, c in enumerate(chunks):
        c["chunk_id"] = i

    return chunks



##############
# Orchestrator
##############


class PreprocessingError(Exception):
    pass


def preprocess_for_summarization(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
    stopword_removal: bool = False,
    allowed_languages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for preprocessing.

    Steps:
      1. Clean text
      2. Detect language
      3. Segment sentences
      4. Calculate stats
      5. Chunk text
      6. Optionally remove stopwords from chunk texts (if configured)

    Returns a dict containing:
      - cleaned_text
      - language
      - sentences
      - stats
      - chunks: list of chunk dicts (with metadata)
      - warnings: list of warnings (e.g., non-english)
    """
    warnings = []
    if not text or not str(text).strip():
        raise PreprocessingError("Input text is empty or only whitespace.")

    cleaned_text = clean_text(text)

    # Basic validation and edge-case warnings
    stats = calculate_text_stats(cleaned_text)
    wc = stats.get("word_count", 0)
    if wc < 100:
        warnings.append("Text is very short (<100 words). Summaries may be trivial.")
    if wc > 100_000:
        warnings.append("Text is very long (>100,000 words). Consider splitting or shorter chunk_size.")

    # Language detection
    language = detect_language(cleaned_text)
    if allowed_languages and language and language not in allowed_languages:
        warnings.append(f"Detected language '{language}' is not in allowed languages {allowed_languages}.")

    if language and language != "en":
        warnings.append(f"Detected language '{language}'. If your summarization model only supports English, results may be poor.")

    # Sentence segmentation
    try:
        sentences = segment_sentences(cleaned_text)
    except Exception as e:
        logger.exception("Sentence segmentation failed")
        sentences = []
        warnings.append("Sentence segmentation failed; proceeding with fallback chunking.")

    # Chunking
    try:
        chunks = chunk_text(cleaned_text, chunk_size=chunk_size, overlap=overlap)
    except Exception:
        logger.exception("Chunking failed")
        raise PreprocessingError("Chunking failed due to unexpected error")

    # Optional stopword handling (apply per chunk, not overall)
    if stopword_removal:
        lang_for_stop = language if language else "english"
        # NLTK stopwords use 'english' name; adjust common cases
        if lang_for_stop == "en":
            lang_for_stop = "english"
        if _NLTK_AVAILABLE:
            for c in chunks:
                # remove stopwords from chunk text (non-destructive metadata preserved)
                c["text_no_stopwords"] = remove_stopwords(c["text"], language=lang_for_stop)
        else:
            warnings.append("Stopword removal requested but NLTK not available; skipping stopword removal.")

    return {
        "cleaned_text": cleaned_text,
        "language": language,
        "sentences": sentences,
        "stats": stats,
        "chunks": chunks,
        "warnings": warnings,
    }


##############
# Small usage example (for tests or quick manual run)
##############
if __name__ == "__main__":  # pragma: no cover
    sample = (
        "Dr. Kumar arrived at 3.5 p.m. He said: \"This is a test.\" "
        "The price is 3.14. This is another sentence.\n\nNew paragraph here."
    )
    out = preprocess_for_summarization(sample, chunk_size=20, overlap=5, stopword_removal=False)
    import json
    print(json.dumps(out, indent=2, ensure_ascii=False))
