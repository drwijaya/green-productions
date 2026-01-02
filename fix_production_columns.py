"""
Script to migrate production_tasks columns from ENUM to VARCHAR.
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

def fix_column_types():
    with app.app_context():
        try:
            print("Altering production_tasks columns to VARCHAR...")
            db.session.execute(text("ALTER TABLE production_tasks ALTER COLUMN status TYPE VARCHAR(50) USING status::text"))
            db.session.execute(text("ALTER TABLE production_tasks ALTER COLUMN process TYPE VARCHAR(50) USING process::text"))
            db.session.commit()
            print("Successfully converted production_tasks columns to VARCHAR.")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_column_types()
