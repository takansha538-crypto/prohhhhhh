"""Test: disable sqlite3 prepared statement caching."""
import os, sqlite3

def test_cached(cached_statements):
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", f"_cache{cached_statements}.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path, cached_statements=cached_statements)
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT)")
    con.execute("BEGIN")
    try:
        for i in range(1, 5):
            email = f"u{i}@test.com"
            con.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, f"u{i}"))
            idv = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"  insert {email} -> id={idv}")
        con.commit()
        print(f"  cached_statements={cached_statements} OK:", con.execute("SELECT * FROM users").fetchall())
    except Exception as e:
        print(f"  cached_statements={cached_statements} FAIL:", e)

print("=== cached_statements=0 ===")
test_cached(0)
print("\n=== cached_statements=1 ===")
test_cached(1)
print("\n=== cached_statements=100 (default) ===")
test_cached(100)
