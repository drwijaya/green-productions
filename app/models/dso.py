"""DSO (Digital Standard Operation) models."""
from enum import Enum
from datetime import datetime
from ..extensions import db


class DSOStatus(Enum):
    """DSO approval status."""
    DRAFT = 'draft'
    PENDING_APPROVAL = 'pending_approval'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    SUPERSEDED = 'superseded'


class DSO(db.Model):
    """Digital Standard Operation document."""
    __tablename__ = 'dso'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    version = db.Column(db.Integer, default=1)
    
    # Product Information (matches template layout)
    jenis = db.Column(db.String(200))       # JENIS
    bahan = db.Column(db.String(200))       # BAHAN
    warna = db.Column(db.String(100))       # WARNA
    sablon = db.Column(db.String(200))      # SABLON
    posisi = db.Column(db.String(200))      # POSISI (sablon position)
    
    # Accessories (ACC 1-5)
    acc_1 = db.Column(db.String(200))
    acc_2 = db.Column(db.String(200))
    acc_3 = db.Column(db.String(200))
    acc_4 = db.Column(db.String(200))
    acc_5 = db.Column(db.String(200))
    
    # Components
    kancing = db.Column(db.String(100))        # KANCING
    saku = db.Column(db.String(100))           # SAKU
    resleting = db.Column(db.String(100))      # RESLETING
    model_badan_bawah = db.Column(db.String(200))  # MODEL BADAN BAWAH
    
    # Image
    gambar_depan_url = db.Column(db.String(500))  # TAMPAK DEPAN image
    
    # Customer Notes (6 rows as per template)
    catatan_customer_1 = db.Column(db.String(500))
    catatan_customer_2 = db.Column(db.String(500))
    catatan_customer_3 = db.Column(db.String(500))
    catatan_customer_4 = db.Column(db.String(500))
    catatan_customer_5 = db.Column(db.String(500))
    catatan_customer_6 = db.Column(db.String(500))
    
    # Label
    label = db.Column(db.String(500))          # LABEL
    
    # Legacy fields (kept for compatibility)
    gramasi = db.Column(db.String(50))
    jahitan = db.Column(db.String(200))
    benang = db.Column(db.String(100))
    label_merk = db.Column(db.String(100))
    label_size = db.Column(db.String(100))
    label_care = db.Column(db.String(100))
    hangtag = db.Column(db.String(100))
    packaging = db.Column(db.Text)
    catatan_produksi = db.Column(db.Text)
    catatan_customer = db.Column(db.Text)  # Legacy single field
    
    # Approval
    status = db.Column(db.String(50), default='draft')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('DSOImage', backref='dso', lazy='dynamic', cascade='all, delete-orphan')
    accessories = db.relationship('DSOAccessory', backref='dso', lazy='dynamic', cascade='all, delete-orphan')
    sizes = db.relationship('DSOSize', backref='dso', lazy='dynamic', cascade='all, delete-orphan')
    approver = db.relationship('User', foreign_keys=[approved_by])
    creator = db.relationship('User', foreign_keys=[created_by])
    change_requests = db.relationship('ChangeRequest', foreign_keys='ChangeRequest.dso_id', backref='dso', lazy='dynamic')
    
    def create_new_version(self):
        """Create a new version of this DSO."""
        new_dso = DSO(
            order_id=self.order_id,
            version=self.version + 1,
            bahan=self.bahan,
            warna=self.warna,
            gramasi=self.gramasi,
            jahitan=self.jahitan,
            benang=self.benang,
            kancing=self.kancing,
            resleting=self.resleting,
            label_merk=self.label_merk,
            label_size=self.label_size,
            label_care=self.label_care,
            hangtag=self.hangtag,
            packaging=self.packaging,
            catatan_produksi=self.catatan_produksi,
            catatan_customer=self.catatan_customer,
            status='draft'
        )
        
        # Mark current version as superseded
        self.status = 'superseded'
        
        return new_dso
    
    def to_dict(self, include_relations=False):
        """Convert DSO to dictionary for API response."""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'version': self.version,
            # Template fields
            'jenis': self.jenis,
            'bahan': self.bahan,
            'warna': self.warna,
            'sablon': self.sablon,
            'posisi': self.posisi,
            'acc_1': self.acc_1,
            'acc_2': self.acc_2,
            'acc_3': self.acc_3,
            'acc_4': self.acc_4,
            'acc_5': self.acc_5,
            'kancing': self.kancing,
            'saku': self.saku,
            'resleting': self.resleting,
            'model_badan_bawah': self.model_badan_bawah,
            'gambar_depan_url': self.gambar_depan_url,
            'catatan_customer_1': self.catatan_customer_1,
            'catatan_customer_2': self.catatan_customer_2,
            'catatan_customer_3': self.catatan_customer_3,
            'catatan_customer_4': self.catatan_customer_4,
            'catatan_customer_5': self.catatan_customer_5,
            'catatan_customer_6': self.catatan_customer_6,
            'label': self.label,
            # Legacy fields
            'gramasi': self.gramasi,
            'jahitan': self.jahitan,
            'benang': self.benang,
            'label_merk': self.label_merk,
            'label_size': self.label_size,
            'label_care': self.label_care,
            'hangtag': self.hangtag,
            'packaging': self.packaging,
            'catatan_produksi': self.catatan_produksi,
            'catatan_customer': self.catatan_customer,
            'status': self.status,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_relations:
            data['images'] = [img.to_dict() for img in self.images.all()]
            data['accessories'] = [acc.to_dict() for acc in self.accessories.all()]
            data['sizes'] = [size.to_dict() for size in self.sizes.all()]
            data['size_chart_dewasa'] = self.size_chart_dewasa.to_dict() if self.size_chart_dewasa else None
            data['size_chart_anak'] = self.size_chart_anak.to_dict() if self.size_chart_anak else None
        
        
        return data
    
    def __repr__(self):
        return f'<DSO Order:{self.order_id} v{self.version}>'


