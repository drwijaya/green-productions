"""Vendor API endpoints."""
from flask import request, jsonify
from flask_login import login_required, current_user
from . import api_bp
from ..extensions import db
from ..models import Vendor


@api_bp.route('/vendors', methods=['GET'])
@login_required
def get_vendors():
    """Get all vendors with optional filters."""
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    query = Vendor.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            db.or_(
                Vendor.name.ilike(f'%{search}%'),
                Vendor.code.ilike(f'%{search}%'),
                Vendor.contact_person.ilike(f'%{search}%')
            )
        )
    
    vendors = query.order_by(Vendor.name).all()
    
    return jsonify({
        'vendors': [v.to_dict() for v in vendors],
        'total': len(vendors)
    })


@api_bp.route('/vendors', methods=['POST'])
@login_required
def create_vendor():
    """Create a new vendor."""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Nama vendor wajib diisi'}), 400
    
    vendor = Vendor(
        code=Vendor.generate_vendor_code(),
        name=data['name'],
        contact_person=data.get('contact_person'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        city=data.get('city'),
        status=data.get('status', 'active'),
        notes=data.get('notes'),
        created_by=current_user.id
    )
    
    db.session.add(vendor)
    db.session.commit()
    
    return jsonify({
        'message': 'Vendor berhasil dibuat',
        'vendor': vendor.to_dict()
    }), 201


@api_bp.route('/vendors/<int:vendor_id>', methods=['GET'])
@login_required
def get_vendor(vendor_id):
    """Get vendor by ID."""
    vendor = Vendor.query.get_or_404(vendor_id)
    return jsonify(vendor.to_dict())


@api_bp.route('/vendors/<int:vendor_id>', methods=['PUT'])
@login_required
def update_vendor(vendor_id):
    """Update vendor."""
    vendor = Vendor.query.get_or_404(vendor_id)
    data = request.get_json()
    
    if 'name' in data:
        vendor.name = data['name']
    if 'contact_person' in data:
        vendor.contact_person = data['contact_person']
    if 'phone' in data:
        vendor.phone = data['phone']
    if 'email' in data:
        vendor.email = data['email']
    if 'address' in data:
        vendor.address = data['address']
    if 'city' in data:
        vendor.city = data['city']
    if 'status' in data:
        vendor.status = data['status']
    if 'notes' in data:
        vendor.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Vendor berhasil diupdate',
        'vendor': vendor.to_dict()
    })


@api_bp.route('/vendors/<int:vendor_id>', methods=['DELETE'])
@login_required
def delete_vendor(vendor_id):
    """Delete vendor."""
    vendor = Vendor.query.get_or_404(vendor_id)
    
    # Check if vendor has material requests
    if vendor.material_requests.count() > 0:
        return jsonify({
            'error': 'Tidak dapat menghapus vendor yang memiliki material request'
        }), 400
    
    db.session.delete(vendor)
    db.session.commit()
    
    return jsonify({'message': 'Vendor berhasil dihapus'})
