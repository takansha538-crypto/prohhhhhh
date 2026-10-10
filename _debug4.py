"""Narrow the issue: per-loop flush with echo."""
import os, logging
os.environ["FLASK_DEBUG"] = "0"
logging.basicConfig(level=logging.WARN)
from werkzeug.security import generate_password_hash
from flask import Flask
from database.schema import db, User

app = Flask(__name__)
app.config["SECRET_KEY"] = "x"
# Use a real file DB to avoid in-memory quirks
tmp_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "_test.db")
if os.path.exists(tmp_db):
    os.remove(tmp_db)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_db}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
db.init_app(app)

with app.app_context():
    db.create_all()
    users_data = [
        ("[email protected]", "User One"),
        ("[email protected]", "User Two"),
    ]
    for email, name in users_data:
        u = User(
            email=email,
            password_hash=generate_password_hash("demo123"),
            name=name,
            role="creator",
            avatar="/static/images/avatars/default.svg",
            location="Test",
            is_demo=False,
        )
        print(f"\n>>> ADDING {email}, session.new BEFORE add:", len(db.session.new))
        db.session.add(u)
        print(f">>> session.new AFTER add:", len(db.session.new))
        print(f">>> FLUSHING")
        db.session.flush()
        print(f">>> OK {email} id={u.id}")
    db.session.commit()
    print("\nOK total=", User.query.count())
