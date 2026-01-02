"""SOP Document models."""
from datetime import datetime
from ..extensions import db


class SOPDocument(db.Model):
    """SOP document with version control."""
    __tablename__ = 'sop_document'
    
    id = db.Column(db.Integer, primary_key=True)
    
    title = db.Column(db.String(200), nullable=False)
    document_code = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(100))  # e.g., 'Produksi', 'QC', 'Safety'
    
    version = db.Column(db.String(20), default='1.0')
    revision_number = db.Column(db.Integer, default=0)  # No. Revisi
    revision_date = db.Column(db.Date)  # Tanggal Revisi
    description = db.Column(db.Text)
    
    # File storage
    file_url = db.Column(db.String(500))
    file_type = db.Column(db.String(20))  # 'pdf', 'doc', etc.
    file_size = db.Column(db.Integer)  # bytes
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    effective_date = db.Column(db.Date)  # Berlaku Efektif
    review_date = db.Column(db.Date)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    acknowledgments = db.relationship('SOPAcknowledgment', backref='sop', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def get_acknowledgment_count(self):
        """Get total acknowledgment count."""
        return self.acknowledgments.count()
    
    def is_acknowledged_by(self, user_id):
        """Check if SOP is acknowledged by a specific user."""
        return self.acknowledgments.filter_by(user_id=user_id).first() is not None
    
    def to_dict(self, include_stats=False):
        """Convert to dictionary for API response."""
        data = {
            'id': self.id,
            'title': self.title,
            'document_code': self.document_code,
            'category': self.category,
            'version': self.version,
            'revision_number': self.revision_number,
            'revision_date': self.revision_date.isoformat() if self.revision_date else None,
            'description': self.description,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'is_active': self.is_active,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_stats:
            data['acknowledgment_count'] = self.get_acknowledgment_count()
        
        return data
    
    def __repr__(self):
        return f'<SOPDocument {self.document_code}>'


class SOPAcknowledgment(db.Model):
    """SOP acknowledgment by users."""
    __tablename__ = 'sop_acknowledgment'
    
    id = db.Column(db.Integer, primary_key=True)
    sop_id = db.Column(db.Integer, db.ForeignKey('sop_document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    version_acknowledged = db.Column(db.String(20))  # Track which version was acknowledged
    
    # Device/Location info
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    user = db.relationship('User', foreign_keys=[user_id])
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            'id': self.id,
            'sop_id': self.sop_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'version_acknowledged': self.version_acknowledged
        }
    
    def __repr__(self):
        return f'<SOPAcknowledgment SOP:{self.sop_id} User:{self.user_id}>'
