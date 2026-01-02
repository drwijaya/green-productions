"""Audit and Change Request models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class ChangeRequestStatus(Enum):
    """Change request status."""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    IMPLEMENTED = 'implemented'


class ActivityLog(db.Model):
    """Activity log for audit trail."""
    __tablename__ = 'activity_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # What was accessed/modified
    module = db.Column(db.String(50), nullable=False)  # 'order', 'dso', 'qc', etc.
    action = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'view', etc.
    
    # Reference to the affected record
    record_id = db.Column(db.Integer)
    record_type = db.Column(db.String(50))
    
    # Data snapshot (before and after for updates)
    data_before = db.Column(db.JSON)
    data_after = db.Column(db.JSON)
    
    # Additional info
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'module': self.module,
            'action': self.action,
            'record_id': self.record_id,
            'record_type': self.record_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<ActivityLog {self.module}:{self.action} by User:{self.user_id}>'


class ChangeRequest(db.Model):
    """Change request for DSO modifications."""
    __tablename__ = 'change_request'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False)
    
    # Request details
    request_code = db.Column(db.String(50), unique=True, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, default=1)  # 1=Normal, 2=High, 3=Urgent
    
    # What changes are requested
    changes_json = db.Column(db.JSON)
    # Example: [{"field": "bahan", "from": "Cotton", "to": "Polyester"}, ...]
    
    # Impact assessment
    affects_production = db.Column(db.Boolean, default=False)
    production_impact = db.Column(db.Text)
    
    # Status
    status = db.Column(db.Enum(ChangeRequestStatus), default=ChangeRequestStatus.PENDING)
    
    # Requester
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Approver
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    approval_notes = db.Column(db.Text)
    
    # Implementation
    implemented_at = db.Column(db.DateTime)
    new_dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'))  # New DSO version after implementation
    
    requester = db.relationship('User', foreign_keys=[requested_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    new_dso = db.relationship('DSO', foreign_keys=[new_dso_id])
    
    @staticmethod
    def generate_request_code():
        """Generate unique request code."""
        today = datetime.now()
        prefix = f"CR-{today.strftime('%Y%m')}"
        last_cr = ChangeRequest.query.filter(
            ChangeRequest.request_code.like(f'{prefix}%')
        ).order_by(ChangeRequest.id.desc()).first()
        
        if last_cr:
            last_num = int(last_cr.request_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def approve(self, user_id, notes=None):
        """Approve the change request."""
        self.status = ChangeRequestStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = notes
    
    def reject(self, user_id, notes=None):
        """Reject the change request."""
        self.status = ChangeRequestStatus.REJECTED
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = notes
    
    def implement(self, new_dso_id):
        """Mark change request as implemented."""
        self.status = ChangeRequestStatus.IMPLEMENTED
        self.implemented_at = datetime.utcnow()
        self.new_dso_id = new_dso_id
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'dso_id': self.dso_id,
            'request_code': self.request_code,
            'reason': self.reason,
            'description': self.description,
            'priority': self.priority,
            'changes_json': self.changes_json,
            'affects_production': self.affects_production,
            'production_impact': self.production_impact,
            'status': self.status.value,
            'requested_by': self.requested_by,
            'requester_name': self.requester.full_name if self.requester else None,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'approved_by': self.approved_by,
            'approver_name': self.approver.full_name if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_notes': self.approval_notes,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None
        }
        
        if include_relations:
            data['dso'] = self.dso.to_dict() if self.dso else None
        
        return data
    
    def __repr__(self):
        return f'<ChangeRequest {self.request_code}>'
