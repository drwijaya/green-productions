"""
QC Analytics Service Module
Provides advanced analytics and reporting functions for Quality Control data.
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from ..extensions import db
from ..models import QCSheet, DefectLog, ProductionTask, Order, QCResult


class QCAnalyticsService:
    """Service for QC data analytics and reporting."""
    
    # Quality Score Weights (customize as needed)
    WEIGHTS = {
        'pass_rate': 0.4,        # 40% weight for overall pass rate
        'ng_rate': 0.3,          # 30% weight for NG rate (inverted)
        'resolution_rate': 0.2,  # 20% weight for defect resolution
        'consistency': 0.1       # 10% weight for consistency
    }
    
    @staticmethod
    def calculate_fpy(start_date=None, end_date=None):
        """
        Calculate First Pass Yield (FPY) percentage.
        FPY = (Units passing QC on first attempt / Total units inspected) * 100
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get QC sheets in period
        sheets = QCSheet.query.filter(
            QCSheet.created_at >= start_date,
            QCSheet.created_at <= end_date
        ).all()
        
        total_inspected = sum(s.qty_inspected or 0 for s in sheets)
        total_passed = sum(s.qty_passed or 0 for s in sheets)
        
        if total_inspected == 0:
            return {
                'fpy_percentage': 100.0,
                'total_inspected': 0,
                'total_passed': 0,
                'total_failed': 0,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat()
            }
        
        fpy = round((total_passed / total_inspected) * 100, 2)
        
        return {
            'fpy_percentage': fpy,
            'total_inspected': total_inspected,
            'total_passed': total_passed,
            'total_failed': total_inspected - total_passed,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
    
    @staticmethod
    def get_parameter_trends(days=30):
        """
        Get parameter failure trends over time.
        Returns weekly breakdown of NG rates per parameter.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all QC sheets with checklist data
        sheets = QCSheet.query.filter(
            QCSheet.created_at >= start_date,
            QCSheet.checklist_json != None
        ).order_by(QCSheet.created_at).all()
        
        # Group by week
        weekly_data = {}
        param_totals = {}
        
        for sheet in sheets:
            # Get week number
            week_num = sheet.created_at.isocalendar()[1]
            week_key = f"W{week_num}"
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {}
            
            checklist = sheet.checklist_json or []
            for item in checklist:
                if not isinstance(item, dict):
                    continue
                
                param_name = item.get('name', item.get('parameter', 'Unknown'))
                qty_checked = int(item.get('qty_checked', 0) or 0)
                qty_ng = int(item.get('qty_ng', 0) or 0)
                
                if param_name not in weekly_data[week_key]:
                    weekly_data[week_key][param_name] = {'checked': 0, 'ng': 0}
                
                weekly_data[week_key][param_name]['checked'] += qty_checked
                weekly_data[week_key][param_name]['ng'] += qty_ng
                
                # Track totals for trend calculation
                if param_name not in param_totals:
                    param_totals[param_name] = {'checked': 0, 'ng': 0, 'weeks': []}
                param_totals[param_name]['checked'] += qty_checked
                param_totals[param_name]['ng'] += qty_ng
        
        # Calculate trends (improvement/decline)
        trends = []
        weeks = sorted(weekly_data.keys())
        
        for param_name, totals in param_totals.items():
            if totals['checked'] == 0:
                continue
                
            avg_ng_rate = round((totals['ng'] / totals['checked']) * 100, 2)
            
            # Calculate trend direction
            trend_direction = 'stable'
            if len(weeks) >= 2:
                first_week = weeks[0]
                last_week = weeks[-1]
                
                first_data = weekly_data.get(first_week, {}).get(param_name, {'checked': 0, 'ng': 0})
                last_data = weekly_data.get(last_week, {}).get(param_name, {'checked': 0, 'ng': 0})
                
                first_rate = (first_data['ng'] / first_data['checked'] * 100) if first_data['checked'] > 0 else 0
                last_rate = (last_data['ng'] / last_data['checked'] * 100) if last_data['checked'] > 0 else 0
                
                if last_rate < first_rate - 0.5:
                    trend_direction = 'improving'
                elif last_rate > first_rate + 0.5:
                    trend_direction = 'declining'
            
            trends.append({
                'parameter': param_name,
                'total_checked': totals['checked'],
                'total_ng': totals['ng'],
                'avg_ng_rate': avg_ng_rate,
                'trend': trend_direction
            })
        
        # Sort by NG rate descending
        trends.sort(key=lambda x: x['avg_ng_rate'], reverse=True)
        
        return {
            'weeks': weeks,
            'weekly_data': weekly_data,
            'parameter_trends': trends[:15],  # Top 15
            'period_days': days
        }
    
    @staticmethod
    def calculate_quality_score(start_date=None, end_date=None):
        """
        Calculate weighted quality score (0-100).
        Higher score = better quality.
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get FPY data
        fpy_data = QCAnalyticsService.calculate_fpy(start_date, end_date)
        fpy_score = fpy_data['fpy_percentage']
        
        # Calculate NG rate score (inverted - lower NG = higher score)
        sheets = QCSheet.query.filter(
            QCSheet.created_at >= start_date,
            QCSheet.created_at <= end_date,
            QCSheet.checklist_json != None
        ).all()
        
        total_checked = 0
        total_ng = 0
        
        for sheet in sheets:
            checklist = sheet.checklist_json or []
            for item in checklist:
                if isinstance(item, dict):
                    total_checked += int(item.get('qty_checked', 0) or 0)
                    total_ng += int(item.get('qty_ng', 0) or 0)
        
        ng_rate = (total_ng / total_checked * 100) if total_checked > 0 else 0
        ng_score = max(0, 100 - (ng_rate * 10))  # 10% NG = 0 score
        
        # Calculate resolution rate score
        total_defects = DefectLog.query.filter(
            DefectLog.created_at >= start_date,
            DefectLog.created_at <= end_date
        ).count()
        
        resolved_defects = DefectLog.query.filter(
            DefectLog.created_at >= start_date,
            DefectLog.created_at <= end_date,
            DefectLog.status.in_(['resolved', 'closed'])
        ).count()
        
        resolution_score = (resolved_defects / total_defects * 100) if total_defects > 0 else 100
        
        # Calculate consistency score (standard deviation of NG rates)
        consistency_score = 85  # Default baseline
        
        # Weighted final score
        weights = QCAnalyticsService.WEIGHTS
        quality_score = round(
            (fpy_score * weights['pass_rate']) +
            (ng_score * weights['ng_rate']) +
            (resolution_score * weights['resolution_rate']) +
            (consistency_score * weights['consistency']),
            1
        )
        
        # Determine grade
        if quality_score >= 90:
            grade = 'A'
            status = 'Excellent'
        elif quality_score >= 80:
            grade = 'B'
            status = 'Good'
        elif quality_score >= 70:
            grade = 'C'
            status = 'Average'
        elif quality_score >= 60:
            grade = 'D'
            status = 'Below Average'
        else:
            grade = 'F'
            status = 'Critical'
        
        return {
            'quality_score': quality_score,
            'grade': grade,
            'status': status,
            'components': {
                'fpy_score': round(fpy_score, 1),
                'ng_score': round(ng_score, 1),
                'resolution_score': round(resolution_score, 1),
                'consistency_score': round(consistency_score, 1)
            },
            'weights': weights,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat()
        }
    
    @staticmethod
    def get_process_comparison(days=30):
        """
        Compare quality metrics across process stages (Cutting, Sewing, Finishing, Sablon, Packing).
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all QC sheets with production task info
        sheets = QCSheet.query.join(
            ProductionTask, QCSheet.production_task_id == ProductionTask.id
        ).filter(
            QCSheet.created_at >= start_date
        ).all()
        
        # Aggregate by process stage
        stage_data = {}
        
        for sheet in sheets:
            if not sheet.production_task:
                continue
                
            stage = sheet.production_task.process or 'unknown'
            
            if stage not in stage_data:
                stage_data[stage] = {
                    'name': stage.title(),
                    'total_sheets': 0,
                    'total_inspected': 0,
                    'total_passed': 0,
                    'total_failed': 0,
                    'total_checked': 0,
                    'total_ng': 0,
                    'pass_count': 0,
                    'fail_count': 0
                }
            
            stage_data[stage]['total_sheets'] += 1
            stage_data[stage]['total_inspected'] += sheet.qty_inspected or 0
            stage_data[stage]['total_passed'] += sheet.qty_passed or 0
            stage_data[stage]['total_failed'] += sheet.qty_failed or 0
            
            if sheet.result in [QCResult.PASS, QCResult.CONDITIONAL_PASS]:
                stage_data[stage]['pass_count'] += 1
            elif sheet.result == QCResult.FAIL:
                stage_data[stage]['fail_count'] += 1
            
            # Aggregate from checklist
            checklist = sheet.checklist_json or []
            for item in checklist:
                if isinstance(item, dict):
                    stage_data[stage]['total_checked'] += int(item.get('qty_checked', 0) or 0)
                    stage_data[stage]['total_ng'] += int(item.get('qty_ng', 0) or 0)
        
        # Calculate metrics
        comparison = []
        for stage, data in stage_data.items():
            pass_rate = round((data['total_passed'] / data['total_inspected'] * 100), 1) if data['total_inspected'] > 0 else 0
            ng_rate = round((data['total_ng'] / data['total_checked'] * 100), 2) if data['total_checked'] > 0 else 0
            sheet_pass_rate = round((data['pass_count'] / data['total_sheets'] * 100), 1) if data['total_sheets'] > 0 else 0
            
            comparison.append({
                'stage': stage,
                'name': data['name'],
                'total_sheets': data['total_sheets'],
                'total_inspected': data['total_inspected'],
                'total_passed': data['total_passed'],
                'total_ng': data['total_ng'],
                'pass_rate': pass_rate,
                'ng_rate': ng_rate,
                'sheet_pass_rate': sheet_pass_rate
            })
        
        # Sort by total sheets (most inspected first)
        comparison.sort(key=lambda x: x['total_sheets'], reverse=True)
        
        # Find best and worst stages
        if comparison:
            best_stage = min(comparison, key=lambda x: x['ng_rate'])
            worst_stage = max(comparison, key=lambda x: x['ng_rate'])
        else:
            best_stage = worst_stage = None
        
        return {
            'stages': comparison,
            'best_stage': best_stage,
            'worst_stage': worst_stage,
            'period_days': days
        }
    
    @staticmethod
    def generate_summary_report(period='week'):
        """
        Generate exportable summary report data.
        """
        end_date = datetime.now()
        
        if period == 'week':
            start_date = end_date - timedelta(days=7)
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
            prev_start = start_date - timedelta(days=30)
            prev_end = start_date
        else:
            start_date = end_date - timedelta(days=7)
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date
        
        # Current period data
        current_fpy = QCAnalyticsService.calculate_fpy(start_date, end_date)
        current_score = QCAnalyticsService.calculate_quality_score(start_date, end_date)
        current_process = QCAnalyticsService.get_process_comparison(7 if period == 'week' else 30)
        
        # Previous period data for comparison
        prev_fpy = QCAnalyticsService.calculate_fpy(prev_start, prev_end)
        prev_score = QCAnalyticsService.calculate_quality_score(prev_start, prev_end)
        
        # Calculate changes
        fpy_change = round(current_fpy['fpy_percentage'] - prev_fpy['fpy_percentage'], 2)
        score_change = round(current_score['quality_score'] - prev_score['quality_score'], 1)
        
        # Get top issues
        trends = QCAnalyticsService.get_parameter_trends(7 if period == 'week' else 30)
        top_issues = trends['parameter_trends'][:5]
        
        # Defect summary
        total_defects = DefectLog.query.filter(
            DefectLog.created_at >= start_date,
            DefectLog.created_at <= end_date
        ).count()
        
        open_defects = DefectLog.query.filter(
            DefectLog.created_at >= start_date,
            DefectLog.status.in_(['open', 'in_progress'])
        ).count()
        
        return {
            'period': period,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'summary': {
                'fpy': current_fpy['fpy_percentage'],
                'fpy_change': fpy_change,
                'fpy_trend': 'up' if fpy_change > 0 else 'down' if fpy_change < 0 else 'stable',
                'quality_score': current_score['quality_score'],
                'quality_grade': current_score['grade'],
                'score_change': score_change,
                'score_trend': 'up' if score_change > 0 else 'down' if score_change < 0 else 'stable',
                'total_inspected': current_fpy['total_inspected'],
                'total_passed': current_fpy['total_passed'],
                'total_failed': current_fpy['total_failed'],
                'total_defects': total_defects,
                'open_defects': open_defects
            },
            'process_comparison': current_process['stages'],
            'top_issues': top_issues,
            'generated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def get_checklist_analysis(days=30):
        """
        Deep analysis of checklist parameters with statistical insights.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all QC sheets with checklist data
        sheets = QCSheet.query.filter(
            QCSheet.created_at >= start_date,
            QCSheet.checklist_json != None
        ).all()
        
        # Aggregate parameter data
        param_data = {}
        
        for sheet in sheets:
            stage = sheet.production_task.process if sheet.production_task else 'unknown'
            checklist = sheet.checklist_json or []
            
            for item in checklist:
                if not isinstance(item, dict):
                    continue
                
                param_name = item.get('name', item.get('parameter', 'Unknown'))
                qty_checked = int(item.get('qty_checked', 0) or 0)
                qty_ng = int(item.get('qty_ng', 0) or 0)
                status = item.get('status', 'pending')
                
                key = f"{stage}|{param_name}"
                
                if key not in param_data:
                    param_data[key] = {
                        'stage': stage,
                        'parameter': param_name,
                        'total_checked': 0,
                        'total_ng': 0,
                        'samples': [],
                        'pass_count': 0,
                        'fail_count': 0
                    }
                
                param_data[key]['total_checked'] += qty_checked
                param_data[key]['total_ng'] += qty_ng
                
                if qty_checked > 0:
                    param_data[key]['samples'].append(qty_ng / qty_checked * 100)
                
                if status == 'pass':
                    param_data[key]['pass_count'] += 1
                elif status == 'fail':
                    param_data[key]['fail_count'] += 1
        
        # Calculate statistics
        analysis = []
        for key, data in param_data.items():
            if data['total_checked'] == 0:
                continue
            
            ng_rate = round((data['total_ng'] / data['total_checked']) * 100, 2)
            
            # Calculate variance
            samples = data['samples']
            if len(samples) > 1:
                mean = sum(samples) / len(samples)
                variance = sum((x - mean) ** 2 for x in samples) / len(samples)
                std_dev = round(variance ** 0.5, 2)
            else:
                std_dev = 0
            
            # Determine status
            if ng_rate > 2.5:
                status = 'critical'
            elif ng_rate > 1:
                status = 'warning'
            else:
                status = 'good'
            
            analysis.append({
                'stage': data['stage'],
                'parameter': data['parameter'],
                'total_checked': data['total_checked'],
                'total_ng': data['total_ng'],
                'ng_rate': ng_rate,
                'std_dev': std_dev,
                'sample_count': len(samples),
                'pass_count': data['pass_count'],
                'fail_count': data['fail_count'],
                'status': status
            })
        
        # Sort by NG rate descending
        analysis.sort(key=lambda x: x['ng_rate'], reverse=True)
        
        # Group by stage
        by_stage = {}
        for item in analysis:
            stage = item['stage']
            if stage not in by_stage:
                by_stage[stage] = []
            by_stage[stage].append(item)
        
        return {
            'total_parameters_analyzed': len(analysis),
            'total_sheets_analyzed': len(sheets),
            'parameters': analysis[:20],  # Top 20
            'by_stage': by_stage,
            'period_days': days
        }
    
    @staticmethod
    def get_defect_pareto(days=30):
        """
        Get Pareto analysis data for defect types.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query defect logs grouped by type
        results = db.session.query(
            DefectLog.defect_type,
            func.sum(DefectLog.qty_defect).label('total_qty')
        ).filter(
            DefectLog.created_at >= start_date,
            DefectLog.defect_type != None
        ).group_by(
            DefectLog.defect_type
        ).order_by(
            func.sum(DefectLog.qty_defect).desc()
        ).limit(10).all()
        
        # Calculate cumulative percentage
        total_defects = sum(r[1] or 0 for r in results)
        pareto_data = []
        cumulative_qty = 0
        
        for r in results:
            qty = int(r[1] or 0)
            cumulative_qty += qty
            cumulative_pct = round((cumulative_qty / total_defects * 100), 1) if total_defects > 0 else 0
            
            pareto_data.append({
                'type': r[0],
                'count': qty,
                'cumulative_percentage': cumulative_pct
            })
            
        return {
            'total_defects': total_defects,
            'pareto_data': pareto_data,
            'period_days': days
        }
