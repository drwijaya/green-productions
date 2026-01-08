from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract, case
from datetime import datetime, timedelta
from . import api_bp
from ..extensions import db
from ..models import QCSheet, DefectLog, DefectSeverity, DefectStatus, ProductionTask, Order, QCResult, Employee


@api_bp.route('/qc/dashboard/stats', methods=['GET'])
@login_required
def get_monitoring_stats():
    """Get KPI statistics for QC Dashboard from real QC data."""
    period = request.args.get('period', 'month')
    
    now = datetime.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    # Total Defects from DefectLog
    total_defects = db.session.query(func.sum(DefectLog.qty_defect)).filter(
        DefectLog.created_at >= start_date
    ).scalar() or 0
    
    # Open defects (using string comparison)
    open_defects = DefectLog.query.filter(
        DefectLog.status.in_(['open', 'in_progress']),
        DefectLog.created_at >= start_date
    ).count()
    
    # Resolved defects (using string comparison)
    resolved_defects = DefectLog.query.filter(
        DefectLog.status.in_(['resolved', 'closed']),
        DefectLog.created_at >= start_date
    ).count()
    
    # Pass Rate from QCSheet (using string comparison for result)
    total_qc = QCSheet.query.filter(QCSheet.created_at >= start_date).count()
    passed_qc = QCSheet.query.filter(
        QCSheet.result.in_([QCResult.PASS, QCResult.CONDITIONAL_PASS]),
        QCSheet.created_at >= start_date
    ).count()
    
    # Also aggregate from checklist_json for more accurate stats
    qc_sheets = QCSheet.query.filter(QCSheet.created_at >= start_date).all()
    total_inspected = sum(s.qty_inspected or 0 for s in qc_sheets)
    total_passed = sum(s.qty_passed or 0 for s in qc_sheets)
    total_failed = sum(s.qty_failed or 0 for s in qc_sheets)
    
    # Calculate pass rate from actual inspection counts
    if total_inspected > 0:
        pass_rate = round((total_passed / total_inspected * 100), 1)
    elif total_qc > 0:
        pass_rate = round((passed_qc / total_qc * 100), 1)
    else:
        pass_rate = 100.0
    
    return jsonify({
        'total_defects': int(total_defects),
        'open_defects': open_defects,
        'resolved_defects': resolved_defects,
        'pass_rate': pass_rate,
        'total_inspected': total_inspected,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'period': period
    })


@api_bp.route('/qc/dashboard/trends', methods=['GET'])
@login_required
def get_monitoring_trends():
    """Get trend data for charts from real QC data."""
    days = 30
    start_date = datetime.now() - timedelta(days=days)
    
    # 1. Daily Defect Trend
    daily_stats = db.session.query(
        func.date(DefectLog.created_at).label('date'),
        func.sum(DefectLog.qty_defect).label('count')
    ).filter(
        DefectLog.created_at >= start_date
    ).group_by(
        func.date(DefectLog.created_at)
    ).order_by(
        func.date(DefectLog.created_at)
    ).all()
    
    trend_labels = [d[0].strftime('%d/%m') if d[0] else '' for d in daily_stats]
    trend_data = [int(d[1] or 0) for d in daily_stats]
    
    # 2. Top Defect Types (Pareto)
    top_defects = db.session.query(
        DefectLog.defect_type,
        func.sum(DefectLog.qty_defect).label('count')
    ).filter(
        DefectLog.created_at >= start_date,
        DefectLog.defect_type != None
    ).group_by(
        DefectLog.defect_type
    ).order_by(
        func.sum(DefectLog.qty_defect).desc()
    ).limit(5).all()
    
    pareto_labels = [d[0] or 'Unknown' for d in top_defects]
    pareto_data = [int(d[1] or 0) for d in top_defects]
    
    # 3. Defects by Stage
    stage_stats = db.session.query(
        DefectLog.process_stage,
        func.count(DefectLog.id).label('count')
    ).filter(
        DefectLog.created_at >= start_date,
        DefectLog.process_stage != None
    ).group_by(
        DefectLog.process_stage
    ).all()
    
    stage_labels = [d[0] or 'Unknown' for d in stage_stats]
    stage_data = [int(d[1] or 0) for d in stage_stats]
    
    return jsonify({
        'trend': {'labels': trend_labels, 'data': trend_data},
        'pareto': {'labels': pareto_labels, 'data': pareto_data},
        'stage': {'labels': stage_labels, 'data': stage_data}
    })


