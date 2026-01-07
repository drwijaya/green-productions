"""Order model."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class OrderStatus(Enum):
    """Order status enum (simplified)."""
    DRAFT = 'draft'
    IN_PRODUCTION = 'in_production'
    QC_PENDING = 'qc_pending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Order(db.Model):
    """Order model for production management."""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Product Details
    model = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    qty_total = db.Column(db.Integer, nullable=False)
    
    # Dates
    order_date = db.Column(db.Date, default=datetime.utcnow)
    deadline = db.Column(db.Date)
    
    # Status and Priority
    status = db.Column(db.String(50), default='draft')
    priority = db.Column(db.Integer, default=1)  # 1=Normal, 2=High, 3=Urgent
    
    # DSO Status for tracking DSO creation: not_created, draft, created
    dso_status = db.Column(db.String(50), default='not_created')
    
    # QC Assignment
    qc_inspector_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Notes
    customer_notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dso = db.relationship('DSO', backref='order', lazy='dynamic')
    production_tasks = db.relationship('ProductionTask', backref='order', lazy='dynamic')
    barcodes = db.relationship('Barcode', backref='order', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[created_by])
    qc_inspector = db.relationship('Employee', foreign_keys=[qc_inspector_id])
    
    @staticmethod
    def generate_order_code():
        """Generate unique order code."""
        today = datetime.now()
        prefix = f"INV-{today.strftime('%Y%m')}"
        last_order = Order.query.filter(
            Order.order_code.like(f'{prefix}%')
        ).order_by(Order.id.desc()).first()
        
        if last_order:
            last_num = int(last_order.order_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def get_current_dso(self):
        """Get the latest approved DSO version."""
        return self.dso.filter_by(status='approved').order_by(
            db.desc('version')
        ).first()
    
    def get_production_progress(self):
        """Calculate production progress percentage."""
        tasks = self.production_tasks.all()
        if not tasks:
            return 0
        completed = sum(1 for t in tasks if t.status == 'completed')
        return int((completed / len(tasks)) * 100)
    
    def get_latest_dso(self):
        """Get the latest DSO version (any status)."""
        return self.dso.order_by(db.desc('version')).first()
    
    def update_dso_status(self):
        """Update DSO status based on existing DSOs."""
        dsos = self.dso.all()
        if not dsos:
            self.dso_status = 'not_created'
        else:
            latest = self.get_latest_dso()
            if latest.status == 'approved':
                self.dso_status = 'created'
            else:
                self.dso_status = 'draft'
    
    def to_dict(self, include_relations=False):
        """Convert order to dictionary for API response."""
        data = {
            'id': self.id,
            'order_code': self.order_code,
            'customer_id': self.customer_id,
            'model': self.model,
            'description': self.description,
            'qty_total': self.qty_total,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'priority': self.priority,
            'dso_status': self.dso_status,
            'customer_notes': self.customer_notes,
            'internal_notes': self.internal_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'production_progress': self.get_production_progress()
        }
        
        if include_relations:
            data['customer'] = self.customer.to_dict() if self.customer else None
            current_dso = self.get_current_dso()
            data['current_dso'] = current_dso.to_dict() if current_dso else None
            # Include QC reports summary
            data['qc_reports'] = [
                {'id': sheet.id, 'production_task_id': sheet.production_task_id, 'result': sheet.result.value if sheet.result else 'pending'}
                for sheet in self.qc_reports.all()
            ] if hasattr(self, 'qc_reports') else []
        
        return data
    
    def __repr__(self):
        return f'<Order {self.order_code}>'
