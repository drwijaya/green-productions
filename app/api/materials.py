"""Material Request API endpoints."""
from flask import request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from . import api_bp
from ..extensions import db
from ..models import MaterialRequest, MaterialRequestItem, MaterialQCSheet, Vendor, Material


@api_bp.route('/materials', methods=['GET'])
@login_required
def get_material_requests():
    """Get all material requests with optional filters."""
    status = request.args.get('status')
    vendor_id = request.args.get('vendor_id')
    search = request.args.get('search', '')
    
    query = MaterialRequest.query
    
    if status:
        query = query.filter_by(status=status)
    
    if vendor_id:
        query = query.filter_by(vendor_id=vendor_id)
    
    if search:
        query = query.filter(
            db.or_(
                MaterialRequest.request_code.ilike(f'%{search}%')
            )
        )
    
    requests = query.order_by(MaterialRequest.created_at.desc()).all()
    
    return jsonify({
        'material_requests': [r.to_dict(include_relations=True) for r in requests],
        'total': len(requests)
    })


@api_bp.route('/materials', methods=['POST'])
@login_required
def create_material_request():
    """Create a new material request."""
    data = request.get_json()
    
    if not data.get('vendor_id'):
        return jsonify({'error': 'Vendor wajib dipilih'}), 400
    
    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'Minimal harus ada 1 item material'}), 400
    
    # Verify vendor exists
    vendor = Vendor.query.get(data['vendor_id'])
    if not vendor:
        return jsonify({'error': 'Vendor tidak ditemukan'}), 404
    
    # Create material request
    material_request = MaterialRequest(
        request_code=MaterialRequest.generate_request_code(),
        vendor_id=data['vendor_id'],
        order_id=data.get('order_id'),
        status='requested',
        expected_arrival=datetime.strptime(data['expected_arrival'], '%Y-%m-%d').date() if data.get('expected_arrival') else None,
        notes=data.get('notes'),
        created_by=current_user.id
    )
    
    db.session.add(material_request)
    db.session.flush()  # Get the ID
    
    # Add items
    for item_data in data['items']:
        item = MaterialRequestItem(
            material_request_id=material_request.id,
            material_name=item_data['material_name'],
            material_type=item_data.get('material_type'),
            specifications=item_data.get('specifications'),
            color=item_data.get('color'),
            size=item_data.get('size'),
            qty_ordered=item_data['qty_ordered'],
            unit=item_data.get('unit', 'pcs'),
            notes=item_data.get('notes')
        )
        db.session.add(item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Material request berhasil dibuat',
        'material_request': material_request.to_dict(include_relations=True)
    }), 201


@api_bp.route('/materials/<int:request_id>', methods=['GET'])
@login_required
def get_material_request(request_id):
    """Get material request by ID."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    return jsonify(material_request.to_dict(include_relations=True))


@api_bp.route('/materials/<int:request_id>', methods=['PUT'])
@login_required
def update_material_request(request_id):
    """Update material request."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    data = request.get_json()
    
    if 'vendor_id' in data:
        material_request.vendor_id = data['vendor_id']
    if 'order_id' in data:
        material_request.order_id = data['order_id']
    if 'expected_arrival' in data:
        material_request.expected_arrival = datetime.strptime(data['expected_arrival'], '%Y-%m-%d').date() if data['expected_arrival'] else None
    if 'notes' in data:
        material_request.notes = data['notes']
    
    # Update items if provided
    if 'items' in data:
        # Delete existing items
        MaterialRequestItem.query.filter_by(material_request_id=material_request.id).delete()
        
        # Add new items
        for item_data in data['items']:
            item = MaterialRequestItem(
                material_request_id=material_request.id,
                material_name=item_data['material_name'],
                material_type=item_data.get('material_type'),
                specifications=item_data.get('specifications'),
                color=item_data.get('color'),
                size=item_data.get('size'),
                qty_ordered=item_data['qty_ordered'],
                unit=item_data.get('unit', 'pcs'),
                notes=item_data.get('notes')
            )
            db.session.add(item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Material request berhasil diupdate',
        'material_request': material_request.to_dict(include_relations=True)
    })


