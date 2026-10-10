"""Minimal test: does per-loop flush + scoped_session work?"""
import os
os.environ["FLASK_DEBUG"] = "0"
from werkzeug.security import generate_password_hash
from flask import Flask
from database.schema import db, User

app = Flask(__name__)
app.config["SECRET_KEY"] = "x"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    users_data = [
        ("[email protected]", "User One"),
        ("[email protected]", "User Two"),
        ("[email protected]", "User Three"),
    ]
    try:
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
            db.session.add(u)
            print(f"Before flush {email}: session new={u in db.session.new}")
            db.session.flush()
            print(f"After  flush {email}: id={u.id}  identity key={u in db.session.identity_map.values()}")
            # Check if the user is now really in the DB
            cnt = User.query.count()
            print(f"  User.count() = {cnt}")
        db.session.commit()
        print("OK. Total:", User.query.count())
    except Exception as e:
        print("FAIL:", type(e).__name__, str(e)[:200])
        import traceback; traceback.print_exc(limit=6)
