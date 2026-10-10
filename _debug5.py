"""Compare: standalone model vs project model."""
import os
os.environ["FLASK_DEBUG"] = "0"
from werkzeug.security import generate_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

# Test A: Standalone
dbA = SQLAlchemy()

class UserA(dbA.Model):
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
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', '_testA.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
dbA.init_app(app)

with app.app_context():
    dbA.create_all()
    try:
        for email, name in [("[email protected]", "U1"), ("[email protected]", "U2")]:
            u = UserA(email=email, password_hash=generate_password_hash("x"), name=name, role="creator", avatar="a", location="l")
            dbA.session.add(u)
            print(f"before flush {email}: new={len(dbA.session.new)} identity={len(dbA.session.identity_map)}")
            dbA.session.flush()
            print(f"after  flush {email}: id={u.id}  identity={len(dbA.session.identity_map)}")
        dbA.session.commit()
        print("Standalone OK: count=", UserA.query.count())
    except Exception as e:
        print("STANDALONE FAIL:", e)
        dbA.session.rollback()
