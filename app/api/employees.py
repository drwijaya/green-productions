"""Employees API endpoints."""
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.employee import Employee
from ..models.user import User, UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query
from datetime import datetime


@api_bp.route('/employees', methods=['GET'])
@login_required
def list_employees():
    """List all employees."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    search = request.args.get('search', '')
    
    query = Employee.query.filter(Employee.is_active == True)
    
    if search:
        query = query.filter(
            (Employee.name.ilike(f'%{search}%')) |
            (Employee.employee_code.ilike(f'%{search}%'))
        )
    
    query = query.order_by(Employee.name.asc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'employees': [e.to_dict() for e in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    """Get employee by ID with user info."""
    employee = Employee.query.get_or_404(employee_id)
    data = employee.to_dict()
    
    # Add user info if exists
    if employee.user:
        data['username'] = employee.user.username
        data['role'] = employee.user.role
    
    return api_response(data=data)


@api_bp.route('/employees', methods=['POST'])
@login_required
def create_employee():
    """Create a new employee with optional login account."""
    data = request.get_json()
    
    if not data.get('name'):
        return api_response(success=False, message='Nama wajib diisi', status_code=400)
    
    if not data.get('position'):
        return api_response(success=False, message='Posisi/stasiun kerja wajib diisi', status_code=400)
    
    # Validate position value
    valid_positions = ['owner', 'admin', 'qc_line', 'sewing', 'sablon', 'cutting', 'finishing', 'packing']
    if data['position'] not in valid_positions:
        return api_response(success=False, message='Posisi tidak valid', status_code=400)
    
    # Generate employee code
    last_emp = Employee.query.order_by(Employee.id.desc()).first()
    next_num = (last_emp.id + 1) if last_emp else 1
    employee_code = f'EMP{next_num:05d}'
    
    # Check if employee code already exists, if so increment
    while Employee.query.filter_by(employee_code=employee_code).first():
        next_num += 1
        employee_code = f'EMP{next_num:05d}'
    
    user = None
    create_login = data.get('create_login', False)
    
    if create_login:
        username = data.get('username', '').strip().lower()
        password = data.get('password', 'password123')
        role = data.get('role', 'operator')
        
        if not username:
            return api_response(success=False, message='Username wajib diisi untuk membuat akun', status_code=400)
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return api_response(success=False, message=f'Username "{username}" sudah digunakan', status_code=400)
        
        # Check if email already exists (if provided)
        email = data.get('email', '').strip()
        if email and User.query.filter_by(email=email).first():
            return api_response(success=False, message=f'Email "{email}" sudah digunakan', status_code=400)
        
        # Create user account
        user = User(
            email=email or f'{username}@greenproduction.local',
            username=username,
            full_name=data['name'],
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user ID
    
    # Parse join_date
    join_date = None
    if data.get('join_date'):
        try:
            join_date = datetime.strptime(data['join_date'], '%Y-%m-%d').date()
        except:
            pass
    
    # Auto-set department based on position
    position = data.get('position')
    department_map = {
        'owner': 'Management',
        'admin': 'Office',
        'qc_line': 'QC',
        'sewing': 'Production',
        'sablon': 'Production',
        'cutting': 'Production',
        'finishing': 'Production',
        'packing': 'Warehouse'
    }
    department = department_map.get(position, 'Production')
    
    # Validate employment type
    employment_type = data.get('employment_type', 'karyawan')
    valid_employment_types = ['karyawan', 'harian_lepas', 'borongan', 'magang']
    if employment_type not in valid_employment_types:
        employment_type = 'karyawan'
    
    # Create employee
    employee = Employee(
        user_id=user.id if user else None,
        employee_code=employee_code,
        name=data['name'],
        department=department,
        position=position,
        employment_type=employment_type,
        phone=data.get('phone'),
        email=data.get('email'),
        join_date=join_date,
        is_active=True
    )
    
    db.session.add(employee)
    
    try:
        db.session.commit()
        result = employee.to_dict()
        if user:
            result['login_created'] = True
            result['username'] = user.username
        return api_response(data=result, message='Employee berhasil ditambahkan')
    except Exception as e:
        db.session.rollback()
        return api_response(success=False, message=f'Gagal menyimpan: {str(e)}', status_code=500)


@api_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    """Update an existing employee."""
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()
    
    if not data.get('name'):
        return api_response(success=False, message='Nama wajib diisi', status_code=400)
    
    # Update employee fields
    employee.name = data['name']
    employee.position = data.get('position')
    employee.phone = data.get('phone')
    employee.email = data.get('email')
    
    # Auto-set department based on position
    if data.get('position'):
        department_map = {
            'owner': 'Management',
            'admin': 'Office',
            'qc_line': 'QC',
            'sewing': 'Production',
            'sablon': 'Production',
            'cutting': 'Production',
            'finishing': 'Production',
            'packing': 'Warehouse'
        }
        employee.department = department_map.get(data['position'], 'Production')
    
    # Update employment type
    if data.get('employment_type'):
        valid_employment_types = ['karyawan', 'harian_lepas', 'borongan', 'magang']
        if data['employment_type'] in valid_employment_types:
            employee.employment_type = data['employment_type']
    
    if data.get('join_date'):
        try:
            employee.join_date = datetime.strptime(data['join_date'], '%Y-%m-%d').date()
        except:
            pass
    
    create_login = data.get('create_login', False)
    
    # Handle login account
    if create_login and not employee.user_id:
        # Create new user account
        username = data.get('username', '').strip().lower()
        password = data.get('password', 'password123')
        role = data.get('role', 'operator')
        
        if not username:
            return api_response(success=False, message='Username wajib diisi untuk membuat akun', status_code=400)
        
        if User.query.filter_by(username=username).first():
            return api_response(success=False, message=f'Username "{username}" sudah digunakan', status_code=400)
        
        email = data.get('email', '').strip()
        if email and User.query.filter_by(email=email).first():
            existing_user = User.query.filter_by(email=email).first()
            if existing_user.id != employee.user_id:
                return api_response(success=False, message=f'Email "{email}" sudah digunakan', status_code=400)
        
        user = User(
            email=email or f'{username}@greenproduction.local',
            username=username,
            full_name=data['name'],
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        employee.user_id = user.id
        
    elif employee.user:
        # Update existing user
        if data.get('role'):
            employee.user.role = data['role']
        employee.user.full_name = data['name']
        if data.get('password'):
            employee.user.set_password(data['password'])
    
    try:
        db.session.commit()
        return api_response(data=employee.to_dict(), message='Employee berhasil diupdate')
    except Exception as e:
        db.session.rollback()
        return api_response(success=False, message=f'Gagal menyimpan: {str(e)}', status_code=500)


@api_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    """Soft delete an employee (set inactive)."""
    employee = Employee.query.get_or_404(employee_id)
    
    employee.is_active = False
    if employee.user:
        employee.user.is_active = False
    
    try:
        db.session.commit()
        return api_response(message='Employee berhasil dihapus')
    except Exception as e:
        db.session.rollback()
        return api_response(success=False, message=f'Gagal menghapus: {str(e)}', status_code=500)


@api_bp.route('/employees/departments', methods=['GET'])
@login_required
def get_departments():
    """Get list of available departments."""
    departments = [
        {'value': 'Production', 'label': 'Production'},
        {'value': 'QC', 'label': 'QC (Quality Control)'},
        {'value': 'Warehouse', 'label': 'Warehouse'},
        {'value': 'Design', 'label': 'Design'},
        {'value': 'Marketing', 'label': 'Marketing'},
        {'value': 'Finance', 'label': 'Finance'},
        {'value': 'HR', 'label': 'HR (Human Resources)'},
        {'value': 'IT', 'label': 'IT'},
        {'value': 'Office', 'label': 'Office / Admin'},
    ]
    return api_response(data=departments)


@api_bp.route('/employees/positions', methods=['GET'])
@login_required
def get_positions():
    """Get list of available positions/work stations."""
    positions = [
        {'value': 'owner', 'label': 'Owner', 'icon': 'fa-crown'},
        {'value': 'admin', 'label': 'Admin', 'icon': 'fa-user-shield'},
        {'value': 'qc_line', 'label': 'QC Line', 'icon': 'fa-clipboard-check'},
        {'value': 'sewing', 'label': 'Sewing', 'icon': 'fa-tshirt'},
        {'value': 'sablon', 'label': 'Sablon', 'icon': 'fa-paint-brush'},
        {'value': 'cutting', 'label': 'Cutting', 'icon': 'fa-cut'},
        {'value': 'finishing', 'label': 'Finishing', 'icon': 'fa-magic'},
        {'value': 'packing', 'label': 'Packing', 'icon': 'fa-box'},
    ]
    return api_response(data=positions)

