# init_db.py
from app import create_app
from app.extensions import db
from app.models import (
    User,
    Post,
    Transaction,
    Balance,
)  # Make sure ALL models are imported

app = create_app()

with app.app_context():
    # Drop all tables first to ensure a clean slate
    db.drop_all()
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")
