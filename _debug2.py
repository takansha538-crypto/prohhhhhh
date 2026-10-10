"""Step-by-step seed debug."""
import os
os.environ["FLASK_DEBUG"] = "0"
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from database.schema import db, User, CreatorProfile

app = Flask(__name__)
app.config["SECRET_KEY"] = "debug"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    app.instance_path, "creatorshub.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
os.makedirs(app.instance_path, exist_ok=True)
print("Instance path:", app.instance_path)
# wipe the file
db_path = os.path.join(app.instance_path, "creatorshub.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Removed old DB.")

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Tables created. User count before seed:", User.query.count())

    # Now manually run the seed with per-step prints
    from database.seed import _seed
    try:
        _seed()
        db.session.commit()
        print("SEED OK. Users:", User.query.count(), "Creators:", CreatorProfile.query.count())
    except Exception as e:
        print("SEED FAILED:", type(e).__name__, str(e)[:300])
        db.session.rollback()
        print("Rolled back. User count:", User.query.count())
