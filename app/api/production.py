"""Production API endpoints."""
from datetime import datetime
from flask import request, g, jsonify
from flask_login import login_required, current_user
from . import api_bp
from ..models.production import ProductionTask, ProcessType, TaskStatus, ProductionWorkerLog
from ..models.order import Order, OrderStatus
from ..models.employee import Employee
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity


@api_bp.route('/production/tasks', methods=['GET'])
@login_required
def list_production_tasks():
    """List production tasks with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    order_id = request.args.get('order_id', type=int)
    process = request.args.get('process')
    status = request.args.get('status')
    
    query = ProductionTask.query
    
    if order_id:
        query = query.filter(ProductionTask.order_id == order_id)
    if process:
        try:
            query = query.filter(ProductionTask.process == ProcessType(process))
        except ValueError:
            pass
    if status:
        try:
            query = query.filter(ProductionTask.status == TaskStatus(status))
        except ValueError:
            pass
    
    query = query.order_by(ProductionTask.order_id, ProductionTask.sequence)
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'tasks': [t.to_dict(include_relations=True) for t in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/production/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_production_task(task_id):
    """Get production task by ID."""
    task = ProductionTask.query.get_or_404(task_id)
    data = task.to_dict(include_relations=True)
    data['qc_sheets'] = [qc.to_dict() for qc in task.qc_sheets.all()]
    return api_response(data=data)


@api_bp.route('/production/tasks/<int:task_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def update_production_task(task_id):
    """Update production task."""
    task = ProductionTask.query.get_or_404(task_id)
    data = request.get_json()
    
    if 'line_supervisor_id' in data:
        task.line_supervisor_id = data['line_supervisor_id']
    if 'planned_start' in data and data['planned_start']:
        task.planned_start = datetime.fromisoformat(data['planned_start'])
    if 'planned_end' in data and data['planned_end']:
        task.planned_end = datetime.fromisoformat(data['planned_end'])
    if 'qty_target' in data:
        task.qty_target = data['qty_target']
    if 'notes' in data:
        task.notes = data['notes']
    
    db.session.commit()
    return api_response(data=task.to_dict(include_relations=True), message='Task updated')


@api_bp.route('/production/tasks/<int:task_id>/start', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI, UserRole.QC_LINE)
def start_production_task(task_id):
    """Start production task - can only start if workers are assigned."""
    task = ProductionTask.query.get_or_404(task_id)
    
    # Can start from pending or assigned status
    if task.status not in ['pending', 'assigned']:
        return api_response(message='Task already started or completed', status=400)
    
    # Check if workers are assigned
    if task.worker_logs.count() == 0:
        return api_response(message='Assign workers before starting task', status=400)
    
    task.start_task()
    order = task.order
    if order.status == 'draft':
        order.status = 'in_production'
    
    db.session.commit()
    return api_response(data=task.to_dict(include_relations=True), message='Task started')


@api_bp.route('/production/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def complete_production_task(task_id):
    """Complete production task."""
    task = ProductionTask.query.get_or_404(task_id)
    data = request.get_json()
    
    task.qty_completed = data.get('qty_completed', task.qty_target)
    task.qty_defect = data.get('qty_defect', 0)
    task.complete_task()
    
    order = task.order
    all_tasks = order.production_tasks.all()
    if all(t.status == 'completed' for t in all_tasks):
        order.status = 'completed'  # QC is now optional reporting, production completes directly
    
    db.session.commit()
    return api_response(data=task.to_dict(), message='Task completed')


@api_bp.route('/production/timeline', methods=['GET'])
@login_required
def get_production_timeline():
    """Get production timeline for Gantt chart."""
    order_id = request.args.get('order_id', type=int)
    query = ProductionTask.query.join(Order)
    
    if order_id:
        query = query.filter(ProductionTask.order_id == order_id)
    
    tasks = query.order_by(Order.id, ProductionTask.sequence).all()
    
    timeline_data = [{
        'id': t.id,
        'order_code': t.order.order_code,
        'process': t.process.value,
        'status': t.status.value,
        'progress': t.get_progress_percentage(),
        'planned_start': t.planned_start.isoformat() if t.planned_start else None,
        'planned_end': t.planned_end.isoformat() if t.planned_end else None,
        'actual_start': t.actual_start.isoformat() if t.actual_start else None,
        'actual_end': t.actual_end.isoformat() if t.actual_end else None
    } for t in tasks]
    
    return api_response(data=timeline_data)


# Worker Log Endpoints
@api_bp.route('/production/tasks/<int:task_id>/workers', methods=['GET'])
@login_required
def get_task_workers(task_id):
    """Get all worker logs for a task."""
    task = ProductionTask.query.get_or_404(task_id)
    return api_response(data=[log.to_dict() for log in task.worker_logs.all()])


@api_bp.route('/production/tasks/<int:task_id>/workers', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def add_worker_log(task_id):
    """Assign worker to task. Sets task status to 'assigned' if pending."""
    task = ProductionTask.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data.get('employee_id'):
        return api_response(message='employee_id is required', status=400)
    
    # Check if worker already assigned
    existing = ProductionWorkerLog.query.filter_by(
        task_id=task_id, 
        employee_id=data['employee_id']
    ).first()
    if existing:
        return api_response(message='Worker already assigned to this task', status=400)
    
    worker_log = ProductionWorkerLog(
        task_id=task_id,
        employee_id=data['employee_id'],
        qty_completed=0,  # Start with 0, will be updated via progress
        qty_defect=0,
        notes=data.get('notes')
    )
    db.session.add(worker_log)
    
    # Change status to assigned if still pending
    if task.status == 'pending':
        task.status = 'assigned'
    
    db.session.commit()
    
    return api_response(data=worker_log.to_dict(), message='Worker assigned', status=201)


@api_bp.route('/production/workers/<int:log_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def update_worker_log(log_id):
    """Update a worker's qty completed."""
    worker_log = ProductionWorkerLog.query.get_or_404(log_id)
    data = request.get_json()
    
    if 'qty_completed' in data:
        worker_log.qty_completed = data['qty_completed']
    if 'qty_defect' in data:
        worker_log.qty_defect = data['qty_defect']
    if 'notes' in data:
        worker_log.notes = data['notes']
    if data.get('completed'):
        worker_log.completed_at = datetime.utcnow()
    
    # Update task total
    task = worker_log.task
    task.update_qty_from_workers()
    db.session.commit()
    
    # Return updated progress info for real-time UI updates
    response_data = worker_log.to_dict()
    response_data['task_progress'] = task.get_progress_percentage()
    response_data['qty_completed'] = task.qty_completed
    response_data['qty_target'] = task.qty_target
    
    return api_response(data=response_data, message='Worker log updated')