@api_bp.route('/materials/<int:request_id>/status', methods=['PUT'])
@login_required
def update_material_status(request_id):
    """Update material request status."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    data = request.get_json()
    
    new_status = data.get('status')
    valid_statuses = ['requested', 'in_transit', 'arrived', 'qc_pending', 'qc_passed', 'qc_failed', 'stored', 'cancelled']
    
    if new_status not in valid_statuses:
        return jsonify({'error': f'Status tidak valid. Status yang tersedia: {", ".join(valid_statuses)}'}), 400
    
    material_request.status = new_status
    
    # Set actual arrival when status becomes arrived
    if new_status == 'arrived' and not material_request.actual_arrival:
        material_request.actual_arrival = datetime.utcnow()
    
    # Add to inventory when stored
    if new_status == 'stored' and material_request.qc_sheet and material_request.qc_sheet.result != 'fail':
        for item in material_request.items:
            # Try to find existing material by name and type
            # Note: In a real system, you might want stricter matching or explicit linking
            existing_material = Material.query.filter(
                Material.name.ilike(item.material_name),
                Material.material_type == item.material_type
            ).first()
            
            qty_to_store = item.qty_received if item.qty_received > 0 else item.qty_ordered
            
            if existing_material:
                # Update existing stock
                existing_material.stock_qty += qty_to_store
                existing_material.update_status()
            else:
                # Create new material
                new_material = Material(
                    code=Material.generate_material_code(item.material_type),
                    name=item.material_name,
                    material_type=item.material_type or 'Lainnya',
                    specifications=item.specifications,
                    color=item.color,
                    size=item.size,
                    unit=item.unit,
                    stock_qty=qty_to_store,
                    min_stock=10,  # Default min stock
                    default_vendor_id=material_request.vendor_id,
                    notes=f"Auto-created from MR {material_request.request_code}"
                )
                new_material.update_status()
                db.session.add(new_material)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Status berhasil diubah ke {new_status}',
        'material_request': material_request.to_dict(include_relations=True)
    })


@api_bp.route('/materials/<int:request_id>', methods=['DELETE'])
@login_required
def delete_material_request(request_id):
    """Delete material request."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    
    # Only allow deletion if status is requested or cancelled
    if material_request.status not in ['requested', 'cancelled']:
        return jsonify({
            'error': 'Hanya material request dengan status "requested" atau "cancelled" yang dapat dihapus'
        }), 400
    
    db.session.delete(material_request)
    db.session.commit()
    
    return jsonify({'message': 'Material request berhasil dihapus'})


