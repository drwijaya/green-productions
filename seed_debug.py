# ... imports ...
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.order import Order
from app.models.dso import DSO
from app.models.production import ProductionTask
from app.models.qc import QCSheet, QCResult, DefectLog, DefectSeverity

fake = Faker(['id_ID', 'en_US'])
app = create_app()

def seed_debug():
    with app.app_context():
        employees = Employee.query.all()
        customers = Customer.query.all()
        print(f"DEBUG: {len(employees)} Emps, {len(customers)} Custs")
        
        for i in range(2):
            try:
                # ... same logic ...
                # Reduced for debug
                o_date = datetime.now()
                order = Order(
                    order_code=f"INV-TEST-{uuid.uuid4().hex[:6]}",
                    customer_id=customers[0].id,
                    model="Test Model",
                    qty_total=100,
                    order_date=o_date,
                    status='completed'
                )
                db.session.add(order)
                db.session.flush()
                
                dso = DSO(
                    order_id=order.id, version=1, status='approved',
                    jenis='Test', bahan='Test', warna='Red',
                    created_at=o_date
                )
                db.session.add(dso)
                
                task = ProductionTask(
                   order_id=order.id, process='cutting', status='completed',
                   qty_target=100, qty_completed=100,
                   line_supervisor_id=employees[0].id
                )
                db.session.add(task)
                db.session.flush()
                
                qc = QCSheet(
                   inspection_code=f"QC-TEST-{uuid.uuid4().hex[:6]}",
                   production_task_id=task.id, order_id=order.id,
                   inspector_id=employees[0].id, result=QCResult.PASS,
                   qty_inspected=100, qty_passed=100
                )
                db.session.add(qc)
                db.session.commit()
                print(f"DEBUG: Success {i}")
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG: Failed {i} - {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    seed_debug()
