"""Workaround: keyword params bypass positional parameter memory corruption in Python 3.14 pysqlite."""
import os, sqlite3

dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_kw.db")
if os.path.exists(dbp):
    os.remove(dbp)

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

c0 = sqlite3.connect(dbp)
c0.executescript(SCHEMA)
c0.close()

rows = [
    dict(email="[email protected]", ph="h1", name="U1", role="c", av="a", loc="l", dm=0),
    dict(email="[email protected]", ph="h2", name="U2", role="c", av="a", loc="l", dm=0),
    dict(email="[email protected]", ph="h3", name="U3", role="c", av="a", loc="l", dm=0),
    dict(email="[email protected]", ph="h4", name="U4", role="c", av="a", loc="l", dm=0),
    dict(email="[email protected]", ph="h5", name="U5", role="c", av="a", loc="l", dm=0),
]

SQL = """INSERT INTO users_c (email, password_hash, name, role, avatar, location, is_demo)
        VALUES (:email, :ph, :name, :role, :av, :loc, :dm)"""

con = sqlite3.connect(dbp)
try:
    con.execute("BEGIN")
    for d in rows:
        con.execute(SQL, d)  # keyword dict params
    con.commit()
    print("KEYWORD PARAMS OK:")
    for r in con.execute("SELECT id,email,name FROM users_c ORDER BY id"):
        print(" ", r)
except Exception as e:
    print("FAIL:", e)
    con.rollback()
finally:
    con.close()

# ALSO test: List instead of tuple for positional
dbp2 = dbp.replace("_kw.db", "_listpos.db")
if os.path.exists(dbp2):
    os.remove(dbp2)
c2 = sqlite3.connect(dbp2)
c2.executescript(SCHEMA)
try:
    rows2 = [
        ["[email protected]", "h1", "U1", "c", "a", "l", 0],
        ["[email protected]", "h2", "U2", "c", "a", "l", 0],
        ["[email protected]", "h3", "U3", "c", "a", "l", 0],
    ]
    SQL2 = "INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)"
    c2.execute("BEGIN")
    for lst in rows_as_list:
        c2.execute(SQL2, lst)  # list params
    c2.commit()
    print("\nLIST PARAMS (as list, not tuple) OK:")
    for r in c2.execute("SELECT id,email FROM users_c ORDER BY id"):
        print(" ", r)
except Exception as e:
    print("LIST PARAMS FAIL:", e)
    c2.rollback()
finally:
    c2.close()
