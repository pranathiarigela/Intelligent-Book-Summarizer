# tests/manual_test_auth.py
from backend import auth

DB = "data/summarizer.db"

def setup():
    # create fresh DB for this run
    import os
    if os.path.exists(DB):
        os.remove(DB)
    auth.init_user_table(DB)
    print("DB initialized:", DB)

def run():
    # 1) Register user
    res = auth.register_user(name="Ammu Tester", email="ammu@example.com",
                             password="StrongP@ssw0rd!", db_path=DB)
    print("Register:", res)

    # 2) Attempt duplicate registration
    res2 = auth.register_user(name="Ammu Tester", email="ammu@example.com",
                              password="StrongP@ssw0rd!", db_path=DB)
    print("Duplicate Register:", res2)

    # 3) Login with correct password
    res3 = auth.login_user(email="ammu@example.com", password="StrongP@ssw0rd!", db_path=DB)
    print("Login (correct):", res3)

    # 4) Login with wrong password
    res4 = auth.login_user(email="ammu@example.com", password="wrongpass", db_path=DB)
    print("Login (wrong):", res4)

    # 5) Inspect DB rows (quick)
    import sqlite3
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, created_at FROM users")
    rows = cur.fetchall()
    print("Users in DB:", rows)
    conn.close()

if __name__ == "__main__":
    setup()
    run()