class DSOImage(db.Model):
    """DSO images with annotations."""
    __tablename__ = 'dso_images'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False)
    
    image_type = db.Column(db.String(50), nullable=False)  # depan, belakang, label, detail
    image_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    
    # Fabric.js annotation data
    annotations_json = db.Column(db.JSON)
    
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'dso_id': self.dso_id,
            'image_type': self.image_type,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'annotations_json': self.annotations_json,
            'sort_order': self.sort_order
        }
    
    def __repr__(self):
        return f'<DSOImage {self.image_type}>'


class DSOAccessory(db.Model):
    """DSO accessories list (ACC)."""
    __tablename__ = 'dso_accessories'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False)
    
    name = db.Column(db.String(200), nullable=False)
    specification = db.Column(db.String(200))
    qty = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'dso_id': self.dso_id,
            'name': self.name,
            'specification': self.specification,
            'qty': self.qty,
            'unit': self.unit,
            'notes': self.notes,
            'sort_order': self.sort_order
        }
    
    def __repr__(self):
        return f'<DSOAccessory {self.name}>'


class DSOSize(db.Model):
    """DSO size specifications."""
    __tablename__ = 'dso_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False)
    
    size_label = db.Column(db.String(20), nullable=False)  # S, M, L, XL, etc.
    qty = db.Column(db.Integer, default=0)
    
    # Measurements in JSON format
    measurements_json = db.Column(db.JSON)
    # Example: {"panjang": 70, "lebar": 55, "lengan": 60, "leher": 40}
    
    notes = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'dso_id': self.dso_id,
            'size_label': self.size_label,
            'qty': self.qty,
            'measurements_json': self.measurements_json,
            'notes': self.notes,
            'sort_order': self.sort_order
        }
    
    def __repr__(self):
        return f'<DSOSize {self.size_label}>'


class DSOSizeChartDewasa(db.Model):
    """Adult size chart - matches S.Chart Dewasa in template."""
    __tablename__ = 'dso_size_chart_dewasa'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False, unique=True)
    
    # Pendek row (XS to X5L)
    pendek_xs = db.Column(db.Integer, default=0)
    pendek_s = db.Column(db.Integer, default=0)
    pendek_m = db.Column(db.Integer, default=0)
    pendek_l = db.Column(db.Integer, default=0)
    pendek_xl = db.Column(db.Integer, default=0)
    pendek_xxl = db.Column(db.Integer, default=0)
    pendek_x3l = db.Column(db.Integer, default=0)
    pendek_x4l = db.Column(db.Integer, default=0)
    pendek_x5l = db.Column(db.Integer, default=0)
    
    # Panjang row (XS to X5L)
    panjang_xs = db.Column(db.Integer, default=0)
    panjang_s = db.Column(db.Integer, default=0)
    panjang_m = db.Column(db.Integer, default=0)
    panjang_l = db.Column(db.Integer, default=0)
    panjang_xl = db.Column(db.Integer, default=0)
    panjang_xxl = db.Column(db.Integer, default=0)
    panjang_x3l = db.Column(db.Integer, default=0)
    panjang_x4l = db.Column(db.Integer, default=0)
    panjang_x5l = db.Column(db.Integer, default=0)
    
    # Relationship
    dso = db.relationship('DSO', backref=db.backref('size_chart_dewasa', uselist=False))
    
    @property
    def jum_pendek(self):
        """Calculate JUM for Pendek row."""
        return sum([
            self.pendek_xs or 0, self.pendek_s or 0, self.pendek_m or 0,
            self.pendek_l or 0, self.pendek_xl or 0, self.pendek_xxl or 0,
            self.pendek_x3l or 0, self.pendek_x4l or 0, self.pendek_x5l or 0
        ])
    
    @property
    def jum_panjang(self):
        """Calculate JUM for Panjang row."""
        return sum([
            self.panjang_xs or 0, self.panjang_s or 0, self.panjang_m or 0,
            self.panjang_l or 0, self.panjang_xl or 0, self.panjang_xxl or 0,
            self.panjang_x3l or 0, self.panjang_x4l or 0, self.panjang_x5l or 0
        ])
    
    @property
    def total(self):
        """Calculate TOTAL (sum of both JUMs)."""
        return self.jum_pendek + self.jum_panjang
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'dso_id': self.dso_id,
            'pendek': {
                'xs': self.pendek_xs, 's': self.pendek_s, 'm': self.pendek_m,
                'l': self.pendek_l, 'xl': self.pendek_xl, 'xxl': self.pendek_xxl,
                'x3l': self.pendek_x3l, 'x4l': self.pendek_x4l, 'x5l': self.pendek_x5l,
                'jum': self.jum_pendek
            },
            'panjang': {
                'xs': self.panjang_xs, 's': self.panjang_s, 'm': self.panjang_m,
                'l': self.panjang_l, 'xl': self.panjang_xl, 'xxl': self.panjang_xxl,
                'x3l': self.panjang_x3l, 'x4l': self.panjang_x4l, 'x5l': self.panjang_x5l,
                'jum': self.jum_panjang
            },
            'total': self.total
        }


