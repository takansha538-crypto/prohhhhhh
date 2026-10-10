"""Compare: per-row flush vs batch flush, no func.now(), no defaults."""
import os
os.environ["FLASK_DEBUG"] = "0"
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class UserB(db.Model):
    __tablename__ = "users_b"
    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(180), unique=True, nullable=False)
    name = sa.Column(sa.String(120), nullable=False)

def run_test(which):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "x"
    dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", f"_t{which}.db")
    if os.path.exists(dbp):
        os.remove(dbp)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{dbp}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"cached_statements": 0}}
    db.init_app(app)
    with app.app_context():
        db.engine.dialect.insert_returning = False
        db.create_all()
        try:
            if which == 1:
                print("Test 1: PER-ROW flush")
                for i in range(1, 5):
                    email = f"user{i}@t.com"
                    u = UserB(email=email, name=f"Name{i}")
                    db.session.add(u)
                    db.session.flush()
                    print(f"  flush {email} id={u.id}")
                db.session.commit()
            else:
                print("Test 2: BATCH flush (one flush at end)")
                objs = []
                for i in range(1, 5):
                    email = f"user{i}@t.com"
                    u = UserB(email=email, name=f"Name{i}")
                    db.session.add(u)
                    objs.append(u)
                    print(f"  added {email}")
                db.session.flush()  # ONE FLUSH
                for u in objs:
                    print(f"  after one flush: {u.email} id={u.id}")
                db.session.commit()
            print(f"  => Test {which} OK: count=", db.session.query(UserB).count())
        except Exception as e:
            print(f"  => Test {which} FAIL:", e)
            db.session.rollback()

run_test(1)
print()
# Need new Flask app context / db since fsa db singleton bound to previous
# Actually db = SQLAlchemy() is global above, so running twice is unsafe.
# Run test 2 separately via subprocess to avoid singleton issues
