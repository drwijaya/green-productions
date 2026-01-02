"""Customers API endpoints."""
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.customer import Customer
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity


@api_bp.route('/customers', methods=['GET'])
@login_required
def list_customers():
    """List all customers with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = Customer.query
    
    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.company_name.ilike(f'%{search}%')) |
            (Customer.contact_person.ilike(f'%{search}%'))
        )
    
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    query = query.order_by(Customer.name.asc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'customers': [c.to_dict() for c in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """Get customer by ID."""
    customer = Customer.query.get_or_404(customer_id)
    
    data = customer.to_dict()
    data['recent_orders'] = [
        o.to_dict() for o in customer.orders.order_by(
            db.desc('created_at')
        ).limit(5).all()
    ]
    
    return api_response(data=data)


@api_bp.route('/customers', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('customers', 'create')
def create_customer():
    """Create new customer."""
    data = request.get_json()
    
    if not data.get('name'):
        return api_response(message='Customer name is required', status=400)
    
    customer = Customer(
        name=data['name'],
        company_name=data.get('company_name'),
        contact_person=data.get('contact_person'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        city=data.get('city'),
        notes=data.get('notes'),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return api_response(data=customer.to_dict(), message='Customer created successfully', status=201)


@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('customers', 'update')
def update_customer(customer_id):
    """Update customer."""
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json()
    
    if 'name' in data:
        customer.name = data['name']
    if 'company_name' in data:
        customer.company_name = data['company_name']
    if 'contact_person' in data:
        customer.contact_person = data['contact_person']
    if 'phone' in data:
        customer.phone = data['phone']
    if 'email' in data:
        customer.email = data['email']
    if 'address' in data:
        customer.address = data['address']
    if 'city' in data:
        customer.city = data['city']
    if 'notes' in data:
        customer.notes = data['notes']
    if 'is_active' in data:
        customer.is_active = data['is_active']
    
    db.session.commit()
    
    return api_response(data=customer.to_dict(), message='Customer updated successfully')


@api_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('customers', 'delete')
def delete_customer(customer_id):
    """Delete/deactivate customer."""
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if customer has orders
    if customer.orders.count() > 0:
        customer.is_active = False
        db.session.commit()
        return api_response(message='Customer deactivated (has existing orders)')
    
    db.session.delete(customer)
    db.session.commit()
    
    return api_response(message='Customer deleted successfully')


@api_bp.route('/customers/search', methods=['GET'])
@login_required
def search_customers():
    """Quick search for customers (for autocomplete)."""
    term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    customers = Customer.query.filter(
        Customer.is_active == True,
        (Customer.name.ilike(f'%{term}%')) |
        (Customer.company_name.ilike(f'%{term}%'))
    ).limit(limit).all()
    
    return api_response(data=[
        {'id': c.id, 'name': c.name, 'company_name': c.company_name}
        for c in customers
    ])
