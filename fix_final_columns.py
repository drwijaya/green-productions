"""
Script to migrate users and dso columns from ENUM to VARCHAR.
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

def fix_column_types():
    with app.app_context():
        try:
            print("Altering users.role column to VARCHAR...")
            db.session.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50) USING role::text"))
            
            print("Altering dso.status column to VARCHAR...")
            db.session.execute(text("ALTER TABLE dso ALTER COLUMN status TYPE VARCHAR(50) USING status::text"))
            
            db.session.commit()
            print("Successfully converted users and dso columns to VARCHAR.")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_column_types()
