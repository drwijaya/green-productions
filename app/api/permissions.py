"""Permissions API endpoints."""
from flask import request
from flask_login import login_required
from . import api_bp
from ..models.user import User, UserRole
from ..models.permission import UserPermission, AVAILABLE_PERMISSIONS
from ..extensions import db
from ..utils.decorators import require_roles, api_response, log_activity


@api_bp.route('/permissions/available', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN)
def get_available_permissions():
    """Get list of all available permissions."""
    return api_response(data=AVAILABLE_PERMISSIONS)


@api_bp.route('/permissions/user/<int:user_id>', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN)
def get_user_permissions(user_id):
    """Get permissions for a specific user."""
    user = User.query.get_or_404(user_id)
    
    # Get all permissions for this user
    perms = UserPermission.query.filter_by(user_id=user_id).all()
    permissions = {p.permission_key: p.to_dict() for p in perms}
    
    return api_response(data={
        'user_id': user_id,
        'username': user.username,
        'role': user.role,
        'permissions': permissions,
        'available': AVAILABLE_PERMISSIONS
    })


@api_bp.route('/permissions/user/<int:user_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('permissions', 'update')
def update_user_permissions(user_id):
    """Update permissions for a user."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # data format: { "permissions": { "dashboard": {"can_view": true, "can_edit": false, ...}, ... } }
    permissions = data.get('permissions', {})
    
    for key, perm_data in permissions.items():
        if key not in AVAILABLE_PERMISSIONS:
            continue
        
        UserPermission.set_user_permission(
            user_id=user_id,
            permission_key=key,
            can_view=perm_data.get('can_view', False),
            can_create=perm_data.get('can_create', False),
            can_edit=perm_data.get('can_edit', False),
            can_delete=perm_data.get('can_delete', False)
        )
    
    # Remove permissions that are not in the update
    existing_keys = [p.permission_key for p in UserPermission.query.filter_by(user_id=user_id).all()]
    for key in existing_keys:
        if key not in permissions:
            UserPermission.query.filter_by(user_id=user_id, permission_key=key).delete()
    
    db.session.commit()
    
    return api_response(message='Permissions updated successfully')


@api_bp.route('/permissions/user/<int:user_id>/reset', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('permissions', 'reset')
def reset_user_permissions(user_id):
    """Reset user permissions to role defaults."""
    user = User.query.get_or_404(user_id)
    
    # Delete existing permissions
    UserPermission.query.filter_by(user_id=user_id).delete()
    
    # Create default permissions based on role
    UserPermission.create_default_permissions(user_id, user.role)
    
    db.session.commit()
    
    return api_response(message='Permissions reset to role defaults')


@api_bp.route('/permissions/user/<int:user_id>/quick', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('permissions', 'quick_set')
def quick_set_permission(user_id):
    """Quickly toggle a single permission."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    key = data.get('permission_key')
    can_view = data.get('can_view', True)
    
    if key not in AVAILABLE_PERMISSIONS:
        return api_response(message='Invalid permission key', status=400)
    
    if can_view:
        UserPermission.set_user_permission(user_id, key, can_view=True)
    else:
        UserPermission.query.filter_by(user_id=user_id, permission_key=key).delete()
    
    db.session.commit()
    
    return api_response(message=f'Permission {key} updated')
