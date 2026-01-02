"""Orders API endpoints."""
from datetime import datetime
from flask import request, g
from flask_login import login_required, current_user
from . import api_bp
from ..models.order import Order, OrderStatus
from ..models.dso import DSO, DSOStatus
from ..models.production import ProductionTask, ProcessType, TaskStatus
from ..models.qc import QCSheet
from ..models.barcode import Barcode, BarcodeType
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity


@api_bp.route('/orders', methods=['GET'])
@login_required
def list_orders():
    """List all orders with pagination and filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Order.query
    
    if search:
        query = query.filter(
            (Order.order_code.ilike(f'%{search}%')) |
            (Order.model.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.order_date >= date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Order.order_date <= date_to)
        except ValueError:
            pass
    
    query = query.order_by(Order.created_at.desc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'orders': [o.to_dict(include_relations=True) for o in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order by ID with full details."""
    order = Order.query.get_or_404(order_id)
    
    data = order.to_dict(include_relations=True)
    
    # Add DSO versions
    data['dso_versions'] = [
        dso.to_dict(include_relations=True) for dso in order.dso.order_by(DSO.version.desc()).all()
    ]
    
    # Add production tasks
    data['production_tasks'] = [
        task.to_dict(include_relations=True) for task in order.production_tasks.order_by(ProductionTask.sequence).all()
    ]
    
    # Add barcodes
    data['barcodes'] = [b.to_dict() for b in order.barcodes.all()]
    
    return api_response(data=data)


@api_bp.route('/orders', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('orders', 'create')
def create_order():
    """Create new order with auto-generated DSO and production tasks."""
    data = request.get_json()
    
    # Validate required fields
    required = ['customer_id', 'model', 'qty_total']
    for field in required:
        if not data.get(field):
            return api_response(message=f'{field} is required', status=400)
    
    # Parse deadline
    deadline = None
    if data.get('deadline'):
        try:
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
        except ValueError:
            return api_response(message='Invalid deadline format', status=400)
    
    # Create order
    order = Order(
        order_code=Order.generate_order_code(),
        customer_id=data['customer_id'],
        model=data['model'],
        description=data.get('description'),
        qty_total=data['qty_total'],
        deadline=deadline,
        priority=data.get('priority', 1),
        customer_notes=data.get('customer_notes'),
        internal_notes=data.get('internal_notes'),
        status='draft',
        created_by=current_user.id
    )
    
    db.session.add(order)
    db.session.flush()  # Get order ID
    
    # Auto-create DSO version 1
    dso = DSO(
        order_id=order.id,
        version=1,
        status='draft',
        created_by=current_user.id
    )
    db.session.add(dso)
    
    # Auto-create production tasks for each process (5 processes including Sablon)
    processes = ['cutting', 'sewing', 'sablon', 'finishing', 'packing']
    created_tasks = []
    for idx, process in enumerate(processes):
        task = ProductionTask(
            order_id=order.id,
            process=process,
            status='pending',
            qty_target=order.qty_total,
            sequence=idx + 1
        )
        db.session.add(task)
        db.session.flush()  # Get task ID
        created_tasks.append(task)
    
    # Auto-create QC sheets for each production task
    for task in created_tasks:
        qc_sheet = QCSheet(
            order_id=order.id,
            production_task_id=task.id,
            inspection_code=QCSheet.generate_inspection_code(),
            result=None  # Will be set when inspection is done
        )
        db.session.add(qc_sheet)
        db.session.flush()  # Ensure unique inspection_code for next iteration
    
    # Auto-create order barcode
    barcode = Barcode(
        order_id=order.id,
        barcode_value=Barcode.generate_barcode_value(BarcodeType.ORDER, order.id),
        barcode_type=BarcodeType.ORDER,
        reference_id=order.id,
        reference_type='order'
    )
    db.session.add(barcode)
    
    db.session.commit()
    
    # Set activity log context
    g.record_id = order.id
    g.record_type = 'order'
    g.log_description = f'Created order {order.order_code}'
    
    return api_response(
        data=order.to_dict(include_relations=True),
        message='Order created successfully',
        status=201
    )


@api_bp.route('/orders/<int:order_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.ADMIN_PRODUKSI)
@log_activity('orders', 'update')
def update_order(order_id):
    """Update order."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    # Store before state for audit
    g.data_before = order.to_dict()
    
    if 'customer_id' in data:
        order.customer_id = data['customer_id']
    if 'model' in data:
        order.model = data['model']
    if 'description' in data:
        order.description = data['description']
    if 'qty_total' in data:
        order.qty_total = data['qty_total']
    if 'deadline' in data:
        try:
            order.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d') if data['deadline'] else None
        except ValueError:
            pass
    if 'priority' in data:
        order.priority = data['priority']
    if 'customer_notes' in data:
        order.customer_notes = data['customer_notes']
    if 'internal_notes' in data:
        order.internal_notes = data['internal_notes']
    if 'status' in data:
        order.status = data['status']
    
    db.session.commit()
    
    # Set activity log context
    g.record_id = order.id
    g.record_type = 'order'
    g.data_after = order.to_dict()
    
    return api_response(data=order.to_dict(include_relations=True), message='Order updated successfully')


@api_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('orders', 'delete')
def delete_order(order_id):
    """Delete order permanently from database."""
    order = Order.query.get_or_404(order_id)
    
    # Delete related DSO records
    for dso in order.dso.all():
        dso.images.delete()
        dso.accessories.delete()
        dso.sizes.delete()
        db.session.delete(dso)
    
    # Delete related QC sheets
    for qc_sheet in order.qc_reports.all():
        qc_sheet.defects.delete()
        db.session.delete(qc_sheet)
    
    # Delete production tasks and their worker logs
    for task in order.production_tasks.all():
        task.worker_logs.delete()
        db.session.delete(task)
    
    # Delete barcodes
    order.barcodes.delete()
    
    # Delete the order
    db.session.delete(order)
    db.session.commit()
    
    return api_response(message='Order deleted successfully')


@api_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.ADMIN_PRODUKSI)
@log_activity('orders', 'status_change')
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    new_status = data.get('status')
    if not new_status:
        return api_response(message='Status is required', status=400)
    
    order.status = new_status
    
    db.session.commit()
    
    return api_response(data=order.to_dict(), message='Order status updated')


@api_bp.route('/orders/statuses', methods=['GET'])
@login_required
def get_order_statuses():
    """Get available order statuses."""
    statuses = [
        {'value': 'draft', 'label': 'Draft'},
        {'value': 'in_production', 'label': 'In Production'},
        {'value': 'qc_pending', 'label': 'QC Pending'},
        {'value': 'completed', 'label': 'Completed'},
        {'value': 'cancelled', 'label': 'Cancelled'}
    ]
    return api_response(data=statuses)
