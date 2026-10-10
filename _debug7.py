"""Get raw session, bypass scoped_session proxy."""
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
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', '_testC.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    # FIX: get RAW session, not proxy
    s = db.session()  # actually calling scoped_session() __call__ returns raw session
    # In newer fsa, try:
    # s = db.session.registry()  # alternative
    print("s type:", type(s).__name__)
    try:
        for email, name in [("[email protected]", "U1"), ("[email protected]", "U2"), ("[email protected]", "U3")]:
            u = UserA(email=email, password_hash=generate_password_hash("x"), name=name, role="creator", avatar="a", location="l")
            s.add(u)
            print(f"before flush {email}: new={len(s.new)} identity={len(s.identity_map)}")
            s.flush()
            print(f"after  flush {email}: id={u.id}  identity={len(s.identity_map)}")
        s.commit()
        with db.session() as s2:
            print("FIX OK: count=", s2.query(UserA).count())
    except Exception as e:
        import traceback; traceback.print_exc(limit=4)
        print("FAIL:", e)
        s.rollback()
