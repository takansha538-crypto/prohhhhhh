"""Test raw sqlite3 and SQLAlchemy core to isolate."""
import os, sqlite3
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_raw.db")
if os.path.exists(db_path):
    os.remove(db_path)

# ---- Part 1: raw sqlite3 ----
print("=== RAW SQLITE3 ===")
con = sqlite3.connect(db_path)
con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT)")
# Begin explicit transaction
con.execute("BEGIN")
con.execute("INSERT INTO users (email, name) VALUES (?, ?) RETURNING id", ("[email protected]", "u1"))
row = con.execute("SELECT last_insert_rowid()").fetchone()
print(f"After u1 insert, rowid={row}, selecting:")
for r in con.execute("SELECT * FROM users"):
    print(" ", r)
# Now insert u2
try:
    con.execute("INSERT INTO users (email, name) VALUES (?, ?) RETURNING id", ("[email protected]", "u2"))
    print("u2 inserted OK")
    for r in con.execute("SELECT * FROM users"):
        print(" ", r)
    con.commit()
    print("RAW OK. Count:", con.execute("SELECT COUNT(*) FROM users").fetchone())
except Exception as e:
    print("RAW FAIL:", e)

# ---- Part 2: SQLAlchemy core ----
print("\n=== SQLALCHEMY CORE ===")
db_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_core.db")
if os.path.exists(db_path2):
    os.remove(db_path2)
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
eng = create_engine(f"sqlite:///{db_path2}")
with eng.connect() as conn:
    conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT)"))
    conn.commit()
    # begin
    with conn.begin():
        r1 = conn.execute(text("INSERT INTO users (email, name) VALUES (:email, :name) RETURNING id"), {"email":"[email protected]", "name":"U1"})
        print("u1 inserted, id:", list(r1))
        r2 = conn.execute(text("INSERT INTO users (email, name) VALUES (:email, :name) RETURNING id"), {"email":"[email protected]", "name":"U2"})
        print("u2 inserted, id:", list(r2))
    print("CORE OK.")
