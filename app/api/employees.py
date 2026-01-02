"""Employees API endpoints."""
from flask import request
from flask_login import login_required
from . import api_bp
from ..models.employee import Employee
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query


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
    """Get employee by ID."""
    employee = Employee.query.get_or_404(employee_id)
    return api_response(data=employee.to_dict())
