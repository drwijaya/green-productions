"""QC Sheet and Defect Log models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class QCResult(Enum):
    """QC inspection result."""
    PENDING = 'pending'
    PASS = 'pass'
    FAIL = 'fail'
    REWORK = 'rework'
    CONDITIONAL_PASS = 'conditional_pass'


class DefectSeverity(Enum):
    """Defect severity levels."""
    MINOR = 'minor'
    MAJOR = 'major'
    CRITICAL = 'critical'


class QCSheet(db.Model):
    """QC inspection/report sheet - Optional quality documentation."""
    __tablename__ = 'qc_sheet'
    
    id = db.Column(db.Integer, primary_key=True)
    # QC can be linked to either production task or order (both optional)
    production_task_id = db.Column(db.Integer, db.ForeignKey('production_tasks.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Inspection Details
    inspection_code = db.Column(db.String(50), unique=True, nullable=False)
    checklist_json = db.Column(db.JSON)  # Auto-loaded from DSO
    # Example: [{"item": "Jahitan lurus", "standard": "±2mm", "result": "pass", "notes": ""}]
    
    # Results
    result = db.Column(db.Enum(QCResult), default=QCResult.PENDING)
    qty_inspected = db.Column(db.Integer, default=0)
    qty_passed = db.Column(db.Integer, default=0)
    qty_failed = db.Column(db.Integer, default=0)
    
    # Photos
    photos_json = db.Column(db.JSON)  # Array of photo URLs
    
    # Inspector
    inspector_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    inspected_at = db.Column(db.DateTime)
    
    # Barcode scan requirement
    barcode_scanned = db.Column(db.Boolean, default=False)
    barcode_scan_time = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    defects = db.relationship('DefectLog', backref='qc_sheet', lazy='dynamic', cascade='all, delete-orphan')
    order = db.relationship('Order', backref=db.backref('qc_reports', lazy='dynamic'))
    # production_task relationship is defined via backref from ProductionTask.qc_sheets
    
    @staticmethod
    def generate_inspection_code():
        """Generate unique inspection code."""
        today = datetime.now()
        prefix = f"QC-{today.strftime('%Y%m%d')}"
        last_qc = QCSheet.query.filter(
            QCSheet.inspection_code.like(f'{prefix}%')
        ).order_by(QCSheet.id.desc()).first()
        
        if last_qc:
            last_num = int(last_qc.inspection_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def get_pass_rate(self):
        """Calculate pass rate percentage."""
        if self.qty_inspected == 0:
            return 0
        return round((self.qty_passed / self.qty_inspected) * 100, 2)
    
    def has_critical_defect(self):
        """Check if there are any critical defects."""
        return self.defects.filter_by(severity=DefectSeverity.CRITICAL).count() > 0
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'production_task_id': self.production_task_id,
            'order_id': self.order_id,
            'inspection_code': self.inspection_code,
            'checklist_json': self.checklist_json,
            'result': self.result.value if self.result else 'pending',
            'qty_inspected': self.qty_inspected,
            'qty_passed': self.qty_passed,
            'qty_failed': self.qty_failed,
            'pass_rate': self.get_pass_rate(),
            'photos_json': self.photos_json,
            'inspector_id': self.inspector_id,
            'inspected_at': self.inspected_at.isoformat() if self.inspected_at else None,
            'barcode_scanned': self.barcode_scanned,
            'notes': self.notes,
            'has_critical_defect': self.has_critical_defect(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_relations:
            data['defects'] = [d.to_dict() for d in self.defects.all()]
            # Don't include full production_task to avoid recursion, just basic info
            if self.production_task:
                data['production_task'] = {
                    'id': self.production_task.id,
                    'process': self.production_task.process,
                    'status': self.production_task.status
                }
            else:
                data['production_task'] = None
            # Don't include full order to avoid recursion, just basic info  
            if self.order:
                data['order'] = {
                    'id': self.order.id,
                    'order_code': self.order.order_code,
                    'model': self.order.model
                }
            else:
                data['order'] = None
        
        return data

    
    def __repr__(self):
        return f'<QCSheet {self.inspection_code}>'


class DefectStatus(Enum):
    """Defect resolution status."""
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class DefectLog(db.Model):
    """Defect log for QC inspections."""
    __tablename__ = 'defect_log'
    
    id = db.Column(db.Integer, primary_key=True)
    qc_sheet_id = db.Column(db.Integer, db.ForeignKey('qc_sheet.id'), nullable=False)
    
    # B. INFORMASI DEFECT
    defect_type = db.Column(db.String(100), nullable=False)
    defect_category = db.Column(db.String(100))  # e.g., Jahitan, Kain, Aksesoris
    severity = db.Column(db.Enum(DefectSeverity), nullable=False, default=DefectSeverity.MINOR)
    qty_defect = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    
    # Photo evidence
    photo_url = db.Column(db.String(500))
    photo_annotations_json = db.Column(db.JSON)  # Fabric.js annotations
    
    # Context (Where it happened)
    station = db.Column(db.String(100)) # Specific station/machine
    process_stage = db.Column(db.String(50)) # Cutting, Sewing, Finishing, etc.
    
    # C. TINDAKAN PENANGANAN
    action_taken = db.Column(db.Text)
    responsible_department = db.Column(db.String(100)) # Bagian Penanggung Jawab
    target_resolution_date = db.Column(db.Date) # Target Penyelesaian
    
    # D. VERIFIKASI HASIL
    verification_result = db.Column(db.String(20)) # Sesuai / Tidak Sesuai
    verification_notes = db.Column(db.Text) # Catatan QC
    status = db.Column(db.String(50), default='open') # Status Akhir
    
    # Audit & Timeline
    reported_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # E. TANDA TANGAN (Linked to Employees)
    rework_operator_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    qc_operator_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Relationships
    reporter = db.relationship('Employee', foreign_keys=[reported_by])
    resolver = db.relationship('Employee', foreign_keys=[resolved_by])
    rework_operator = db.relationship('Employee', foreign_keys=[rework_operator_id])
    qc_operator = db.relationship('Employee', foreign_keys=[qc_operator_id])
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'qc_sheet_id': self.qc_sheet_id,
            'defect_type': self.defect_type,
            'defect_category': self.defect_category,
            'severity': self.severity.value,
            'qty_defect': self.qty_defect,
            'description': self.description,
            'photo_url': self.photo_url,
            'station': self.station,
            'process_stage': self.process_stage,
            'action_taken': self.action_taken,
            'responsible_department': self.responsible_department,
            'target_resolution_date': self.target_resolution_date.isoformat() if self.target_resolution_date else None,
            'verification_result': self.verification_result,
            'verification_notes': self.verification_notes,
            'status': self.status,
            'reported_by_name': self.reporter.name if self.reporter else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'order_code': self.qc_sheet.order.order_code if self.qc_sheet and self.qc_sheet.order else 
                         (self.qc_sheet.production_task.order.order_code if self.qc_sheet and self.qc_sheet.production_task else None),
            'product_name': self.qc_sheet.order.model if self.qc_sheet and self.qc_sheet.order else 
                           (self.qc_sheet.production_task.order.model if self.qc_sheet and self.qc_sheet.production_task else None),
            'customer_name': self.qc_sheet.order.customer.name if self.qc_sheet and self.qc_sheet.order and self.qc_sheet.order.customer else 
                            (self.qc_sheet.production_task.order.customer.name if self.qc_sheet and self.qc_sheet.production_task and self.qc_sheet.production_task.order.customer else None),
            'production_task_id': self.qc_sheet.production_task_id if self.qc_sheet else None
        }
    
    def __repr__(self):
        return f'<DefectLog {self.defect_type} ({self.status})>'
