import re
from collections import Counter


class SummaryPostProcessor:
    def __init__(self, min_words=40, max_words=120):
        self.min_words = min_words
        self.max_words = max_words

    # -------------------------
    # Core Utilities
    # -------------------------
    def _normalize(self, text):
        return re.sub(r"\s+", " ", text.strip().lower())

    def _sentence_split(self, text):
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    # -------------------------
    # Duplicate Removal
    # -------------------------
    def remove_duplicates(self, sentences):
        seen = set()
        unique = []

        for s in sentences:
            norm = self._normalize(s)
            if norm not in seen:
                seen.add(norm)
                unique.append(s)

        return unique

    # -------------------------
    # Sentence Reordering
    # -------------------------
    def reorder_sentences(self, sentences, original_text):
        ordered = []
        for s in sentences:
            idx = original_text.find(s)
            ordered.append((idx if idx != -1 else float("inf"), s))

        ordered.sort(key=lambda x: x[0])
        return [s for _, s in ordered]

    # -------------------------
    # Length Enforcement
    # -------------------------
    def enforce_length(self, sentences):
        words = []
        final = []

        for s in sentences:
            s_words = s.split()
            if len(words) + len(s_words) <= self.max_words:
                final.append(s)
                words.extend(s_words)
            else:
                break

        return final

    # -------------------------
    # Formatting Cleanup
    # -------------------------
    def format_summary(self, sentences):
        formatted = []

        for s in sentences:
            s = s.strip()
            if not s.endswith((".", "!", "?")):
                s += "."
            s = s[0].upper() + s[1:]
            formatted.append(s)

        return " ".join(formatted)

    # -------------------------
    # Keyword Extraction (Optional)
    # -------------------------
    def extract_keywords(self, text, top_k=5):
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq = Counter(words)

        common = {
            "that", "this", "with", "from", "were", "they",
            "have", "their", "there", "about"
        }

        keywords = [
            w for w, _ in freq.most_common()
            if w not in common
        ]

        return keywords[:top_k]

    # -------------------------
    # Full Pipeline
    # -------------------------
    def refine(self, summary_text, original_text):
        sentences = self._sentence_split(summary_text)

        sentences = self.remove_duplicates(sentences)
        sentences = self.reorder_sentences(sentences, original_text)
        sentences = self.enforce_length(sentences)

        final_summary = self.format_summary(sentences)
        keywords = self.extract_keywords(final_summary)

        return {
            "summary": final_summary,
            "keywords": keywords,
            "word_count": len(final_summary.split())
        }
