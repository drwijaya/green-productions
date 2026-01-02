"""QC API endpoints."""
from datetime import datetime
from flask import request, g
from flask_login import login_required, current_user
from . import api_bp
from ..models.qc import QCSheet, DefectLog, QCResult, DefectSeverity
from ..models.production import ProductionTask, TaskStatus
from ..models.order import Order, OrderStatus
from ..models.employee import Employee
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity
from ..services.storage_service import upload_file


@api_bp.route('/qc/my-tasks', methods=['GET'])
@login_required
def get_my_qc_tasks():
    """Get QC tasks for current user."""
    user = current_user
    
    # Get employee linked to user
    employee = Employee.query.filter_by(user_id=user.id).first()
    if not employee:
        return api_response(data={'tasks': []})
    
    # Get pending QC tasks
    tasks = ProductionTask.query.filter(
        ProductionTask.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.QC_PENDING])
    ).order_by(ProductionTask.created_at.desc()).all()
    
    return api_response(data={
        'tasks': [t.to_dict(include_relations=True) for t in tasks]
    })


@api_bp.route('/qc/sheets', methods=['GET'])
@login_required
def list_qc_sheets():
    """List QC reports with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    task_id = request.args.get('task_id', type=int)
    order_id = request.args.get('order_id', type=int)
    result = request.args.get('result')
    
    query = QCSheet.query
    
    if task_id:
        query = query.filter(QCSheet.production_task_id == task_id)
    if order_id:
        query = query.filter(QCSheet.order_id == order_id)
    if result:
        try:
            query = query.filter(QCSheet.result == QCResult(result))
        except ValueError:
            pass
    
    query = query.order_by(QCSheet.created_at.desc())
    res = paginate_query(query, page, per_page)
    
    return api_response(data={
        'sheets': [s.to_dict(include_relations=True) for s in res['items']],
        'pagination': res['pagination']
    })


@api_bp.route('/qc/sheets/<int:sheet_id>', methods=['GET'])
@login_required
def get_qc_sheet(sheet_id):
    """Get QC sheet by ID."""
    sheet = QCSheet.query.get_or_404(sheet_id)
    return api_response(data=sheet.to_dict(include_relations=True))


@api_bp.route('/qc/tasks/<int:task_id>/inspect', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.QC_LINE)
@log_activity('qc', 'inspect')
def create_inspection(task_id):
    """Create QC report for task (optional documentation, does not affect production)."""
    task = ProductionTask.query.get_or_404(task_id)
    data = request.get_json()
    
    # Get inspector employee
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    sheet = QCSheet(
        production_task_id=task_id,
        order_id=task.order_id,  # Also link to order for easier querying
        inspection_code=QCSheet.generate_inspection_code(),
        checklist_json=data.get('checklist'),
        result=QCResult(data.get('result', 'pending')),
        qty_inspected=data.get('qty_inspected', 0),
        qty_passed=data.get('qty_passed', 0),
        qty_failed=data.get('qty_failed', 0),
        notes=data.get('notes'),
        inspector_id=employee.id if employee else None,
        inspected_at=datetime.utcnow(),
        barcode_scanned=data.get('barcode_scanned', False)
    )
    
    db.session.add(sheet)
    db.session.commit()
    
    # Note: QC is now optional documentation only
    # Task status is NOT affected by QC result
    
    return api_response(data=sheet.to_dict(), message='QC Report created', status=201)


@api_bp.route('/qc/orders/<int:order_id>/report', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.QC_LINE)
@log_activity('qc', 'order_report')
def create_order_qc_report(order_id):
    """Create QC report for an order (optional quality documentation)."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    # Get inspector employee
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    sheet = QCSheet(
        order_id=order_id,
        production_task_id=data.get('production_task_id'),  # Optional link to specific task
        inspection_code=QCSheet.generate_inspection_code(),
        checklist_json=data.get('checklist'),
        result=QCResult(data.get('result', 'pending')),
        qty_inspected=data.get('qty_inspected', 0),
        qty_passed=data.get('qty_passed', 0),
        qty_failed=data.get('qty_failed', 0),
        notes=data.get('notes'),
        inspector_id=employee.id if employee else None,
        inspected_at=datetime.utcnow(),
        barcode_scanned=data.get('barcode_scanned', False)
    )
    
    db.session.add(sheet)
    db.session.commit()
    
    return api_response(data=sheet.to_dict(), message='QC Report created', status=201)


@api_bp.route('/qc/sheets/<int:sheet_id>/defect', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.QC_LINE)
def log_defect(sheet_id):
    """Log defect for QC sheet."""
    sheet = QCSheet.query.get_or_404(sheet_id)
    data = request.get_json()
    
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    defect = DefectLog(
        qc_sheet_id=sheet_id,
        defect_type=data.get('defect_type'),
        defect_category=data.get('defect_category'),
        severity=DefectSeverity(data.get('severity', 'minor')),
        qty_defect=data.get('qty_defect', 1),
        description=data.get('description'),
        station=data.get('station'),
        reported_by=employee.id if employee else None
    )
    
    db.session.add(defect)
    db.session.commit()
    
    return api_response(data=defect.to_dict(), message='Defect logged', status=201)


@api_bp.route('/qc/sheets/<int:sheet_id>/defect/<int:defect_id>/photo', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.QC_LINE)
def upload_defect_photo(sheet_id, defect_id):
    """Upload defect photo."""
    defect = DefectLog.query.filter_by(id=defect_id, qc_sheet_id=sheet_id).first_or_404()
    
    if 'file' not in request.files:
        return api_response(message='No file provided', status=400)
    
    file = request.files['file']
    result = upload_file(file, f'defects/{sheet_id}')
    
    if not result['success']:
        return api_response(message='Upload failed', status=500)
    
    defect.photo_url = result['url']
    db.session.commit()
    
    return api_response(data=defect.to_dict(), message='Photo uploaded')


@api_bp.route('/qc/defects', methods=['GET'])
@login_required
def list_defects():
    """List defects with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    severity = request.args.get('severity')
    
    query = DefectLog.query
    
    if severity:
        try:
            query = query.filter(DefectLog.severity == DefectSeverity(severity))
        except ValueError:
            pass
    
    query = query.order_by(DefectLog.created_at.desc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'defects': [d.to_dict() for d in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/qc/stats', methods=['GET'])
@login_required
def get_qc_stats():
    """Get QC statistics."""
    total = QCSheet.query.count()
    passed = QCSheet.query.filter_by(result=QCResult.PASS).count()
    failed = QCSheet.query.filter_by(result=QCResult.FAIL).count()
    
    defects_minor = DefectLog.query.filter_by(severity=DefectSeverity.MINOR).count()
    defects_major = DefectLog.query.filter_by(severity=DefectSeverity.MAJOR).count()
    defects_critical = DefectLog.query.filter_by(severity=DefectSeverity.CRITICAL).count()
    
    return api_response(data={
        'inspections': {'total': total, 'passed': passed, 'failed': failed},
        'defects': {'minor': defects_minor, 'major': defects_major, 'critical': defects_critical}
    })
