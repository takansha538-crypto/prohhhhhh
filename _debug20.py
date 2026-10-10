"""Most explicit: step by step with DB state check between each step."""
import os, sqlite3, sys
print(f"Python {sys.version}")
print(f"sqlite3 module sqlite_version: {sqlite3.sqlite_version}")
print(f"sqlite3 paramstyle: {sqlite3.paramstyle}")

dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_step.db")
if os.path.exists(dbp):
    os.remove(dbp)

SCHEMA = """
CREATE TABLE users_c (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    avatar TEXT,
    location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_demo BOOLEAN DEFAULT 0
);
"""

def mkdb():
    c = sqlite3.connect(dbp)
    c.executescript(SCHEMA)
    c.commit()
    c.close()
    print("\nDB created at", dbp)

def check(step):
    c = sqlite3.connect(dbp)
    rows = c.execute("SELECT id, email, name FROM users_c ORDER BY id").fetchall()
    print(f"[{step}] DB contents: {rows}")
    c.close()
    return rows

mkdb()
check("after mkdb, empty")

# INSERT 1
c = sqlite3.connect(dbp)
params = dict(email="[email protected]", ph="AAAAAAAA", name="User-One", role="creator", av="/a.svg", loc="NYC", dm=0)
sql = "INSERT INTO users_c (email, password_hash, name, role, avatar, location, is_demo) VALUES (:email, :ph, :name, :role, :av, :loc, :dm)"
print(f"\n[INSERT 1] about to execute with params email={params['email']}, name={params['name']}")
c.execute(sql, params)
c.commit()
c.close()
check("after insert 1 (u1)")

# INSERT 2
c = sqlite3.connect(dbp)
params2 = dict(email="[email protected]", ph="BBBBBBBB", name="User-Two", role="creator", av="/b.svg", loc="SFO", dm=0)
print(f"\n[INSERT 2] about to execute with params email={params2['email']}, name={params2['name']}")
try:
    c.execute(sql, params2)
    c.commit()
    c.close()
    check("after insert 2 (u2)")
except Exception as e:
    print(f"[INSERT 2 FAILED] {type(e).__name__}: {e}")
    c.rollback()
    c.close()
    check("after failed insert 2")

# INSERT 3 (totally different email, just to verify even third fails after fail)
print(f"\n[INSERT 3] fresh connection, fresh email u3")
c = sqlite3.connect(dbp)
try:
    c.execute(sql, dict(email="[email protected]", ph="CCCC", name="User-Three", role="creator", av="/c.svg", loc="CHI", dm=0))
    c.commit()
    c.close()
    check("after insert 3")
except Exception as e:
    print(f"[INSERT 3 FAILED] {e}")
    c.rollback()
    c.close()
    check("after fail 3")
