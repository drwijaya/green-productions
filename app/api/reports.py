"""Reports API endpoints."""
from datetime import datetime, timedelta
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.order import Order, OrderStatus
from ..models.qc import QCSheet, DefectLog, QCResult, DefectSeverity
from ..models.production import ProductionTask, ProcessType, TaskStatus
from ..models.dso import DSO
from ..models.audit import ActivityLog
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response


@api_bp.route('/reports/dashboard', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def get_dashboard_data():
    """Get dashboard analytics data."""
    # Orders summary
    total_orders = Order.query.count()
    active_orders = Order.query.filter(Order.status.in_([
        OrderStatus.IN_PRODUCTION, OrderStatus.QC_IN_PROGRESS
    ])).count()
    completed_orders = Order.query.filter_by(status=OrderStatus.COMPLETED).count()
    
    # QC summary
    total_inspections = QCSheet.query.count()
    passed = QCSheet.query.filter_by(result=QCResult.PASS).count()
    failed = QCSheet.query.filter_by(result=QCResult.FAIL).count()
    pass_rate = (passed / total_inspections * 100) if total_inspections > 0 else 0
    
    # Defects summary
    total_defects = DefectLog.query.count()
    critical_defects = DefectLog.query.filter_by(severity=DefectSeverity.CRITICAL).count()
    
    # Production tasks summary
    pending_tasks = ProductionTask.query.filter_by(status=TaskStatus.PENDING).count()
    in_progress = ProductionTask.query.filter_by(status=TaskStatus.IN_PROGRESS).count()
    
    return api_response(data={
        'orders': {
            'total': total_orders,
            'active': active_orders,
            'completed': completed_orders
        },
        'qc': {
            'total_inspections': total_inspections,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(pass_rate, 2)
        },
        'defects': {
            'total': total_defects,
            'critical': critical_defects
        },
        'production': {
            'pending_tasks': pending_tasks,
            'in_progress': in_progress
        }
    })


@api_bp.route('/reports/defects', methods=['GET'])
@login_required
def get_defect_report():
    """Get defect analysis report."""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    defects = DefectLog.query.filter(DefectLog.created_at >= start_date).all()
    
    # Group by type
    by_type = {}
    for d in defects:
        if d.defect_type not in by_type:
            by_type[d.defect_type] = 0
        by_type[d.defect_type] += d.qty_defect
    
    # Group by severity
    by_severity = {'minor': 0, 'major': 0, 'critical': 0}
    for d in defects:
        by_severity[d.severity.value] += d.qty_defect
    
    # Group by station
    by_station = {}
    for d in defects:
        station = d.station or 'Unknown'
        if station not in by_station:
            by_station[station] = 0
        by_station[station] += d.qty_defect
    
    return api_response(data={
        'period_days': days,
        'total_defects': sum(d.qty_defect for d in defects),
        'by_type': by_type,
        'by_severity': by_severity,
        'by_station': by_station
    })


@api_bp.route('/reports/production', methods=['GET'])
@login_required
def get_production_report():
    """Get production performance report."""
    # Get tasks completed in last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)
    
    tasks = ProductionTask.query.filter(
        ProductionTask.actual_end >= start_date,
        ProductionTask.status == 'completed'
    ).all()
    
    by_process = {}
    for process in ['cutting', 'sewing', 'finishing', 'packing']:
        process_tasks = [t for t in tasks if t.process == process]
        total_qty = sum(t.qty_completed for t in process_tasks)
        total_defect = sum(t.qty_defect for t in process_tasks)
        by_process[process] = {
            'tasks_completed': len(process_tasks),
            'qty_completed': total_qty,
            'qty_defect': total_defect,
            'defect_rate': round((total_defect / total_qty * 100) if total_qty > 0 else 0, 2)
        }
    
    return api_response(data={'by_process': by_process})


@api_bp.route('/reports/activity', methods=['GET'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
def get_activity_report():
    """Get activity log report."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    module = request.args.get('module')
    user_id = request.args.get('user_id', type=int)
    
    query = ActivityLog.query
    
    if module:
        query = query.filter(ActivityLog.module == module)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    query = query.order_by(ActivityLog.timestamp.desc())
    
    from ..utils.decorators import paginate_query
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'logs': [l.to_dict() for l in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/reports/invoice/<int:order_id>', methods=['GET'])
@login_required
def get_invoice_report(order_id):
    """Get comprehensive invoice report for an order."""
    order = Order.query.get_or_404(order_id)
    
    # Get DSO (approved version or latest)
    dso = order.dso.filter_by(status='approved').order_by(DSO.version.desc()).first()
    if not dso:
        dso = order.dso.order_by(DSO.version.desc()).first()
    
    # Get production tasks
    tasks = order.production_tasks.order_by(ProductionTask.sequence).all()
    tasks_data = []
    for t in tasks:
        tasks_data.append({
            'id': t.id,
            'process': t.process,
            'sequence': t.sequence,
            'planned_start': t.planned_start.isoformat() if t.planned_start else None,
            'planned_end': t.planned_end.isoformat() if t.planned_end else None,
            'actual_start': t.actual_start.isoformat() if t.actual_start else None,
            'actual_end': t.actual_end.isoformat() if t.actual_end else None,
            'status': t.status,
            'qty_target': t.qty_target,
            'qty_completed': t.qty_completed,
            'qty_defect': t.qty_defect,
            'operator_name': t.operator.name if t.operator else None
        })
    
    # Get QC sheets for this order
    qc_sheets = QCSheet.query.filter_by(order_id=order_id).order_by(QCSheet.inspected_at.desc()).all()
    qc_data = []
    total_inspected = 0
    total_passed = 0
    total_failed = 0
    for sheet in qc_sheets:
        qc_data.append({
            'id': sheet.id,
            'inspection_code': sheet.inspection_code,
            'production_task_id': sheet.production_task_id,
            'process': sheet.production_task.process if sheet.production_task else None,
            'result': sheet.result.value if sheet.result else 'pending',
            'qty_inspected': sheet.qty_inspected,
            'qty_passed': sheet.qty_passed,
            'qty_failed': sheet.qty_failed,
            'pass_rate': sheet.get_pass_rate() if hasattr(sheet, 'get_pass_rate') else 0,
            'inspected_at': sheet.inspected_at.isoformat() if sheet.inspected_at else None,
            'inspector_name': sheet.inspector.name if sheet.inspector else None,
            'notes': sheet.notes
        })
        total_inspected += sheet.qty_inspected or 0
        total_passed += sheet.qty_passed or 0
        total_failed += sheet.qty_failed or 0
    
    # Get defects for this order
    defects = DefectLog.query.filter_by(order_id=order_id).order_by(DefectLog.created_at.desc()).all()
    defects_data = []
    defect_summary = {'minor': 0, 'major': 0, 'critical': 0, 'total': 0}
    for d in defects:
        defects_data.append({
            'id': d.id,
            'qc_sheet_id': d.qc_sheet_id,
            'defect_type': d.defect_type,
            'severity': d.severity.value if d.severity else 'minor',
            'qty_defect': d.qty_defect,
            'description': d.description,
            'station': d.station,
            'photo_url': d.photo_url,
            'created_at': d.created_at.isoformat() if d.created_at else None
        })
        if d.severity:
            defect_summary[d.severity.value] += d.qty_defect
        defect_summary['total'] += d.qty_defect
    
    # Calculate overall QC pass rate
    overall_pass_rate = round((total_passed / total_inspected * 100), 2) if total_inspected > 0 else 0
    
    return api_response(data={
        'order': order.to_dict(include_relations=True),
        'dso': dso.to_dict(include_relations=True) if dso else None,
        'production_tasks': tasks_data,
        'qc_summary': {
            'total_inspected': total_inspected,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_pass_rate': overall_pass_rate,
            'sheets_count': len(qc_sheets)
        },
        'qc_sheets': qc_data,
        'defect_summary': defect_summary,
        'defects': defects_data,
        'generated_at': datetime.utcnow().isoformat()
    })


@api_bp.route('/reports/orders', methods=['GET'])
@login_required
def get_orders_for_reports():
    """Get list of orders for reports page."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Order.query
    
    if search:
        query = query.filter(
            (Order.order_code.ilike(f'%{search}%')) |
            (Order.model.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    
    from ..utils.decorators import paginate_query
    result = paginate_query(query, page, per_page)
    
    orders_data = []
    for o in result['items']:
        orders_data.append({
            'id': o.id,
            'order_code': o.order_code,
            'customer_name': o.customer.name if o.customer else None,
            'model': o.model,
            'qty_total': o.qty_total,
            'order_date': o.order_date.isoformat() if o.order_date else None,
            'deadline': o.deadline.isoformat() if o.deadline else None,
            'status': o.status,
            'production_progress': o.get_production_progress()
        })
    
    return api_response(data={
        'orders': orders_data,
        'pagination': result['pagination']
    })

