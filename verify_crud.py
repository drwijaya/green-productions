import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app, db
from app.models.order import Order, OrderStatus
from app.models.customer import Customer

def verify():
    app = create_app()
    with app.app_context():
        print(f"Testing DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            # Clean up test data first
            Order.query.filter_by(order_code="CRUD-TEST").delete()
            db.session.commit()
            
            # Ensure at least one customer
            c = Customer.query.first()
            if not c:
                print("No customer found. Seed first.")
                return

            # Create
            o = Order(order_code="CRUD-TEST", model="Test", qty_total=1, status=OrderStatus.DRAFT, customer_id=c.id)
            db.session.add(o)
            db.session.commit()
            print("Create OK")

            # Read
            o = Order.query.filter_by(order_code="CRUD-TEST").first()
            assert o is not None
            print(f"Read OK: {o.order_code}")

            # Update
            o.model = "Test Updated"
            db.session.commit()
            o2 = Order.query.filter_by(order_code="CRUD-TEST").first()
            assert o2.model == "Test Updated"
            print("Update OK")

            # Delete
            db.session.delete(o)
            db.session.commit()
            o3 = Order.query.filter_by(order_code="CRUD-TEST").first()
            assert o3 is None
            print("Delete OK")
            
        except Exception as e:
            print(f"CRUD Failed: {e}")
            raise e

if __name__ == '__main__':
    verify()
