"""Verify workaround: COMMIT between inserts."""
import os, sqlite3
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_raw2.db")
if os.path.exists(db_path):
    os.remove(db_path)

con = sqlite3.connect(db_path)
con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT)")

# WORKAROUND 1: explicit commit between inserts
print("=== Test: commit between each insert ===")
try:
    con.execute("INSERT INTO users (email, name) VALUES (?, ?) RETURNING id", ("[email protected]", "u1"))
    con.commit()  # <-- explicit commit
    con.execute("INSERT INTO users (email, name) VALUES (?, ?) RETURNING id", ("[email protected]", "u2"))
    con.commit()
    con.execute("INSERT INTO users (email, name) VALUES (?, ?) RETURNING id", ("[email protected]", "u3"))
    con.commit()
    print("WORKAROUND 1 OK: rows=", con.execute("SELECT * FROM users").fetchall())
except Exception as e:
    print("WORKAROUND 1 FAIL:", e)

# WORKAROUND 2: no RETURNING, use last_insert_rowid
print("\n=== Test: no RETURNING at all ===")
db_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_raw3.db")
if os.path.exists(db_path2):
    os.remove(db_path2)
con2 = sqlite3.connect(db_path2)
con2.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT)")
try:
    con2.execute("BEGIN")
    con2.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("[email protected]", "u1"))
    id1 = con2.execute("SELECT last_insert_rowid()").fetchone()[0]
    print("u1 id:", id1)
    con2.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("[email protected]", "u2"))
    id2 = con2.execute("SELECT last_insert_rowid()").fetchone()[0]
    print("u2 id:", id2)
    con2.execute("INSERT INTO users (email, name) VALUES (?, ?)", ("[email protected]", "u3"))
    id3 = con2.execute("SELECT last_insert_rowid()").fetchone()[0]
    print("u3 id:", id3)
    con2.commit()
    print("WORKAROUND 2 OK: rows=", con2.execute("SELECT * FROM users").fetchall())
except Exception as e:
    print("WORKAROUND 2 FAIL:", e)

# WORKAROUND 3: disable RETURNING dialect-wide in SQLAlchemy
print("\n=== Test: SQLAlchemy with insert_returning disabled ===")
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
# Patch the sqlite dialect
original = SQLiteDialect.supports_returning
print(f"  original supports_returning: {original}")
SQLiteDialect.supports_returning = property(lambda self: False)

import sqlalchemy as sa
from flask import Flask
from flask_sqlalchemy import SQLAlchemy as FSA

fsa = FSA()

class UA(fsa.Model):
    __tablename__ = "ua"
    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(80), unique=True, nullable=False)
    name = sa.Column(sa.String(80), nullable=False)

app = Flask(__name__)
app.config["SECRET_KEY"] = "x"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', '_nor.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
fsa.init_app(app)

with app.app_context():
    fsa.create_all()
    s = fsa.session()
    try:
        for i, (email, name) in enumerate([("[email protected]", "X1"), ("[email protected]", "X2"), ("[email protected]", "X3")], 1):
            u = UA(email=email, name=name)
            s.add(u)
            s.flush()
            print(f"  {email} id={u.id}")
        s.commit()
        print("WORKAROUND 3 OK: count=", UA.query.count())
    except Exception as e:
        print("WORKAROUND 3 FAIL:", e)
    finally:
        SQLiteDialect.supports_returning = original  # restore
