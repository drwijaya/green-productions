"""Production task models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class ProcessType(Enum):
    """Production process types."""
    CUTTING = 'cutting'
    SEWING = 'sewing'
    SABLON = 'sablon'
    FINISHING = 'finishing'
    PACKING = 'packing'


class TaskStatus(Enum):
    """Production task status."""
    PENDING = 'pending'          # Task created, no workers assigned
    ASSIGNED = 'assigned'        # Workers assigned, not started yet
    IN_PROGRESS = 'in_progress'  # Work in progress
    COMPLETED = 'completed'      # Task completed


class ProductionTask(db.Model):
    """Production task for each process."""
    __tablename__ = 'production_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    process = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')
    
    # Line Supervisor (PIC for the whole task)
    line_supervisor_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Schedule
    planned_start = db.Column(db.DateTime)
    planned_end = db.Column(db.DateTime)
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    
    # Quantity Tracking
    qty_target = db.Column(db.Integer, default=0)
    qty_completed = db.Column(db.Integer, default=0)
    qty_defect = db.Column(db.Integer, default=0)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Sequence order
    sequence = db.Column(db.Integer, default=0)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supervisor = db.relationship('Employee', foreign_keys=[line_supervisor_id])
    worker_logs = db.relationship('ProductionWorkerLog', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    qc_sheets = db.relationship('QCSheet', backref='production_task', lazy='dynamic')
    
    def get_progress_percentage(self):
        """Calculate task progress percentage."""
        if self.qty_target == 0:
            return 0
        return int((self.qty_completed / self.qty_target) * 100)
    
    def get_defect_rate(self):
        """Calculate defect rate percentage."""
        if self.qty_completed == 0:
            return 0
        return round((self.qty_defect / self.qty_completed) * 100, 2)
    
    def update_qty_from_workers(self):
        """Update qty_completed from all worker logs."""
        total = sum(log.qty_completed for log in self.worker_logs.all())
        self.qty_completed = total
        if total >= self.qty_target:
            self.status = 'completed'
            self.actual_end = datetime.utcnow()
    
    def start_task(self):
        """Start the production task."""
        self.status = 'in_progress'
        self.actual_start = datetime.utcnow()
    
    def complete_task(self):
        """Complete the production task."""
        self.status = 'completed'
        self.actual_end = datetime.utcnow()
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'process': self.process,
            'status': self.status,
            'line_supervisor_id': self.line_supervisor_id,
            'planned_start': self.planned_start.isoformat() if self.planned_start else None,
            'planned_end': self.planned_end.isoformat() if self.planned_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'qty_target': self.qty_target,
            'qty_completed': self.qty_completed,
            'qty_defect': self.qty_defect,
            'progress': self.get_progress_percentage(),
            'defect_rate': self.get_defect_rate(),
            'notes': self.notes,
            'sequence': self.sequence
        }
        
        if include_relations:
            data['supervisor'] = self.supervisor.to_dict() if self.supervisor else None
            data['order'] = self.order.to_dict() if self.order else None
            data['worker_logs'] = [log.to_dict() for log in self.worker_logs.all()]
        
        return data
    
    def __repr__(self):
        return f'<ProductionTask {self.process.value} Order:{self.order_id}>'


class ProductionWorkerLog(db.Model):
    """Individual worker contribution log for a production task."""
    __tablename__ = 'production_worker_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('production_tasks.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # Quantity done by this worker
    qty_completed = db.Column(db.Integer, default=0)
    qty_defect = db.Column(db.Integer, default=0)
    
    # Time tracking
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', foreign_keys=[employee_id])
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'qty_completed': self.qty_completed,
            'qty_defect': self.qty_defect,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<ProductionWorkerLog Task:{self.task_id} Employee:{self.employee_id}>'

