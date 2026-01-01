import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")
    nltk.download("punkt_tab")

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer


class Summarizer:
    def __init__(self):
        self.summarizer = TextRankSummarizer()

    def summarize(self, text: str, sentences: int = 4) -> str:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        ranked = self.summarizer(parser.document, sentences * 2)

        cleaned = []

        for s in ranked:
            s = str(s).strip()
            s_lower = s.lower()

            # Remove dialogue / speech
            if '"' in s or any(w in s_lower for w in ["said", "asked", "replied", "shouted"]):
                continue

            # Remove very short or weak sentences
            if len(s.split()) < 10:
                continue

            cleaned.append(s)

        # Keep best narrative sentences
        final = cleaned[:sentences]

        return " ".join(final)

summarizer = Summarizer()