class DSOSizeChartAnak(db.Model):
    """Children size chart - matches S.Chart Anak in template."""
    __tablename__ = 'dso_size_chart_anak'
    
    id = db.Column(db.Integer, primary_key=True)
    dso_id = db.Column(db.Integer, db.ForeignKey('dso.id'), nullable=False, unique=True)
    
    # Pendek row (XS to X5L)
    pendek_xs = db.Column(db.Integer, default=0)
    pendek_s = db.Column(db.Integer, default=0)
    pendek_m = db.Column(db.Integer, default=0)
    pendek_l = db.Column(db.Integer, default=0)
    pendek_xl = db.Column(db.Integer, default=0)
    pendek_xxl = db.Column(db.Integer, default=0)
    pendek_x3l = db.Column(db.Integer, default=0)
    pendek_x4l = db.Column(db.Integer, default=0)
    pendek_x5l = db.Column(db.Integer, default=0)
    
    # Panjang row (XS to X5L)
    panjang_xs = db.Column(db.Integer, default=0)
    panjang_s = db.Column(db.Integer, default=0)
    panjang_m = db.Column(db.Integer, default=0)
    panjang_l = db.Column(db.Integer, default=0)
    panjang_xl = db.Column(db.Integer, default=0)
    panjang_xxl = db.Column(db.Integer, default=0)
    panjang_x3l = db.Column(db.Integer, default=0)
    panjang_x4l = db.Column(db.Integer, default=0)
    panjang_x5l = db.Column(db.Integer, default=0)
    
    # Relationship
    dso = db.relationship('DSO', backref=db.backref('size_chart_anak', uselist=False))
    
    @property
    def jum_pendek(self):
        """Calculate JUM for Pendek row."""
        return sum([
            self.pendek_xs or 0, self.pendek_s or 0, self.pendek_m or 0,
            self.pendek_l or 0, self.pendek_xl or 0, self.pendek_xxl or 0,
            self.pendek_x3l or 0, self.pendek_x4l or 0, self.pendek_x5l or 0
        ])
    
    @property
    def jum_panjang(self):
        """Calculate JUM for Panjang row."""
        return sum([
            self.panjang_xs or 0, self.panjang_s or 0, self.panjang_m or 0,
            self.panjang_l or 0, self.panjang_xl or 0, self.panjang_xxl or 0,
            self.panjang_x3l or 0, self.panjang_x4l or 0, self.panjang_x5l or 0
        ])
    
    @property
    def total(self):
        """Calculate TOTAL (sum of both JUMs)."""
        return self.jum_pendek + self.jum_panjang
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'dso_id': self.dso_id,
            'pendek': {
                'xs': self.pendek_xs, 's': self.pendek_s, 'm': self.pendek_m,
                'l': self.pendek_l, 'xl': self.pendek_xl, 'xxl': self.pendek_xxl,
                'x3l': self.pendek_x3l, 'x4l': self.pendek_x4l, 'x5l': self.pendek_x5l,
                'jum': self.jum_pendek
            },
            'panjang': {
                'xs': self.panjang_xs, 's': self.panjang_s, 'm': self.panjang_m,
                'l': self.panjang_l, 'xl': self.panjang_xl, 'xxl': self.panjang_xxl,
                'x3l': self.panjang_x3l, 'x4l': self.panjang_x4l, 'x5l': self.panjang_x5l,
                'jum': self.jum_panjang
            },
            'total': self.total
        }

