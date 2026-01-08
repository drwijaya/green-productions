
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.order import Order
from app.models.production import ProductionTask, ProcessType
from app.models.qc import QCSheet, DefectLog, QCResult, DefectSeverity
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.user import User

def seed_analytics_data():
    app = create_app()
    
    with app.app_context():
        print("Starting dummy data generation...")
        
        # 1. Ensure we have dummy master data
        customer = Customer.query.first()
        if not customer:
            customer = Customer(name="PT Maju Mundur", code="CUST-001", email="info@majumundur.com")
            db.session.add(customer)
            db.session.commit()
            print("Created dummy customer")
            
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Warning: Admin user not found, using ID 1")
            admin_id = 1
        else:
            admin_id = admin_user.id
            
        # 2. Generate 30 Orders
        products = [
            "Kaos Polos Cotton 30s", "Kemeja Tactical", "Jaket Hoodie Fleece", 
            "Seragam Batik Sekolah", "Rompi Safety Site", "Kaos Polo Bordir", 
            "Celana Chino", "Jaket Bomber", "Kemeja Flanel", "Tas Totebag Canvas"
        ]
        
        defect_types = [
            "Jahitan Loncat", "Benang Sisa", "Noda Oli", "Ukuran Tidak Sesuai", 
            "Kancing Lepas", "Warna Belang", "Sablon Pecah", "Lubang Kecil", 
            "Kerut Jahitan", "Label Miring"
        ]
        
        # Generate dates over last 6 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        created_count = 0
        
        for i in range(35): # Generate slightly more to ensure good coverage
            # Random date
            days_offset = random.randint(0, 180)
            order_date = end_date - timedelta(days=days_offset)
            
            # Random qty 100-500
            qty = random.randint(100, 500)
            
            # Create Order
            order_code = f"INV-{order_date.strftime('%Y%m')}-{random.randint(1000, 9999)}"
            
            # Check if exists
            if Order.query.filter_by(order_code=order_code).first():
                continue
                
            model = random.choice(products)
            
            print(f"Creating order {order_code}...", flush=True)
            try:
                order = Order(
                    order_code=order_code,
                    customer_id=customer.id,
                    model=model,
                    description=f"Order dummy untuk {model}",
                    qty_total=qty,
                    order_date=order_date,
                    deadline=order_date + timedelta(days=14),
                    status='completed', # Assuming mostly completed for historic analysis
                    created_by=admin_id,
                    created_at=order_date
                )
                db.session.add(order)
                db.session.flush()
                
                # Create Production Tasks (simplified: Sewing, Finishing)
                # We focus on these for defects
                tasks = []
                
                # Sewing Task
                sewing_task = ProductionTask(
                    order_id=order.id,
                    process='Sewing',
                    status='completed',
                    # qty_target=qty, # ProductionTask schema might not have this? Check model
                    qty_target=qty,
                    qty_completed=qty,
                    planned_start=order_date + timedelta(days=2),
                    planned_end=order_date + timedelta(days=7),
                    actual_start=order_date + timedelta(days=2),
                    actual_end=order_date + timedelta(days=7),
                    qty_defect=0 # Will update this aggregation later if we wanted
                )
                db.session.add(sewing_task)
                tasks.append(sewing_task)
                
                # Finishing Task
                finishing_task = ProductionTask(
                    order_id=order.id,
                    process='Finishing',
                    status='completed',
                    qty_target=qty,
                    qty_completed=qty,
                    planned_start=order_date + timedelta(days=8),
                    planned_end=order_date + timedelta(days=10),
                    actual_start=order_date + timedelta(days=8),
                    actual_end=order_date + timedelta(days=10),
                    qty_defect=0
                )
                db.session.add(finishing_task)
                tasks.append(finishing_task)
                
                db.session.flush()
                
                # Create QC Sheets and Defects
                # Varies pass/fail rate
                # Good period: 98% pass
                # Bad period: 90% pass
                # Randomly affect quality based on "random luck" (or simulate a bad month)
                
                is_bad_batch = random.random() < 0.2 # 20% chance of being a bad batch
                
                if is_bad_batch:
                    fail_rate = random.uniform(0.05, 0.15) # 5-15% fail
                else:
                    fail_rate = random.uniform(0.0, 0.03) # 0-3% fail
                    
                for task in tasks:
                    # QC Check for this task
                    inspected_qty = qty # Full inspection
                    failed_qty = int(inspected_qty * fail_rate)
                    passed_qty = inspected_qty - failed_qty
                
                result = 'pass'
                if failed_qty > 0:
                    if failed_qty / inspected_qty > 0.05:
                        result = QCResult.FAIL
                    else:
                        result = QCResult.CONDITIONAL_PASS
                else:
                    result = QCResult.PASS
                
                # Checkbox JSON (dummy)
                checklist = []
                # Add some standard checkpoints
                checkpoints = ["Ukuran", "Jahitan", "Kebersihan", "Warna"]
                for pt in checkpoints:
                    chk = random.randint(int(inspected_qty*0.2), inspected_qty)
                    ng = 0
                    if failed_qty > 0:
                        ng = random.randint(0, failed_qty)
                    
                    checklist.append({
                        "name": pt, 
                        "qty_checked": chk, 
                        "qty_ng": ng, 
                        "status": "pass" if ng == 0 else "fail"
                    })

                qc_sheet = QCSheet(
                    production_task_id=task.id,
                    inspection_code=QCSheet.generate_inspection_code(),
                    inspector_id=1, # Dummy
                    inspected_at=task.actual_end,
                    qty_inspected=inspected_qty,
                    qty_passed=passed_qty,
                    qty_failed=failed_qty,
                    result=result,
                    checklist_json=checklist,
                    created_at=task.actual_end
                )
                db.session.add(qc_sheet)
                db.session.flush()
                
                # Create Defect Logs if any failed
                remaining_defects = failed_qty
                
                while remaining_defects > 0:
                    defect_qty = random.randint(1, min(5, remaining_defects))
                    dtype = random.choice(defect_types)
                    
                    defect = DefectLog(
                        qc_sheet_id=qc_sheet.id,
                        defect_type=dtype,
                        qty_defect=defect_qty,
                        severity=DefectSeverity.MINOR if random.random() > 0.2 else DefectSeverity.MAJOR,
                        status='resolved', # Historic data mostly resolved
                        process_stage=task.process,
                        created_at=task.actual_end,
                        description=f"Temuan {dtype} pada bagian lengan/body",
                        action_taken="Rework / Perbaikan jahit",
                        resolved_at=task.actual_end + timedelta(days=1)
                    )
                    db.session.add(defect)
                    remaining_defects -= defect_qty
            
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error creating order {order_code}: {str(e)}", flush=True)
                import traceback
                traceback.print_exc()
            
            created_count += 1
            print(f"Created Order {order.order_code} - {model} ({qty} pcs) - Date: {order_date.date()}")
            
        try:
            db.session.commit()
            print(f"✅ Successfully finished batch!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing: {str(e)}")

if __name__ == '__main__':
    seed_analytics_data()
