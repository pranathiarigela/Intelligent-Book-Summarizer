from utils.database_sqlalchemy import SessionLocal
from utils import crud
db = SessionLocal()
u = crud.create_user(db, "testuser", "test@example.com", "hashedpwd")
b = crud.create_book(db, u.id, "Title", "Author", "file.pdf", "pdf")
s = crud.create_summary(db, b.id, u.id, "short summary", 2, "test-model", 0.12, [])
print(u.id, b.id, s.id)
db.close()
