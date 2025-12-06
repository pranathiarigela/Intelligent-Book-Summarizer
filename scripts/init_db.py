# scripts/init_db.py
import os
from utils.database import init_db

DB_PATH = os.getenv("SUMMARIZER_DB", "data/summarizer.db")

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db(DB_PATH)
    print(f"Initialized DB at {DB_PATH}")

if __name__ == "__main__":
    main()
