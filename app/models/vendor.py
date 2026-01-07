"""Vendor model for supplier management."""
from datetime import datetime
from ..extensions import db


class Vendor(db.Model):
    """Vendor/Supplier model for material procurement."""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    
    # Status: active, inactive
    status = db.Column(db.String(20), default='active')
    
    # Notes and additional info
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    material_requests = db.relationship('MaterialRequest', backref='vendor', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    @staticmethod
    def generate_vendor_code():
        """Generate unique vendor code."""
        last_vendor = Vendor.query.order_by(Vendor.id.desc()).first()
        if last_vendor:
            new_num = last_vendor.id + 1
        else:
            new_num = 1
        return f"VND-{new_num:04d}"
    
    def to_dict(self):
        """Convert vendor to dictionary for API response."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Vendor {self.code} - {self.name}>'
