"""Barcode models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class BarcodeType(Enum):
    """Barcode type enum."""
    ORDER = 'order'
    TASK = 'task'
    ITEM = 'item'
    BATCH = 'batch'
    QC_CHECKLIST = 'qc_checklist'


class Barcode(db.Model):
    """Barcode for tracking orders and tasks."""
    __tablename__ = 'barcode'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    barcode_value = db.Column(db.String(100), unique=True, nullable=False, index=True)
    barcode_type = db.Column(db.Enum(BarcodeType), nullable=False)
    
    # Additional reference
    reference_id = db.Column(db.Integer)  # Can reference task_id, item_id, etc.
    reference_type = db.Column(db.String(50))  # 'production_task', 'qc_sheet', etc.
    
    # Barcode image URL (stored in Supabase Storage)
    image_url = db.Column(db.String(500))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('BarcodeEvent', backref='barcode', lazy='dynamic')
    
    @staticmethod
    def generate_barcode_value(barcode_type, reference_id):
        """Generate unique barcode value."""
        today = datetime.now()
        prefix_map = {
            BarcodeType.ORDER: 'ORD',
            BarcodeType.TASK: 'TSK',
            BarcodeType.ITEM: 'ITM',
            BarcodeType.BATCH: 'BTH'
        }
        prefix = prefix_map.get(barcode_type, 'GEN')
        timestamp = today.strftime('%y%m%d%H%M')
        return f"{prefix}{timestamp}{reference_id:05d}"
    
    def get_last_event(self):
        """Get the most recent barcode event."""
        return self.events.order_by(BarcodeEvent.scanned_at.desc()).first()
    
    def to_dict(self, include_events=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'barcode_value': self.barcode_value,
            'barcode_type': self.barcode_type.value,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_events:
            last_event = self.get_last_event()
            data['last_event'] = last_event.to_dict() if last_event else None
            data['events'] = [e.to_dict() for e in self.events.order_by(BarcodeEvent.scanned_at.desc()).limit(10).all()]
        
        return data
    
    def __repr__(self):
        return f'<Barcode {self.barcode_value}>'


class BarcodeEvent(db.Model):
    """Barcode scan events for tracking."""
    __tablename__ = 'barcode_event'
    
    id = db.Column(db.Integer, primary_key=True)
    barcode_id = db.Column(db.Integer, db.ForeignKey('barcode.id'), nullable=False)
    
    event_type = db.Column(db.String(50), nullable=False)  # 'scan', 'start', 'complete', 'qc_check', etc.
    
    # Scanner info
    scanned_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Location/Station
    location = db.Column(db.String(100))
    station = db.Column(db.String(100))
    
    # Additional data
    data_json = db.Column(db.JSON)  # Any additional event data
    
    scanner = db.relationship('Employee', foreign_keys=[scanned_by])
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'barcode_id': self.barcode_id,
            'event_type': self.event_type,
            'scanned_by': self.scanned_by,
            'scanner_name': self.scanner.name if self.scanner else None,
            'scanned_at': self.scanned_at.isoformat() if self.scanned_at else None,
            'location': self.location,
            'station': self.station,
            'data_json': self.data_json
        }
    
    def __repr__(self):
        return f'<BarcodeEvent {self.event_type} at {self.scanned_at}>'
