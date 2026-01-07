import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.models.material import Material
from app.models.order import Order
from app.models.dso import DSO
from app.models.production import ProductionTask
from app.models.qc import QCSheet, QCResult, DefectLog, DefectSeverity
from sqlalchemy.exc import IntegrityError

fake = Faker(['id_ID', 'en_US'])
app = create_app()

def seed_data():
    with app.app_context():
        print("=== SEEDING DUMMY DATA (V3) ===")
        
        # 1. Employees & Users
        departments = ['Production', 'QC', 'Warehouse', 'Office', 'Design']
        positions = ['Operator', 'Supervisor', 'Manager', 'Staff', 'Director']
        
        employees = []
        print("Creating Employees...")
        for _ in range(15):
            unique_id = uuid.uuid4().hex[:8]
            email = f"emp_{unique_id}@example.com"
            username = f"user_{unique_id}"
            name = fake.name()
            
            user = User(
                email=email,
                username=username,
                full_name=name,
                role=random.choice(['operator', 'admin', 'admin_produksi', 'qc_line', 'owner'])
            )
            user.set_password('password123')
            db.session.add(user)
            try:
                db.session.flush()
                emp = Employee(
                    user_id=user.id,
                    employee_code=f"EMP-{fake.unique.random_number(digits=5)}_{unique_id}",
                    name=name,
                    department=random.choice(departments),
                    position=random.choice(positions),
                    email=email,
                    join_date=fake.date_between(start_date='-2y', end_date='today')
                )
                db.session.add(emp)
                db.session.flush()
                employees.append(emp)
            except Exception as e:
                print(f"Error creating user/employee: {e}")
                db.session.rollback()
                continue

        db.session.commit()
        print(f"Created {len(employees)} employees.")
        
        # Fallback
        if not employees:
             employees = Employee.query.all()
             if not employees:
                 print("CRITICAL: No employees available. Cannot seed transactions.")
                 return

        # 2. Customers
        customers = []
        print("Creating Customers...")
        for _ in range(20):
            cust = Customer(
                name=fake.company(),
                email=fake.email(), # faker email is fine here
                phone=fake.phone_number(),
                address=fake.address()
            )
            db.session.add(cust)
            customers.append(cust)
        db.session.commit()
        # Re-fetch because session commit might expire objects
        customers = Customer.query.all()
        print(f"Total customers: {len(customers)}")

        if not customers:
             print("CRITICAL: No customers available.")
             return

        # 3. Operations ... (Vendors, Materials) - Skipped for speed or minimal logic
        # Just create 1 Vendor and 5 Materials to satisfy constraints if needed
        # ... logic ...
        
        # 5. Transactions (Orders -> 100)
        print("Seeding 100 Transactions (Orders)...")
        
        start_date = datetime.now() - timedelta(days=120)
        
        for i in range(100):
            try:
                o_date = fake.date_time_between(start_date=start_date, end_date='now')
                cust = random.choice(customers)
                unique_suffix = uuid.uuid4().hex[:6]
                
                order = Order(
                    order_code=f"INV-{o_date.strftime('%Y%m')}-{i+2000}-{unique_suffix}",
                    customer_id=cust.id,
                    model=fake.catch_phrase(),
                    qty_total=random.choice([50, 100, 200, 500]),
                    order_date=o_date,
                    deadline=o_date + timedelta(days=30),
                    status=random.choice(['completed', 'in_production', 'qc_pending']),
                    priority=1,
                    created_at=o_date
                )
                db.session.add(order)
                db.session.flush()
                
                # DSO
                dso = DSO(order_id=order.id, version=1, status='approved', created_at=o_date)
                db.session.add(dso)
                
                # Production Task
                task = ProductionTask(
                    order_id=order.id, process='cutting', status='completed', 
                    qty_target=order.qty_total, qty_completed=order.qty_total,
                    planned_start=o_date, planned_end=o_date+timedelta(days=1),
                    pic_id=employees[0].id # safe pick
                )
                db.session.add(task)
                db.session.flush()
                
                # QC
                qc = QCSheet(
                    inspection_code=f"QC-{order.order_code}-CUT-{unique_suffix}",
                    production_task_id=task.id,
                    order_id=order.id,
                    inspector_id=employees[0].id,
                    result=QCResult.PASS,
                    qty_inspected=order.qty_total,
                    qty_passed=order.qty_total,
                    qty_failed=0,
                    created_at=o_date+timedelta(days=1)
                )
                db.session.add(qc)
                db.session.commit()
                if i % 10 == 0:
                    print(f"Seeded {i} orders...")
                    
            except Exception as e:
                db.session.rollback()
                print(f"Error seeding order {i}: {e}")
                continue

        print("Success! Seeded Transactions.")

if __name__ == '__main__':
    seed_data()
