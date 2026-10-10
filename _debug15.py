"""Test: per-user add + flush + commit (reset connection state between each user)."""
import os
os.environ["FLASK_DEBUG"] = "0"
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class UserC(db.Model):
    __tablename__ = "users_c"
    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(180), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(255), nullable=False)
    name = sa.Column(sa.String(120), nullable=False)
    role = sa.Column(sa.String(20), nullable=False)
    avatar = sa.Column(sa.String(255))
    location = sa.Column(sa.String(120))
    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    is_demo = sa.Column(sa.Boolean, default=False)

app = Flask(__name__)
app.config["SECRET_KEY"] = "x"
dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_committest.db")
if os.path.exists(dbp):
    os.remove(dbp)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{dbp}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"cached_statements": 0}}
db.init_app(app)

with app.app_context():
    db.engine.dialect.insert_returning = False
    db.create_all()
    # Nuclear: commit after EVERY user
    try:
        for i, (email, name) in enumerate([
            ("[email protected]", "User 1"), ("[email protected]", "User 2"),
            ("[email protected]", "User 3"), ("[email protected]", "User 4"),
        ], 1):
            u = UserC(email=email, password_hash=generate_password_hash("x"), name=name, role="creator", avatar="a", location="l")
            db.session.add(u)
            db.session.flush()
            print(f"  flush {email}: id={u.id}")
            db.session.commit()  # <-- reset pysqlite state
            print(f"  commit OK")
        print("FINAL count=", db.session.query(UserC).count())
    except Exception as e:
        import traceback; traceback.print_exc(limit=3)
        print("FAIL:", e)
