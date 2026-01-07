"""Database seeder for initial data."""
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee

def seed_database():
    """Seed the database with initial data."""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                email='admin@greenproduction.com',
                username='admin',
                full_name='System Administrator',
                role=UserRole.ADMIN.value,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create admin employee
            admin_emp = Employee(
                user=admin,
                employee_code='EMP00001',
                name='System Administrator',
                department='IT',
                position='Admin'
            )
            db.session.add(admin_emp)
        
        # Create demo users
        demo_users = [
            ('owner', 'owner@greenproduction.com', 'Owner', 'Pak Budi Owner', UserRole.OWNER),
            ('produksi', 'produksi@greenproduction.com', 'Admin Produksi', 'Ibu Siti Produksi', UserRole.ADMIN_PRODUKSI),
            ('qc', 'qc@greenproduction.com', 'QC Line', 'Pak Joko QC', UserRole.QC_LINE),
            ('operator', 'operator@greenproduction.com', 'Operator', 'Andi Operator', UserRole.OPERATOR),
        ]
        
        for username, email, name, full_name, role in demo_users:
            if not User.query.filter_by(username=username).first():
                print(f"Creating user: {username}")
                user = User(
                    email=email,
                    username=username,
                    full_name=full_name,
                    role=role.value,
                    is_active=True
                )
                user.set_password('password123')
                db.session.add(user)
                
                emp = Employee(
                    user=user,
                    employee_code=f'EMP{User.query.count() + 1:05d}',
                    name=full_name,
                    department=name,
                    position=name
                )
                db.session.add(emp)
        
        # Create demo customers
        demo_customers = [
            ('PT. Fashion Indonesia', 'Fashion Indonesia', 'Pak Ahmad', '081234567890', 'Jakarta'),
            ('CV. Textile Jaya', 'Textile Jaya', 'Bu Dewi', '082345678901', 'Bandung'),
            ('Toko Baju Maju', 'Baju Maju', 'Pak Rudi', '083456789012', 'Surabaya'),
        ]
        
        for name, company, contact, phone, city in demo_customers:
            if not Customer.query.filter_by(name=name).first():
                print(f"Creating customer: {name}")
                customer = Customer(
                    name=name,
                    company_name=company,
                    contact_person=contact,
                    phone=phone,
                    city=city,
                    is_active=True
                )
                db.session.add(customer)
        
        db.session.commit()
        print("Database seeded successfully!")
        print("\n=== Login Credentials ===")
        print("Admin: admin / admin123")
        print("Owner: owner / password123")
        print("Produksi: produksi / password123")
        print("QC: qc / password123")
        print("Operator: operator / password123")

if __name__ == '__main__':
    seed_database()
