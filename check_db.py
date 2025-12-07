import sqlite3

conn = sqlite3.connect("data/app.db")
rows = conn.execute("SELECT id, status, word_count, char_count, extra FROM books").fetchall()
conn.close()

for r in rows:
    print(r)
