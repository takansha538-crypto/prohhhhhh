"""Fix: set dialect.insert_returning=False AFTER engine creation."""
import os
os.environ["FLASK_DEBUG"] = "0"
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class UserA(db.Model):
    __tablename__ = "users_a"
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
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_fix.db")
if os.path.exists(db_path):
    os.remove(db_path)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"cached_statements": 0, "check_same_thread": False},
}
db.init_app(app)

with app.app_context():
    # THE FIX: disable insert returning on the dialect after engine created
    print("dialect.insert_returning BEFORE:", getattr(db.engine.dialect, "insert_returning", "N/A"))
    if hasattr(db.engine.dialect, "insert_returning"):
        db.engine.dialect.insert_returning = False
    print("dialect.insert_returning AFTER :", db.engine.dialect.insert_returning)
    db.create_all()
    try:
        for email, name in [("[email protected]", "U1"), ("[email protected]", "U2"), ("[email protected]", "U3"), ("[email protected]", "U4")]:
            u = UserA(email=email, password_hash=generate_password_hash("x"), name=name, role="creator", avatar="a", location="l")
            db.session.add(u)
            db.session.flush()
            print(f"OK {email} id={u.id}")
        db.session.commit()
        print("FINAL OK count=", UserA.query.count())
    except Exception as e:
        import traceback; traceback.print_exc(limit=4)
        print("FAIL:", e)
        db.session.rollback()
