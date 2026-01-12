"""Material Request and QC models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class MaterialRequestStatus(Enum):
    """Material request status enum."""
    REQUESTED = 'requested'
    IN_TRANSIT = 'in_transit'
    ARRIVED = 'arrived'
    QC_PENDING = 'qc_pending'
    QC_PASSED = 'qc_passed'
    QC_FAILED = 'qc_failed'
    STORED = 'stored'
    CANCELLED = 'cancelled'


class MaterialQCResult(Enum):
    """Material QC result enum."""
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    PASS = 'pass'
    FAIL = 'fail'
    CONDITIONAL_PASS = 'conditional_pass'


class MaterialRequest(db.Model):
    """Material request model for procurement management."""
    __tablename__ = 'material_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # Optional link to order
    
    # Status tracking
    status = db.Column(db.String(50), default='requested')
    
    # Dates
    request_date = db.Column(db.Date, default=datetime.utcnow)
    expected_arrival = db.Column(db.Date)
    actual_arrival = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('MaterialRequestItem', backref='material_request', lazy='dynamic', cascade='all, delete-orphan')
    qc_sheet = db.relationship('MaterialQCSheet', backref='material_request', uselist=False, cascade='all, delete-orphan')
    order = db.relationship('Order', backref=db.backref('material_requests', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by])
    
    @staticmethod
    def generate_request_code():
        """Generate unique request code."""
        today = datetime.now()
        prefix = f"MR-{today.strftime('%Y%m')}"
        last_request = MaterialRequest.query.filter(
            MaterialRequest.request_code.like(f'{prefix}%')
        ).order_by(MaterialRequest.id.desc()).first()
        
        if last_request:
            last_num = int(last_request.request_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def get_total_items(self):
        """Get total number of items."""
        return self.items.count()
    
    def get_total_qty(self):
        """Get total quantity ordered."""
        return sum(item.qty_ordered for item in self.items.all())
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'request_code': self.request_code,
            'vendor_id': self.vendor_id,
            'order_id': self.order_id,
            'status': self.status,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'expected_arrival': self.expected_arrival.isoformat() if self.expected_arrival else None,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'notes': self.notes,
            'total_items': self.get_total_items(),
            'total_qty': self.get_total_qty(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['vendor'] = self.vendor.to_dict() if self.vendor else None
            data['items'] = [item.to_dict() for item in self.items.all()]
            data['qc_sheet'] = self.qc_sheet.to_dict() if self.qc_sheet else None
            data['order'] = {'id': self.order.id, 'order_code': self.order.order_code} if self.order else None
        
        return data
    
    def __repr__(self):
        return f'<MaterialRequest {self.request_code}>'


class MaterialRequestItem(db.Model):
    """Material request item model."""
    __tablename__ = 'material_request_items'
    
    id = db.Column(db.Integer, primary_key=True)
    material_request_id = db.Column(db.Integer, db.ForeignKey('material_requests.id'), nullable=False)
    
    # Material details
    material_name = db.Column(db.String(200), nullable=False)
    material_type = db.Column(db.String(100))  # e.g., Kain, Benang, Kancing, dll
    specifications = db.Column(db.Text)
    color = db.Column(db.String(100))
    size = db.Column(db.String(100))
    
    # Quantity
    qty_ordered = db.Column(db.Integer, nullable=False)
    qty_received = db.Column(db.Integer, default=0)
    qty_rejected = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(50), default='pcs')  # pcs, meter, kg, roll, etc.
    
    # Notes
    notes = db.Column(db.Text)
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'material_request_id': self.material_request_id,
            'material_name': self.material_name,
            'material_type': self.material_type,
            'specifications': self.specifications,
            'color': self.color,
            'size': self.size,
            'qty_ordered': self.qty_ordered,
            'qty_received': self.qty_received,
            'qty_rejected': self.qty_rejected,
            'unit': self.unit,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<MaterialRequestItem {self.material_name}>'


class MaterialQCSheet(db.Model):
    """Material QC inspection sheet."""
    __tablename__ = 'material_qc_sheets'
    
    id = db.Column(db.Integer, primary_key=True)
    material_request_id = db.Column(db.Integer, db.ForeignKey('material_requests.id'), nullable=False)
    
    # Inspection details
    inspection_code = db.Column(db.String(50), unique=True, nullable=False)
    inspected_at = db.Column(db.DateTime)
    inspector_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Checklist JSON - stores the 4 parameters
    # Structure: [
    #   {
    #     "parameter": "Kesesuaian jumlah material dengan PO/DSO",
    #     "qty_received": 100,
    #     "qty_ng": 5,
    #     "status_accepted": true,
    #     "notes": ""
    #   },
    #   ...
    # ]
    checklist_json = db.Column(db.JSON)
    
    # Results
    result = db.Column(db.String(50), default='pending')
    total_received = db.Column(db.Integer, default=0)
    total_ng = db.Column(db.Integer, default=0)
    
    # Signatures
    sender_name = db.Column(db.String(100))  # Vendor representative
    receiver_name = db.Column(db.String(100))  # QC personnel
    
    # Notes
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inspector = db.relationship('Employee', foreign_keys=[inspector_id])
    
    @staticmethod
    def generate_inspection_code():
        """Generate unique inspection code."""
        today = datetime.now()
        prefix = f"MQC-{today.strftime('%Y%m%d')}"
        last_qc = MaterialQCSheet.query.filter(
            MaterialQCSheet.inspection_code.like(f'{prefix}%')
        ).order_by(MaterialQCSheet.id.desc()).first()
        
        if last_qc:
            last_num = int(last_qc.inspection_code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def get_pass_rate(self):
        """Calculate pass rate percentage."""
        if self.total_received == 0:
            return 0
        return round(((self.total_received - self.total_ng) / self.total_received) * 100, 2)
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'material_request_id': self.material_request_id,
            'inspection_code': self.inspection_code,
            'inspected_at': self.inspected_at.isoformat() if self.inspected_at else None,
            'inspector_id': self.inspector_id,
            'checklist_json': self.checklist_json,
            'result': self.result,
            'total_received': self.total_received,
            'total_ng': self.total_ng,
            'pass_rate': self.get_pass_rate(),
            'sender_name': self.sender_name,
            'receiver_name': self.receiver_name,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<MaterialQCSheet {self.inspection_code}>'


class Material(db.Model):
    """Material inventory/stock model."""
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    
    # Classification
    material_type = db.Column(db.String(100), nullable=False)  # Kain, Benang, Aksesoris, Bahan, etc.
    category = db.Column(db.String(100))  # Sub-category
    
    # Details
    specifications = db.Column(db.Text)
    color = db.Column(db.String(100))
    size = db.Column(db.String(100))
    unit = db.Column(db.String(50), default='pcs')  # pcs, meter, kg, roll, etc.
    
    # Stock
    stock_qty = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=0)  # Minimum stock alert threshold
    
    # Status
    status = db.Column(db.String(50), default='active')  # active, low_stock, out_of_stock, discontinued
    
    # Vendor info
    default_vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    default_vendor = db.relationship('Vendor', foreign_keys=[default_vendor_id])
    
    @staticmethod
    def generate_material_code(material_type):
        """Generate unique material code based on type."""
        today = datetime.now()
        type_prefix = material_type[:3].upper() if material_type else 'MAT'
        prefix = f"{type_prefix}-{today.strftime('%y%m')}"
        last_material = Material.query.filter(
            Material.code.like(f'{prefix}%')
        ).order_by(Material.id.desc()).first()
        
        if last_material:
            last_num = int(last_material.code.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{new_num:04d}"
    
    def update_status(self):
        """Update status based on stock level."""
        if self.stock_qty <= 0:
            self.status = 'out_of_stock'
        elif self.stock_qty <= self.min_stock:
            self.status = 'low_stock'
        else:
            self.status = 'active'
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'material_type': self.material_type,
            'category': self.category,
            'specifications': self.specifications,
            'color': self.color,
            'size': self.size,
            'unit': self.unit,
            'stock_qty': self.stock_qty,
            'min_stock': self.min_stock,
            'status': self.status,
            'default_vendor_id': self.default_vendor_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            data['default_vendor'] = self.default_vendor.to_dict() if self.default_vendor else None
        
        return data
    
    def __repr__(self):
        return f'<Material {self.code} - {self.name}>'
