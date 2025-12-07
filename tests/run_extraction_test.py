# backend/run_extraction_test.py
import os
from backend.text_extractor import extract_text
from utils.db_hooks import update_book_text

# Path to a sample file you created
sample_path = "tests/samples/sample_utf8.txt"
book_id = "test-book-1234"

res = extract_text(sample_path, book_id=book_id, db_update_hook=update_book_text)

print("Success:", res["success"])
print("Error:", res.get("error"))
print("Word Count:", res["stats"]["word_count"])
print("Meta:", res["meta"])
