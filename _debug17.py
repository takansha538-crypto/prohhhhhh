"""Nuclear workaround: unique SQL text per INSERT to bypass cache."""
import os, sqlite3

dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_unique.db")
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

# WORKAROUND: include a per-row value in the SQL as a comment so the statement
# cache considers each INSERT to be a distinct prepared statement.
# This defeats the pysqlite 3.14 bug where cached bound params are re-applied.
con = sqlite3.connect(dbp, cached_statements=0)  # 0 should disable but doesn't...
con.executescript(SCHEMA)
try:
    con.execute("BEGIN")
    for email, ph, name, role, av, loc, demo in rows:
        # Use row-unique comment embedded in SQL to force unique statement hash
        sql = f"INSERT /* row_{email} */ INTO users_c (email,password_hash,name,role,avatar,location,is_demo) VALUES (?,?,?,?,?,?,?)"
        con.execute(sql, (email, ph, name, role, av, loc, demo))
    con.commit()
    print("WORKAROUND (unique SQL text) OK:")
    for r in con.execute("SELECT id,email,name FROM users_c"):
        print(" ", r)
except Exception as e:
    print("FAIL:", e)
    con.rollback()
finally:
    con.close()