@api_bp.route('/qc/dashboard/parameters', methods=['GET'])
@login_required
def get_parameter_stats():
    """Get statistics from QC Checklist parameters across all stations."""
    days = int(request.args.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    # Get all QC sheets with checklist data
    qc_sheets = QCSheet.query.filter(
        QCSheet.created_at >= start_date,
        QCSheet.checklist_json != None
    ).all()
    
    # Aggregate parameter statistics
    param_stats = {}
    stage_param_stats = {}
    
    for sheet in qc_sheets:
        # Get process stage from linked production task
        stage = None
        if sheet.production_task:
            stage = sheet.production_task.process
        
        checklist = sheet.checklist_json or []
        for item in checklist:
            if not isinstance(item, dict):
                continue
                
            param_name = item.get('name', item.get('id', 'Unknown'))
            qty_checked = int(item.get('qty_checked', 0) or 0)
            qty_ng = int(item.get('qty_ng', 0) or 0)
            status = item.get('status', '')
            
            # Aggregate by parameter name
            if param_name not in param_stats:
                param_stats[param_name] = {
                    'name': param_name,
                    'total_checked': 0,
                    'total_ng': 0,
                    'pass_count': 0,
                    'fail_count': 0
                }
            
            param_stats[param_name]['total_checked'] += qty_checked
            param_stats[param_name]['total_ng'] += qty_ng
            if status == 'pass':
                param_stats[param_name]['pass_count'] += 1
            elif status == 'fail':
                param_stats[param_name]['fail_count'] += 1
            
            # Aggregate by stage
            if stage:
                if stage not in stage_param_stats:
                    stage_param_stats[stage] = {'total_checked': 0, 'total_ng': 0}
                stage_param_stats[stage]['total_checked'] += qty_checked
                stage_param_stats[stage]['total_ng'] += qty_ng
    
    # Calculate failure rates and sort by NG count
    for param in param_stats.values():
        if param['total_checked'] > 0:
            param['failure_rate'] = round((param['total_ng'] / param['total_checked']) * 100, 1)
        else:
            param['failure_rate'] = 0
    
    # Top failing parameters
    top_params = sorted(param_stats.values(), key=lambda x: x['total_ng'], reverse=True)[:10]
    
    # Stage breakdown
    stage_breakdown = []
    for stage, stats in stage_param_stats.items():
        failure_rate = round((stats['total_ng'] / stats['total_checked'] * 100), 1) if stats['total_checked'] > 0 else 0
        stage_breakdown.append({
            'stage': stage,
            'total_checked': stats['total_checked'],
            'total_ng': stats['total_ng'],
            'failure_rate': failure_rate
        })
    
    return jsonify({
        'top_failing_parameters': top_params,
        'stage_breakdown': stage_breakdown,
        'total_sheets_analyzed': len(qc_sheets)
    })


@api_bp.route('/qc/defects', methods=['GET'])
@login_required
def list_monitoring_defects():
    """Get list of defects with filtering."""
    status = request.args.get('status')
    search = request.args.get('search')
    stage = request.args.get('stage')
    
    query = DefectLog.query
    
    # Filter by status (string comparison)
    if status:
        query = query.filter(DefectLog.status == status)
    
    if stage:
        query = query.filter(DefectLog.process_stage == stage)
        
    if search:
        query = query.filter(
            db.or_(
                DefectLog.defect_type.ilike(f'%{search}%'),
                DefectLog.description.ilike(f'%{search}%')
            )
        )
        
    defects = query.order_by(DefectLog.created_at.desc()).limit(50).all()
    
    return jsonify({
        'defects': [d.to_dict() for d in defects]
    })


@api_bp.route('/qc/defects', methods=['POST'])
@login_required
def create_defect():
    """Create a standalone defect log (via monitoring dashboard)."""
    data = request.get_json()
    
    task_id = data.get('production_task_id')
    if not task_id:
        return jsonify({'error': 'Production Task ID is required'}), 400
        
    # Find existing open QC sheet or create new one
    qc_sheet = QCSheet.query.filter_by(production_task_id=task_id).order_by(QCSheet.id.desc()).first()
    
    if not qc_sheet:
        task = ProductionTask.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
            
        qc_sheet = QCSheet(
            production_task_id=task_id,
            inspection_code=QCSheet.generate_inspection_code(),
            inspector_id=current_user.id,
            inspected_at=datetime.utcnow(),
            result='pending'  # Use string instead of Enum
        )
        db.session.add(qc_sheet)
        db.session.flush()
    
    defect = DefectLog(
        qc_sheet_id=qc_sheet.id,
        defect_type=data['defect_type'],
        defect_category=data.get('defect_category'),
        severity=data.get('severity', 'minor'),
        qty_defect=data.get('qty_defect', 1),
        description=data.get('description'),
        station=data.get('station'),
        process_stage=data.get('process_stage'),
        reported_by=current_user.id,
        status='open'  # Default status as string
    )
    
    db.session.add(defect)
    
    # Update stats
    qc_sheet.qty_failed = (qc_sheet.qty_failed or 0) + defect.qty_defect
    qc_sheet.qty_inspected = (qc_sheet.qty_inspected or 0) + defect.qty_defect
    
    db.session.commit()
    
    return jsonify({
        'message': 'Defect recorded successfully',
        'defect': defect.to_dict()
    }), 201


@api_bp.route('/qc/defects/<int:defect_id>', methods=['PUT'])
@login_required
def update_defect(defect_id):
    """Update defect (Action Taken, Verification, etc)."""
    defect = DefectLog.query.get_or_404(defect_id)
    data = request.get_json()
    
    if 'action_taken' in data:
        defect.action_taken = data['action_taken']
    if 'responsible_department' in data:
        defect.responsible_department = data['responsible_department']
    if 'target_resolution_date' in data and data['target_resolution_date']:
        defect.target_resolution_date = datetime.strptime(data['target_resolution_date'], '%Y-%m-%d').date()
    
    if 'verification_result' in data:
        defect.verification_result = data['verification_result']
    if 'verification_notes' in data:
        defect.verification_notes = data['verification_notes']
        
    if 'status' in data:
        old_status = defect.status
        new_status = data['status']
        defect.status = new_status  # Use string directly
        
        # If resolving/closing
        if new_status in ['resolved', 'closed'] and old_status not in ['resolved', 'closed']:
            defect.resolved_at = datetime.utcnow()
            defect.resolved_by = current_user.id
            
    db.session.commit()
    return jsonify({
        'message': 'Defect updated successfully',
        'defect': defect.to_dict()
    })


# ============================================
# Advanced Analytics Endpoints
# ============================================

from ..services.qc_analytics import QCAnalyticsService


@api_bp.route('/qc/dashboard/checklist-analysis', methods=['GET'])
@login_required
def get_checklist_analysis():
    """Deep analysis of checklist parameters with statistical insights."""
    days = int(request.args.get('days', 30))
    result = QCAnalyticsService.get_checklist_analysis(days)
    return jsonify(result)


@api_bp.route('/qc/dashboard/quality-score', methods=['GET'])
@login_required
def get_quality_score():
    """Get overall quality score with FPY calculation."""
    days = int(request.args.get('days', 30))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    score_data = QCAnalyticsService.calculate_quality_score(start_date, end_date)
    fpy_data = QCAnalyticsService.calculate_fpy(start_date, end_date)
    
    return jsonify({
        'quality_score': score_data['quality_score'],
        'grade': score_data['grade'],
        'status': score_data['status'],
        'components': score_data['components'],
        'fpy': fpy_data['fpy_percentage'],
        'total_inspected': fpy_data['total_inspected'],
        'total_passed': fpy_data['total_passed'],
        'total_failed': fpy_data['total_failed'],
        'period_days': days
    })


@api_bp.route('/qc/dashboard/process-comparison', methods=['GET'])
@login_required
def get_process_comparison():
    """Compare quality metrics across process stages."""
    days = int(request.args.get('days', 30))
    result = QCAnalyticsService.get_process_comparison(days)
    return jsonify(result)


@api_bp.route('/qc/dashboard/summary-report', methods=['GET'])
@login_required
def get_summary_report():
    """Generate summary report with comparison to previous period."""
    period = request.args.get('period', 'week')
    result = QCAnalyticsService.generate_summary_report(period)
    return jsonify(result)


@api_bp.route('/qc/dashboard/parameter-trends', methods=['GET'])
@login_required
def get_parameter_trends():
    """Get parameter failure trends over time."""
    days = int(request.args.get('days', 30))
    result = QCAnalyticsService.get_parameter_trends(days)
    return jsonify(result)


@api_bp.route('/qc/dashboard/defect-pareto', methods=['GET'])
@login_required
def get_defect_pareto():
    """Get Pareto analysis data for defect types."""
    days = int(request.args.get('days', 30))
    result = QCAnalyticsService.get_defect_pareto(days)
    return jsonify(result)


@api_bp.route('/qc/dashboard/defect-rate-trends', methods=['GET'])
@login_required
def get_defect_rate_trends():
    """Get defect rate trends over time."""
    period = request.args.get('period', 'weekly')
    count = int(request.args.get('count', 12))
    result = QCAnalyticsService.get_defect_rate_trends(period, count)
    return jsonify(result)


@api_bp.route('/qc/dashboard/export-csv', methods=['GET'])
@login_required
def export_qc_csv():
    """Export QC data as CSV format."""
    from flask import Response
    import csv
    import io
    
    days = int(request.args.get('days', 30))
    report = QCAnalyticsService.generate_summary_report('week' if days <= 7 else 'month')
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['QC Analytics Report'])
    writer.writerow(['Generated At', report['generated_at']])
    writer.writerow(['Period', report['period_start'], 'to', report['period_end']])
    writer.writerow([])
    
    # Summary
    writer.writerow(['Summary Metrics'])
    writer.writerow(['Metric', 'Value', 'Change', 'Trend'])
    summary = report['summary']
    writer.writerow(['First Pass Yield (%)', summary['fpy'], summary['fpy_change'], summary['fpy_trend']])
    writer.writerow(['Quality Score', summary['quality_score'], summary['score_change'], summary['score_trend']])
    writer.writerow(['Quality Grade', summary['quality_grade'], '', ''])
    writer.writerow(['Total Inspected', summary['total_inspected'], '', ''])
    writer.writerow(['Total Passed', summary['total_passed'], '', ''])
    writer.writerow(['Total Failed', summary['total_failed'], '', ''])
    writer.writerow(['Total Defects', summary['total_defects'], '', ''])
    writer.writerow(['Open Defects', summary['open_defects'], '', ''])
    writer.writerow([])
    
    # Process Comparison
    writer.writerow(['Process Stage Comparison'])
    writer.writerow(['Stage', 'Total Sheets', 'Total Inspected', 'Pass Rate (%)', 'NG Rate (%)'])
    for stage in report['process_comparison']:
        writer.writerow([
            stage['name'],
            stage['total_sheets'],
            stage['total_inspected'],
            stage['pass_rate'],
            stage['ng_rate']
        ])
    writer.writerow([])
    
    # Top Issues
    writer.writerow(['Top Quality Issues'])
    writer.writerow(['Parameter', 'Total Checked', 'Total NG', 'NG Rate (%)', 'Trend'])
    for issue in report['top_issues']:
        writer.writerow([
            issue['parameter'],
            issue['total_checked'],
            issue['total_ng'],
            issue['avg_ng_rate'],
            issue['trend']
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=qc_report_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
