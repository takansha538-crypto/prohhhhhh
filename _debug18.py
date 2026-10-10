"""Most extreme workaround: new sqlite3 connection PER INSERT."""
import os, sqlite3

dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_perconn.db")
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

rows = [
    ("[email protected]", "h1", "U1", "c", "a", "l", 0),
    ("[email protected]", "h2", "U2", "c", "a", "l", 0),
    ("[email protected]", "h3", "U3", "c", "a", "l", 0),
    ("[email protected]", "h4", "U4", "c", "a", "l", 0),
    ("[email protected]", "h5", "U5", "c", "a", "l", 0),
]

# First create schema with one connection, close it
c0 = sqlite3.connect(dbp)
c0.executescript(SCHEMA)
c0.commit()
c0.close()

print("Schema created, table ok:", sqlite3.connect(dbp).execute("PRAGMA table_info(users_c)").fetchall().__len__(), "cols")

try:
    for email, ph, name, role, av, loc, demo in rows:
        # BRAND NEW connection for each INSERT
        con = sqlite3.connect(dbp)
        con.execute("INSERT INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)",
                    (email, ph, name, role, av, loc, demo))
        con.commit()
        con.close()
    # Final check
    final = sqlite3.connect(dbp)
    print("PER-CONNECTION WORKAROUND OK:")
    for r in final.execute("SELECT id,email,name FROM users_c ORDER BY id"):
        print(" ", r)
    final.close()
except Exception as e:
    print("FAIL:", e)
