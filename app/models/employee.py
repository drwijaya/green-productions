"""Employee model."""
from datetime import datetime
from enum import Enum
from ..extensions import db


class EmploymentType(Enum):
    """Employment type/status."""
    KARYAWAN = 'karyawan'           # Permanent employee
    HARIAN_LEPAS = 'harian_lepas'   # Daily worker
    BORONGAN = 'borongan'           # Contract/piece worker
    MAGANG = 'magang'               # Intern


class Employee(db.Model):
    """Employee model linked to user accounts."""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    employment_type = db.Column(db.String(50), default='karyawan')  # karyawan, harian_lepas, borongan, magang
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    join_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    production_tasks = db.relationship('ProductionTask', back_populates='supervisor', foreign_keys='ProductionTask.line_supervisor_id', lazy='dynamic')
    qc_sheets = db.relationship('QCSheet', backref='inspector', lazy='dynamic')
    
    def to_dict(self):
        """Convert employee to dictionary for API response."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_code': self.employee_code,
            'name': self.name,
            'department': self.department,
            'position': self.position,
            'employment_type': self.employment_type,
            'phone': self.phone,
            'email': self.email,
            'join_date': self.join_date.isoformat() if self.join_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Employee {self.name}>'
