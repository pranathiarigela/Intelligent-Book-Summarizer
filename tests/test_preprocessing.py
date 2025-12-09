from backend.preprocessing import preprocess_for_summarization
import json

sample_text = """
Dr. Kumar arrived at 3.5 p.m. He said: "This is a test."
The price is 3.14. This is another sentence.

New paragraph here. Mr. John left at 5.00 p.m.
"""

result = preprocess_for_summarization(
    text=sample_text,
    chunk_size=25,     # small size so you can clearly see chunks
    overlap=5,
    stopword_removal=False
)

print(json.dumps(result, indent=2, ensure_ascii=False))
