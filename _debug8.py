"""Debug: atomic steps without loop, also check RETURNING behavior."""
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
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', '_testD.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Try disabling RETURNING in SQLite
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"execution_options": {"insertmanyvalues": False}}
db.init_app(app)

with app.app_context():
    db.create_all()
    s = db.session()
    print("1. Creating u1")
    u1 = UserA(email="[email protected]", password_hash=generate_password_hash("x"), name="U1", role="creator", avatar="a", location="l")
    print("2. identity before add u1:", len(s.identity_map))
    s.add(u1)
    print("3. identity after  add u1:", len(s.identity_map), "  session.new:", len(s.new))
    print("4. About to FLUSH u1")
    s.flush()
    print("5. identity after flush u1:", len(s.identity_map), "  u1.id:", u1.id)
    # Do NOT proceed to loop. Print identity multiple times
    print("6. identity check A:", len(s.identity_map))
    print("7. identity check B:", len(s.identity_map))
    # Now create u2
    print("8. Creating u2")
    u2 = UserA(email="[email protected]", password_hash=generate_password_hash("x"), name="U2", role="creator", avatar="a", location="l")
    print("9. identity BEFORE add u2:", len(s.identity_map))
    s.add(u2)
    print("10. identity AFTER add u2:", len(s.identity_map), "  session.new:", len(s.new))
    print("11. FLUSH u2 about to happen")
    try:
        s.flush()
        print("12. identity after flush u2:", len(s.identity_map), "  u2.id:", u2.id)
        s.commit()
        print("SUCCESS")
    except Exception as e:
        print("FAIL at step 11:", type(e).__name__, str(e)[:200])
        s.rollback()
