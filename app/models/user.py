"""User model with role-based access control."""
from enum import Enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..extensions import db


class UserRole(Enum):
    """User roles for RBAC."""
    ADMIN = 'admin'
    OWNER = 'owner'
    ADMIN_PRODUKSI = 'admin_produksi'
    QC_LINE = 'qc_line'
    OPERATOR = 'operator'


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='operator')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('Employee', backref='user', uselist=False, lazy='joined')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, *roles):
        """Check if user has any of the specified roles."""
        return self.role in roles
    
    def can_access(self, permission):
        """Check if user can access a specific permission."""
        permissions = {
            'crud_order': [UserRole.ADMIN, UserRole.ADMIN_PRODUKSI],
            'read_order': [UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI, UserRole.QC_LINE],
            'approve_dso': [UserRole.ADMIN, UserRole.OWNER],
            'qc_inspect': [UserRole.ADMIN, UserRole.OWNER, UserRole.QC_LINE],
            'override_qc': [UserRole.ADMIN],
            'manage_users': [UserRole.ADMIN],
            'view_dashboard': [UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI],
            'view_reports': [UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI],
            'view_dso': [UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI, UserRole.QC_LINE, UserRole.OPERATOR],
            'edit_dso': [UserRole.ADMIN, UserRole.ADMIN_PRODUKSI],
        }
        allowed_roles = permissions.get(permission, [])
        return self.role in allowed_roles
    
    def to_dict(self):
        """Convert user to dictionary for API response."""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
