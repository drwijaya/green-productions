"""Users API endpoints."""
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.user import User, UserRole
from ..models.employee import Employee
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity


@api_bp.route('/users', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN)
def list_users():
    """List all users with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    
    if role:
        # Role is now stored as string, filter directly
        valid_roles = ['admin', 'owner', 'admin_produksi', 'qc_line', 'operator']
        if role in valid_roles:
            query = query.filter(User.role == role)
    
    query = query.order_by(User.created_at.desc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'users': [u.to_dict() for u in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN)
def get_user(user_id):
    """Get user by ID."""
    user = User.query.get_or_404(user_id)
    
    data = user.to_dict()
    if user.employee:
        data['employee'] = user.employee.to_dict()
    
    return api_response(data=data)


@api_bp.route('/users', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('users', 'create')
def create_user():
    """Create new user."""
    data = request.get_json()
    
    # Validate required fields
    required = ['email', 'username', 'password', 'full_name', 'role']
    for field in required:
        if not data.get(field):
            return api_response(message=f'{field} is required', status=400)
    
    # Check if email/username exists
    if User.query.filter_by(email=data['email']).first():
        return api_response(message='Email already exists', status=400)
    
    if User.query.filter_by(username=data['username']).first():
        return api_response(message='Username already exists', status=400)
    
    # Validate role - now using string
    valid_roles = ['admin', 'owner', 'admin_produksi', 'qc_line', 'operator']
    if data['role'] not in valid_roles:
        return api_response(message='Invalid role', status=400)
    
    # Create user
    user = User(
        email=data['email'],
        username=data['username'],
        full_name=data['full_name'],
        role=data['role'],  # Store as string directly
        is_active=data.get('is_active', True)
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create associated employee if needed
    if data.get('create_employee', False):
        from ..models.employee import Employee
        employee = Employee(
            user_id=user.id,
            employee_code=f"EMP{user.id:05d}",
            name=user.full_name,
            department=data.get('department', ''),
            position=data.get('position', ''),
            email=user.email
        )
        db.session.add(employee)
        db.session.commit()
    
    return api_response(data=user.to_dict(), message='User created successfully', status=201)


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('users', 'update')
def update_user(user_id):
    """Update user."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Update fields
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return api_response(message='Email already exists', status=400)
        user.email = data['email']
    
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return api_response(message='Username already exists', status=400)
        user.username = data['username']
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'role' in data:
        valid_roles = ['admin', 'owner', 'admin_produksi', 'qc_line', 'operator']
        if data['role'] not in valid_roles:
            return api_response(message='Invalid role', status=400)
        user.role = data['role']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    db.session.commit()
    
    return api_response(data=user.to_dict(), message='User updated successfully')


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN)
@log_activity('users', 'delete')
def delete_user(user_id):
    """Delete/deactivate user."""
    user = User.query.get_or_404(user_id)
    
    # Soft delete - just deactivate
    user.is_active = False
    db.session.commit()
    
    return api_response(message='User deactivated successfully')


@api_bp.route('/users/roles', methods=['GET'])
@login_required
def get_roles():
    """Get available user roles."""
    roles = [{'value': r.value, 'label': r.value.replace('_', ' ').title()} for r in UserRole]
    return api_response(data=roles)
