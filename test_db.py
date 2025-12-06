from utils.database import (
    connect_db,
    create_user,
    get_user_by_email,
    verify_user_password,
    create_book,
    create_summary
)

# Connect to the SQLite database
conn = connect_db("data/summarizer.db")

# Create user
try:
    uid = create_user(conn, "Ammu Example", "ammu@example.com", "S3cureP@ssw0rd", "user")
    print("User created with ID:", uid)
except Exception as e:
    print("Could not create user:", e)

# Fetch user
user = get_user_by_email(conn, "ammu@example.com")
print("Fetched user:", user)

# Password check
print("Password correct:", verify_user_password(conn, "ammu@example.com", "S3cureP@ssw0rd"))

# Create a book
book_id = create_book(conn, user_id=user["user_id"], title="AI Book")
print("Book created:", book_id)

# Create summary
summary_id = create_summary(
    conn,
    book_id,
    user["user_id"],
    "This is a sample summary.",
    "short",
    "paragraphs",
    ["chunk1 summary", "chunk2 summary"],
    2.34
)
print("Summary created:", summary_id)

conn.close()
