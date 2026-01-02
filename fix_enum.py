"""Add qc_pending to orderstatus enum."""
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    try:
        db.session.execute(db.text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'qc_pending'"))
        db.session.commit()
        print("Added qc_pending to orderstatus enum")
    except Exception as e:
        print(f"Error (may already exist): {e}")
        db.session.rollback()
