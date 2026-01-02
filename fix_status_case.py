"""Fix status case in database - convert uppercase to lowercase."""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

def fix_status_case():
    with app.app_context():
        try:
            # Fix Order status
            print("Fixing Order status values...")
            db.session.execute(text("UPDATE orders SET status = LOWER(status)"))
            
            # Fix ProductionTask status and process
            print("Fixing ProductionTask status and process values...")
            db.session.execute(text("UPDATE production_tasks SET status = LOWER(status)"))
            db.session.execute(text("UPDATE production_tasks SET process = LOWER(process)"))
            
            # Fix DSO status
            print("Fixing DSO status values...")
            db.session.execute(text("UPDATE dso SET status = LOWER(status)"))
            
            # Fix User role
            print("Fixing User role values...")
            db.session.execute(text("UPDATE users SET role = LOWER(role)"))
            
            db.session.commit()
            print("Done! All status values converted to lowercase.")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_status_case()
