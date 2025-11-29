from application.database import db
from app import app

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database reset successful — all tables dropped and recreated.")
