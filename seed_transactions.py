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

def seed_transactions():
    with app.app_context():
        print("=== SEEDING TRANSACTIONS (V2 - Fixed) ===")
        
        employees = Employee.query.all()
        customers = Customer.query.all()
        
        if not employees:
            print("No employees found.")
            return
        if not customers:
            print("No customers found.")
            return
            
        print(f"Found {len(employees)} employees and {len(customers)} customers.")
        
        success = 0
        errors = 0
        
        start_date = datetime.now() - timedelta(days=120)
        
        for i in range(100):
            try:
                # Randomize Dates
                o_date = fake.date_time_between(start_date=start_date, end_date='now')
                cust = random.choice(customers)
                unique_suffix = uuid.uuid4().hex[:6]
                
                # Create Order
                order_code = f"INV-{o_date.strftime('%Y%m')}-{fake.unique.random_number(digits=6)}"
                
                order = Order(
                    order_code=order_code,
                    customer_id=cust.id,
                    model=fake.catch_phrase(),
                    qty_total=random.choice([50, 100, 200, 500, 1000]),
                    order_date=o_date,
                    deadline=o_date + timedelta(days=random.randint(14, 45)),
                    status=random.choice(['completed', 'in_production', 'qc_pending', 'draft']),
                    priority=random.randint(1, 3),
                    created_at=o_date
                )
                db.session.add(order)
                db.session.flush()
                
                # Create DSO (Fixed fields)
                dso = DSO(
                    order_id=order.id,
                    version=1,
                    status='approved',
                    jenis=fake.word(),
                    bahan=fake.word(),
                    warna=fake.color_name(),
                    kancing='Standard Button',
                    resleting='YKK Zipper',
                    benang='Polyester',
                    created_at=o_date
                )
                db.session.add(dso)
                
                # Logic
                if order.status != 'draft':
                    processes = ['Cutting', 'Sewing', 'Finishing']
                    
                    for seq, proc in enumerate(processes, 1):
                        # Task Status Logic
                        t_status = 'pending'
                        if order.status == 'completed':
                            t_status = 'completed'
                        elif order.status == 'qc_pending':
                            t_status = 'completed'
                        elif order.status == 'in_production':
                            if proc == 'Cutting': t_status = 'completed'
                            elif proc == 'Sewing': t_status = random.choice(['in_progress', 'completed'])
                        
                        pic = random.choice(employees)
                        
                        task_start = o_date + timedelta(days=seq*2)
                        task_end = task_start + timedelta(days=2)
                        
                        task = ProductionTask(
                            order_id=order.id,
                            task_name=f"{proc} Process",
                            process=proc.lower(), # cutting, sewing, finishing
                            sequence=seq,
                            status=t_status,
                            line_supervisor_id=pic.id,
                            planned_start=task_start,
                            planned_end=task_end,
                            qty_target=order.qty_total,
                            qty_completed=order.qty_total if t_status == 'completed' else 0,
                            created_at=o_date
                        )
                        
                        if t_status == 'completed':
                            task.actual_start = task_start
                            task.actual_end = task_end
                            
                        db.session.add(task)
                        db.session.flush()
                        
                        if t_status == 'completed':
                            # QC
                            is_pass = random.random() < 0.85
                            res = QCResult.PASS if is_pass else QCResult.FAIL
                            
                            inspector = random.choice(employees)
                            qc_code = f"QC-{order_code}-{proc[:3].upper()}-{fake.unique.random_number(digits=4)}"
                            
                            qc = QCSheet(
                                inspection_code=qc_code,
                                production_task_id=task.id,
                                order_id=order.id,
                                inspector_id=inspector.id,
                                result=res,
                                qty_inspected=order.qty_total,
                                qty_passed=order.qty_total if is_pass else int(order.qty_total * 0.9),
                                qty_failed=0 if is_pass else int(order.qty_total * 0.1),
                                inspected_at=task.actual_end,
                                created_at=task.actual_end
                            )
                            db.session.add(qc)
                            db.session.flush()
                            
                            if not is_pass:
                                # Defects
                                defect_types = ['Jahitan Miring', 'Kain Robek', 'Salah Warna', 'Ukuran Tidak Sesuai']
                                for _ in range(random.randint(1, 3)):
                                    d = DefectLog(
                                        qc_sheet_id=qc.id,
                                        defect_type=random.choice(defect_types),
                                        severity=random.choice(list(DefectSeverity)),
                                        qty_defect=random.randint(1, 10),
                                        status='resolved' if order.status == 'completed' else 'open',
                                        station='Station A',
                                        process_stage=proc.lower(),
                                        reported_by=inspector.id,
                                        created_at=qc.created_at
                                    )
                                    db.session.add(d)

                db.session.commit()
                success += 1
                if success % 10 == 0:
                    print(f"Created {success} orders...")
                    
            except Exception as e:
                db.session.rollback()
                print(f"Error on order {i}: {e}")
                errors += 1
                
        print(f"DONE. Success: {success}, Errors: {errors}")

if __name__ == '__main__':
    seed_transactions()