@api_bp.route('/production/workers/<int:log_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def delete_worker_log(log_id):
    """Delete a worker log."""
    worker_log = ProductionWorkerLog.query.get_or_404(log_id)
    task = worker_log.task
    
    db.session.delete(worker_log)
    task.update_qty_from_workers()
    db.session.commit()
    
    return api_response(message='Worker log deleted')


@api_bp.route('/production/tasks/<int:task_id>/supervisor', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def assign_supervisor(task_id):
    """Assign line supervisor to a task."""
    task = ProductionTask.query.get_or_404(task_id)
    data = request.get_json()
    
    task.line_supervisor_id = data.get('employee_id')
    db.session.commit()
    
    return api_response(data=task.to_dict(), message='Supervisor assigned')


@api_bp.route('/production/search-tasks', methods=['GET'])
@login_required
def search_production_tasks():
    """Search tasks for Select2 dropdowns."""
    search = request.args.get('term') # Select2 sends 'term'
    query = ProductionTask.query.join(Order).filter(
        ProductionTask.status != 'completed'
    )
    
    if search:
        query = query.filter(
            db.or_(
                Order.order_code.ilike(f'%{search}%'),
                Order.model.ilike(f'%{search}%')
            )
        )
    
    tasks = query.order_by(Order.order_code.desc()).limit(20).all()
    
    results = []
    for t in tasks:
        results.append({
            'id': t.id,
            'text': f"[{t.order.order_code}] {t.order.model} - {t.process.title()}",
            # Additional info for auto-fill
            'customer_name': t.order.customer.name if t.order.customer else 'Unknown',
            'order_code': t.order.order_code,
            'product_name': t.order.model,
            'process_stage': t.process.title()
        })
        
    return jsonify({'results': results})


