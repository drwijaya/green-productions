"""User Permission model for granular access control."""
from datetime import datetime
from ..extensions import db


# Available menu/feature permissions
AVAILABLE_PERMISSIONS = {
    'dashboard': {
        'label': 'Dashboard',
        'icon': 'fa-chart-pie',
        'description': 'Akses halaman dashboard dan statistik'
    },
    'invoices': {
        'label': 'Invoices',
        'icon': 'fa-file-invoice',
        'description': 'Mengelola invoice/orders'
    },
    'dso_management': {
        'label': 'DSO Management',
        'icon': 'fa-drafting-compass',
        'description': 'Mengelola Design Specification Orders'
    },
    'production': {
        'label': 'Production Monitoring',
        'icon': 'fa-industry',
        'description': 'Memonitor proses produksi'
    },
    'qc': {
        'label': 'QC Monitoring',
        'icon': 'fa-check-circle',
        'description': 'Quality Control dan inspeksi'
    },
    'customers': {
        'label': 'Customers',
        'icon': 'fa-users',
        'description': 'Mengelola data customer'
    },
    'employees': {
        'label': 'Employees',
        'icon': 'fa-id-badge',
        'description': 'Mengelola data karyawan'
    },
    'sop': {
        'label': 'SOP Documents',
        'icon': 'fa-book',
        'description': 'Dokumen Standard Operating Procedure'
    },
    'reports': {
        'label': 'Reports',
        'icon': 'fa-chart-bar',
        'description': 'Akses laporan dan export'
    },
    'user_management': {
        'label': 'User Management',
        'icon': 'fa-user-cog',
        'description': 'Mengelola user dan hak akses (Admin only)'
    }
}


class UserPermission(db.Model):
    """Store individual menu/feature permissions per user."""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permission_key = db.Column(db.String(50), nullable=False)  # e.g., 'dashboard', 'invoices', etc
    can_view = db.Column(db.Boolean, default=True)
    can_create = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint - one permission per user per key
    __table_args__ = (
        db.UniqueConstraint('user_id', 'permission_key', name='unique_user_permission'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'permission_key': self.permission_key,
            'can_view': self.can_view,
            'can_create': self.can_create,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete
        }
    
    @staticmethod
    def get_user_permissions(user_id):
        """Get all permissions for a user as a dict."""
        perms = UserPermission.query.filter_by(user_id=user_id).all()
        return {p.permission_key: p.to_dict() for p in perms}
    
    @staticmethod
    def set_user_permission(user_id, permission_key, can_view=True, can_create=False, can_edit=False, can_delete=False):
        """Set or update a permission for a user."""
        perm = UserPermission.query.filter_by(user_id=user_id, permission_key=permission_key).first()
        if perm:
            perm.can_view = can_view
            perm.can_create = can_create
            perm.can_edit = can_edit
            perm.can_delete = can_delete
        else:
            perm = UserPermission(
                user_id=user_id,
                permission_key=permission_key,
                can_view=can_view,
                can_create=can_create,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.session.add(perm)
        return perm
    
    @staticmethod
    def create_default_permissions(user_id, role):
        """Create default permissions based on user role."""
        # Define default permissions by role
        role_defaults = {
            'admin': list(AVAILABLE_PERMISSIONS.keys()),  # All permissions
            'owner': ['dashboard', 'invoices', 'dso_management', 'production', 'qc', 'customers', 'employees', 'reports'],
            'admin_produksi': ['dashboard', 'invoices', 'dso_management', 'production', 'qc', 'customers', 'employees'],
            'qc_line': ['dashboard', 'production', 'qc'],
            'operator': ['dashboard', 'production']
        }
        
        allowed = role_defaults.get(role, ['dashboard'])
        
        for key in AVAILABLE_PERMISSIONS.keys():
            if key in allowed:
                UserPermission.set_user_permission(
                    user_id, key,
                    can_view=True,
                    can_create=(role in ['admin', 'owner', 'admin_produksi']),
                    can_edit=(role in ['admin', 'owner', 'admin_produksi']),
                    can_delete=(role in ['admin'])
                )