# Material QC Endpoints
@api_bp.route('/materials/<int:request_id>/qc', methods=['GET'])
@login_required
def get_material_qc(request_id):
    """Get material QC sheet."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    
    if material_request.qc_sheet:
        return jsonify(material_request.qc_sheet.to_dict())
    else:
        return jsonify({'message': 'QC sheet belum dibuat', 'qc_sheet': None})


@api_bp.route('/materials/<int:request_id>/qc', methods=['POST'])
@login_required
def create_or_update_material_qc(request_id):
    """Create or update material QC sheet."""
    material_request = MaterialRequest.query.get_or_404(request_id)
    data = request.get_json()
    
    if material_request.qc_sheet:
        # Update existing
        qc_sheet = material_request.qc_sheet
    else:
        # Create new
        qc_sheet = MaterialQCSheet(
            material_request_id=request_id,
            inspection_code=MaterialQCSheet.generate_inspection_code()
        )
        db.session.add(qc_sheet)
    
    # Update QC sheet data
    qc_sheet.checklist_json = data.get('checklist_json')
    qc_sheet.result = data.get('result', 'pending')
    qc_sheet.total_received = data.get('total_received', 0)
    qc_sheet.total_ng = data.get('total_ng', 0)
    qc_sheet.sender_name = data.get('sender_name')
    qc_sheet.receiver_name = data.get('receiver_name')
    qc_sheet.notes = data.get('notes')
    qc_sheet.inspected_at = datetime.utcnow()
    
    # Update material request status based on QC result
    if qc_sheet.result == 'pass':
        material_request.status = 'qc_passed'
    elif qc_sheet.result == 'fail':
        material_request.status = 'qc_failed'
    elif qc_sheet.result == 'conditional_pass':
        material_request.status = 'qc_passed'  # Still passed but with conditions
    
    # Update item quantities if provided
    if 'item_quantities' in data:
        for item_data in data['item_quantities']:
            item = MaterialRequestItem.query.get(item_data['id'])
            if item and item.material_request_id == request_id:
                item.qty_received = item_data.get('qty_received', 0)
                item.qty_rejected = item_data.get('qty_rejected', 0)
    
    db.session.commit()
    
    return jsonify({
        'message': 'QC checklist berhasil disimpan',
        'qc_sheet': qc_sheet.to_dict(),
        'material_request': material_request.to_dict(include_relations=True)
    })


# Material Inventory Endpoints
@api_bp.route('/inventory', methods=['GET'])
@login_required
def get_materials_inventory():
    """Get all materials in inventory with optional filters."""
    material_type = request.args.get('material_type')
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    query = Material.query
    
    if material_type:
        query = query.filter_by(material_type=material_type)
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            db.or_(
                Material.name.ilike(f'%{search}%'),
                Material.code.ilike(f'%{search}%'),
                Material.color.ilike(f'%{search}%')
            )
        )
    
    materials = query.order_by(Material.name).all()
    
    # Get unique material types for filter dropdown
    material_types = db.session.query(Material.material_type).distinct().all()
    types_list = [t[0] for t in material_types if t[0]]
    
    return jsonify({
        'materials': [m.to_dict(include_relations=True) for m in materials],
        'total': len(materials),
        'material_types': types_list
    })


@api_bp.route('/inventory', methods=['POST'])
@login_required
def create_material():
    """Create a new material in inventory."""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Nama material wajib diisi'}), 400
    
    if not data.get('material_type'):
        return jsonify({'error': 'Jenis material wajib diisi'}), 400
    
    material = Material(
        code=Material.generate_material_code(data['material_type']),
        name=data['name'],
        material_type=data['material_type'],
        category=data.get('category'),
        specifications=data.get('specifications'),
        color=data.get('color'),
        size=data.get('size'),
        unit=data.get('unit', 'pcs'),
        stock_qty=data.get('stock_qty', 0),
        min_stock=data.get('min_stock', 0),
        default_vendor_id=data.get('default_vendor_id'),
        notes=data.get('notes')
    )
    
    material.update_status()
    
    db.session.add(material)
    db.session.commit()
    
    return jsonify({
        'message': 'Material berhasil ditambahkan',
        'material': material.to_dict()
    }), 201


@api_bp.route('/inventory/<int:material_id>', methods=['GET'])
@login_required
def get_material(material_id):
    """Get material by ID."""
    material = Material.query.get_or_404(material_id)
    return jsonify(material.to_dict(include_relations=True))


@api_bp.route('/inventory/<int:material_id>', methods=['PUT'])
@login_required
def update_material(material_id):
    """Update material."""
    material = Material.query.get_or_404(material_id)
    data = request.get_json()
    
    if 'name' in data:
        material.name = data['name']
    if 'material_type' in data:
        material.material_type = data['material_type']
    if 'category' in data:
        material.category = data['category']
    if 'specifications' in data:
        material.specifications = data['specifications']
    if 'color' in data:
        material.color = data['color']
    if 'size' in data:
        material.size = data['size']
    if 'unit' in data:
        material.unit = data['unit']
    if 'stock_qty' in data:
        material.stock_qty = data['stock_qty']
    if 'min_stock' in data:
        material.min_stock = data['min_stock']
    if 'default_vendor_id' in data:
        material.default_vendor_id = data['default_vendor_id']
    if 'notes' in data:
        material.notes = data['notes']
    
    material.update_status()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Material berhasil diupdate',
        'material': material.to_dict(include_relations=True)
    })


@api_bp.route('/inventory/<int:material_id>', methods=['DELETE'])
@login_required
def delete_material(material_id):
    """Delete material."""
    material = Material.query.get_or_404(material_id)
    
    db.session.delete(material)
    db.session.commit()
    
    return jsonify({'message': 'Material berhasil dihapus'})


@api_bp.route('/inventory/<int:material_id>/stock', methods=['PUT'])
@login_required
def update_material_stock(material_id):
    """Update material stock quantity."""
    material = Material.query.get_or_404(material_id)
    data = request.get_json()
    
    adjustment = data.get('adjustment', 0)
    reason = data.get('reason', '')
    
    material.stock_qty += adjustment
    if material.stock_qty < 0:
        material.stock_qty = 0
    
    material.update_status()
    
    db.session.commit()
    
    return jsonify({
        'message': f'Stok berhasil di{"tambah" if adjustment > 0 else "kurang"} - {reason}',
        'material': material.to_dict()
    })
