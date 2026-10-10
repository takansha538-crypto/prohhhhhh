"""Isolate trigger: raw sqlite3 with full schema + CURRENT_TIMESTAMP."""
import os, sqlite3

dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_rawfull.db")
if os.path.exists(dbp):
    os.remove(dbp)

# EXACT same schema as ORM User
SCHEMA = """
CREATE TABLE users_c (
    id INTEGER NOT NULL,
    email VARCHAR(180) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL,
    avatar VARCHAR(255),
    location VARCHAR(120),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_demo BOOLEAN,
    PRIMARY KEY (id),
    UNIQUE (email)
);
"""

# A) Test raw with per-insert commit
con = sqlite3.connect(dbp, cached_statements=0)
con.executescript(SCHEMA)

try:
    rows = [
        ("[email protected]", "hashAAAA", "U One", "creator", "/a.svg", "Loc", 0),
        ("[email protected]", "hashBBBB", "U Two", "creator", "/b.svg", "Loc", 0),
        ("[email protected]", "hashCCCC", "U Three", "creator", "/c.svg", "Loc", 0),
    ]
    for email, phash, name, role, av, loc, demo in rows:
        con.execute("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)",
                    (email, phash, name, role, av, loc, demo))
        lastid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"  insert {email} -> id={lastid}")
        con.commit()
        print(f"  committed")
    print("A) PER-COMMIT raw full schema OK: count=", con.execute("SELECT COUNT(*) FROM users_c").fetchone()[0])
except Exception as e:
    print("A) PER-COMMIT FAIL:", e)
    con.rollback()
finally:
    con.close()

# B) Test raw WITH executemany (no loop)
dbp2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_rawmany.db")
if os.path.exists(dbp2):
    os.remove(dbp2)
con2 = sqlite3.connect(dbp2, cached_statements=0)
con2.executescript(SCHEMA)
try:
    rows = [
        ("[email protected]", "h1", "U1", "c", "a", "l", 0),
        ("[email protected]", "h2", "U2", "c", "a", "l", 0),
        ("[email protected]", "h3", "U3", "c", "a", "l", 0),
        ("[email protected]", "h4", "U4", "c", "a", "l", 0),
    ]
    con2.executemany("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)", rows)
    con2.commit()
    print("B) EXECUTEMANY OK: rows=", con2.execute("SELECT * FROM users_c").fetchall())
except Exception as e:
    print("B) EXECUTEMANY FAIL:", e)
    con2.rollback()
finally:
    con2.close()

# C) Test: executemany with NO intermediate selects (no last_insert_rowid call)
dbp3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_rawnoselect.db")
if os.path.exists(dbp3):
    os.remove(dbp3)
con3 = sqlite3.connect(dbp3, cached_statements=0)
con3.executescript(SCHEMA)
try:
    con3.execute("BEGIN")
    con3.execute("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)", ("[email protected]","h1","A","c","a","l",0))
    con3.execute("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)", ("[email protected]","h2","B","c","a","l",0))
    con3.execute("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)", ("[email protected]","h3","C","c","a","l",0))
    con3.commit()
    print("C) LOOP-NO-SELECT OK:", con3.execute("SELECT id,email FROM users_c").fetchall())
except Exception as e:
    print("C) LOOP-NO-SELECT FAIL:", e)
    con3.rollback()
finally:
    con3.close()
