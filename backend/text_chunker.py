"""
Text Chunking Module
--------------------
Handles intelligent chunking of long texts with:
- Token-aware chunk sizes
- Overlapping boundaries
- Natural breakpoints (paragraphs)
- Chunk order tracking
"""

from typing import List, Dict


def chunk_text(
    text: str,
    max_tokens: int = 1000,
    overlap_tokens: int = 150
) -> List[Dict]:
    """
    Splits long text into overlapping chunks with natural boundaries.

    Args:
        text (str): Cleaned input text
        max_tokens (int): Max tokens per chunk (safe < model limit)
        overlap_tokens (int): Overlap size to preserve context

    Returns:
        List[Dict]: Ordered chunks with metadata
    """

    words = text.split()
    total_words = len(words)

    chunks = []
    start = 0
    chunk_index = 0

    while start < total_words:
        # Initial end index
        end = min(start + max_tokens, total_words)

        # Attempt natural break (paragraph boundary)
        candidate_text = " ".join(words[start:end])
        last_para_break = candidate_text.rfind("\n\n")

        # If paragraph break is reasonably deep in the chunk, cut there
        if last_para_break != -1 and last_para_break > len(candidate_text) * 0.6:
            candidate_text = candidate_text[:last_para_break]
            end = start + len(candidate_text.split())

        chunk_words = words[start:end]

        chunks.append({
            "chunk_index": chunk_index,
            "start_word": start,
            "end_word": end,
            "text": " ".join(chunk_words)
        })

        chunk_index += 1

        # Move start forward with overlap
        start = end - overlap_tokens
        if start < 0:
            start = 0

    return chunks
