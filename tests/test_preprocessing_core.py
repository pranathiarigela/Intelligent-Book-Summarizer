# tests/test_preprocessing_core.py
import json
from backend.preprocessing import preprocess_for_summarization, clean_text

SAMPLE = """
Dr. Kumar arrived at 3.5 p.m. He said: "This is a test."
The price is 3.14. This is another sentence.

New paragraph here. Mr. John left at 5.00 p.m.
"""

def test_preprocess_basic():
    out = preprocess_for_summarization(SAMPLE, chunk_size=1000, overlap=100, stopword_removal=False)
    # basic fields
    assert out["language"] == "en"
    assert "cleaned_text" in out and out["cleaned_text"].strip() != ""
    # sentence checks
    expected_sentences = [
        'Dr. Kumar arrived at 3.5 p.m. He said: "This is a test."',
        'The price is 3.14.',
        'This is another sentence.',
        'New paragraph here.',
        'Mr. John left at 5.00 p.m.'
    ]
    assert out["sentences"] == expected_sentences
    assert out["stats"]["sentence_count"] == len(expected_sentences)
    # chunk checks: one chunk, contiguous sentences
    chunks = out["chunks"]
    assert len(chunks) >= 1
    chunk = chunks[0]
    # reconstructed text should equal joined sentences for the chunk range
    start, end = chunk["start_sentence_idx"], chunk["end_sentence_idx"]
    reconstructed = " ".join(out["sentences"][start:end+1]).strip()
    assert reconstructed == chunk["text"].strip()
    # word count sanity
    assert chunk["word_count"] == sum(len(s.split()) for s in out["sentences"][start:end+1])

def test_clean_text_no_space_glue():
    cleaned = clean_text('Hello."World"')
    assert '." ' in cleaned or '."\\n' in cleaned  # there should be a space or newline after punctuation
