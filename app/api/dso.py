"""DSO API endpoints."""
from datetime import datetime
from flask import request, g
from flask_login import login_required, current_user
from . import api_bp
from ..models.dso import DSO, DSOImage, DSOAccessory, DSOSize, DSOStatus, DSOSizeChartDewasa, DSOSizeChartAnak
from ..models.order import Order, OrderStatus
from ..models.audit import ChangeRequest, ChangeRequestStatus
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, log_activity
from ..services.storage_service import upload_file, delete_file


@api_bp.route('/dso/<int:dso_id>', methods=['GET'])
@login_required
def get_dso(dso_id):
    """Get DSO by ID with full details."""
    dso = DSO.query.get_or_404(dso_id)
    return api_response(data=dso.to_dict(include_relations=True))


@api_bp.route('/dso/<int:dso_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('dso', 'update')
def update_dso(dso_id):
    """Update DSO details."""
    dso = DSO.query.get_or_404(dso_id)
    data = request.get_json()
    
    # Only allow editing draft or rejected DSOs
    if dso.status not in ['draft', 'rejected']:
        return api_response(message='Cannot edit approved/superseded DSO. Create a change request.', status=400)
    
    # Store before state
    g.data_before = dso.to_dict()
    
    # Update all DSO fields from template
    fields = [
        'jenis', 'bahan', 'warna', 'sablon', 'posisi',
        'acc_1', 'acc_2', 'acc_3', 'acc_4', 'acc_5',
        'kancing', 'saku', 'resleting', 'model_badan_bawah',
        'catatan_customer_1', 'catatan_customer_2', 'catatan_customer_3',
        'catatan_customer_4', 'catatan_customer_5', 'catatan_customer_6',
        'label', 'gambar_depan_url',
        # Legacy fields
        'gramasi', 'jahitan', 'benang', 'label_merk', 'label_size', 
        'label_care', 'hangtag', 'packaging', 'catatan_produksi', 'catatan_customer'
    ]
    
    for field in fields:
        if field in data:
            setattr(dso, field, data[field])
    
    # Handle Size Chart Dewasa
    if 'size_chart_dewasa' in data:
        dewasa_data = data['size_chart_dewasa']
        if dso.size_chart_dewasa:
            chart = dso.size_chart_dewasa
        else:
            chart = DSOSizeChartDewasa(dso_id=dso.id)
            db.session.add(chart)
        
        for key, value in dewasa_data.items():
            if hasattr(chart, key):
                setattr(chart, key, value or 0)
    
    # Handle Size Chart Anak
    if 'size_chart_anak' in data:
        anak_data = data['size_chart_anak']
        if dso.size_chart_anak:
            chart = dso.size_chart_anak
        else:
            chart = DSOSizeChartAnak(dso_id=dso.id)
            db.session.add(chart)
        
        for key, value in anak_data.items():
            if hasattr(chart, key):
                setattr(chart, key, value or 0)
    
    db.session.commit()
    
    g.record_id = dso.id
    g.record_type = 'dso'
    g.data_after = dso.to_dict()
    
    return api_response(data=dso.to_dict(include_relations=True), message='DSO updated successfully')


@api_bp.route('/dso/<int:dso_id>/submit', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('dso', 'submit_for_approval')
def submit_dso_for_approval(dso_id):
    """Submit DSO for approval."""
    dso = DSO.query.get_or_404(dso_id)
    
    if dso.status != 'draft':
        return api_response(message='DSO is not in draft status', status=400)
    
    dso.status = 'pending_approval'
    db.session.commit()
    
    return api_response(data=dso.to_dict(), message='DSO submitted for approval')


@api_bp.route('/dso/<int:dso_id>/approve', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('dso', 'approve')
def approve_dso(dso_id):
    """Approve DSO."""
    dso = DSO.query.get_or_404(dso_id)
    
    if dso.status != 'pending_approval':
        return api_response(message='DSO is not pending approval', status=400)
    
    dso.status = 'approved'
    dso.approved_by = current_user.id
    dso.approved_at = datetime.utcnow()
    
    # Update order status
    order = dso.order
    order.status = 'in_production'
    
    db.session.commit()
    
    return api_response(data=dso.to_dict(), message='DSO approved successfully')


@api_bp.route('/dso/<int:dso_id>/reject', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('dso', 'reject')
def reject_dso(dso_id):
    """Reject DSO."""
    dso = DSO.query.get_or_404(dso_id)
    data = request.get_json()
    
    if dso.status != 'pending_approval':
        return api_response(message='DSO is not pending approval', status=400)
    
    dso.status = 'rejected'
    dso.rejection_reason = data.get('reason', '')
    dso.approved_by = current_user.id
    dso.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    return api_response(data=dso.to_dict(), message='DSO rejected')


@api_bp.route('/dso/<int:dso_id>/new-version', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('dso', 'create_new_version')
def create_dso_new_version(dso_id):
    """Create new version of DSO."""
    dso = DSO.query.get_or_404(dso_id)
    
    new_dso = dso.create_new_version()
    new_dso.created_by = current_user.id
    
    db.session.add(new_dso)
    db.session.commit()
    
    return api_response(data=new_dso.to_dict(), message=f'DSO version {new_dso.version} created', status=201)


# ===== DSO Images =====

@api_bp.route('/dso/<int:dso_id>/images', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('dso_image', 'upload')
def upload_dso_image(dso_id):
    """Upload image for DSO."""
    dso = DSO.query.get_or_404(dso_id)
    
    if 'file' not in request.files:
        return api_response(message='No file provided', status=400)
    
    file = request.files['file']
    image_type = request.form.get('image_type', 'detail')
    
    if file.filename == '':
        return api_response(message='No file selected', status=400)
    
    # Upload to Supabase Storage
    result = upload_file(file, f'dso/{dso.order_id}')
    
    if not result['success']:
        return api_response(message=result.get('error', 'Upload failed'), status=500)
    
    # Create image record
    dso_image = DSOImage(
        dso_id=dso.id,
        image_type=image_type,
        image_url=result['url'],
        sort_order=dso.images.count()
    )
    
    db.session.add(dso_image)
    db.session.commit()
    
    return api_response(data=dso_image.to_dict(), message='Image uploaded successfully', status=201)


@api_bp.route('/dso/<int:dso_id>/images/<int:image_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('dso_image', 'delete')
def delete_dso_image(dso_id, image_id):
    """Delete DSO image."""
    dso_image = DSOImage.query.filter_by(id=image_id, dso_id=dso_id).first_or_404()
    
    # Delete from storage
    if dso_image.image_url:
        delete_file(dso_image.image_url)
    
    db.session.delete(dso_image)
    db.session.commit()
    
    return api_response(message='Image deleted successfully')


@api_bp.route('/dso/<int:dso_id>/images/<int:image_id>/annotations', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI, UserRole.QC_LINE)
@log_activity('dso_image', 'annotate')
def update_dso_image_annotations(dso_id, image_id):
    """Update DSO image annotations (Fabric.js data)."""
    dso_image = DSOImage.query.filter_by(id=image_id, dso_id=dso_id).first_or_404()
    data = request.get_json()
    
    dso_image.annotations_json = data.get('annotations')
    db.session.commit()
    
    return api_response(data=dso_image.to_dict(), message='Annotations saved')


# ===== DSO Accessories =====

@api_bp.route('/dso/<int:dso_id>/accessories', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def add_dso_accessory(dso_id):
    """Add accessory to DSO."""
    dso = DSO.query.get_or_404(dso_id)
    data = request.get_json()
    
    accessory = DSOAccessory(
        dso_id=dso.id,
        name=data.get('name'),
        specification=data.get('specification'),
        qty=data.get('qty'),
        unit=data.get('unit'),
        notes=data.get('notes'),
        sort_order=dso.accessories.count()
    )
    
    db.session.add(accessory)
    db.session.commit()
    
    return api_response(data=accessory.to_dict(), message='Accessory added', status=201)


@api_bp.route('/dso/<int:dso_id>/accessories/<int:acc_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def update_dso_accessory(dso_id, acc_id):
    """Update DSO accessory."""
    accessory = DSOAccessory.query.filter_by(id=acc_id, dso_id=dso_id).first_or_404()
    data = request.get_json()
    
    for field in ['name', 'specification', 'qty', 'unit', 'notes']:
        if field in data:
            setattr(accessory, field, data[field])
    
    db.session.commit()
    
    return api_response(data=accessory.to_dict(), message='Accessory updated')


@api_bp.route('/dso/<int:dso_id>/accessories/<int:acc_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def delete_dso_accessory(dso_id, acc_id):
    """Delete DSO accessory."""
    accessory = DSOAccessory.query.filter_by(id=acc_id, dso_id=dso_id).first_or_404()
    db.session.delete(accessory)
    db.session.commit()
    
    return api_response(message='Accessory deleted')


# ===== DSO Sizes =====

@api_bp.route('/dso/<int:dso_id>/sizes', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def add_dso_size(dso_id):
    """Add size specification to DSO."""
    dso = DSO.query.get_or_404(dso_id)
    data = request.get_json()
    
    size = DSOSize(
        dso_id=dso.id,
        size_label=data.get('size_label'),
        qty=data.get('qty', 0),
        measurements_json=data.get('measurements'),
        notes=data.get('notes'),
        sort_order=dso.sizes.count()
    )
    
    db.session.add(size)
    db.session.commit()
    
    return api_response(data=size.to_dict(), message='Size added', status=201)


@api_bp.route('/dso/<int:dso_id>/sizes/<int:size_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def update_dso_size(dso_id, size_id):
    """Update DSO size."""
    size = DSOSize.query.filter_by(id=size_id, dso_id=dso_id).first_or_404()
    data = request.get_json()
    
    for field in ['size_label', 'qty', 'measurements_json', 'notes']:
        if field in data:
            setattr(size, field, data[field])
    
    db.session.commit()
    
    return api_response(data=size.to_dict(), message='Size updated')


@api_bp.route('/dso/<int:dso_id>/sizes/<int:size_id>', methods=['DELETE'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def delete_dso_size(dso_id, size_id):
    """Delete DSO size."""
    size = DSOSize.query.filter_by(id=size_id, dso_id=dso_id).first_or_404()
    db.session.delete(size)
    db.session.commit()
    
    return api_response(message='Size deleted')


# ===== Change Requests =====

@api_bp.route('/dso/<int:dso_id>/change-request', methods=['POST'])
@login_required
@log_activity('change_request', 'create')
def create_change_request(dso_id):
    """Create change request for approved DSO."""
    dso = DSO.query.get_or_404(dso_id)
    data = request.get_json()
    
    if dso.status != 'approved':
        return api_response(message='Can only create change request for approved DSO', status=400)
    
    cr = ChangeRequest(
        dso_id=dso.id,
        request_code=ChangeRequest.generate_request_code(),
        reason=data.get('reason'),
        description=data.get('description'),
        priority=data.get('priority', 1),
        changes_json=data.get('changes'),
        affects_production=data.get('affects_production', False),
        production_impact=data.get('production_impact'),
        requested_by=current_user.id
    )
    
    db.session.add(cr)
    db.session.commit()
    
    return api_response(data=cr.to_dict(), message='Change request created', status=201)


@api_bp.route('/change-requests/<int:cr_id>/approve', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('change_request', 'approve')
def approve_change_request(cr_id):
    """Approve change request and create new DSO version."""
    cr = ChangeRequest.query.get_or_404(cr_id)
    data = request.get_json()
    
    if cr.status != ChangeRequestStatus.PENDING:
        return api_response(message='Change request is not pending', status=400)
    
    # Approve the request
    cr.approve(current_user.id, data.get('notes'))
    
    # Create new DSO version
    new_dso = cr.dso.create_new_version()
    new_dso.created_by = current_user.id
    db.session.add(new_dso)
    db.session.flush()
    
    # Mark as implemented
    cr.implement(new_dso.id)
    
    db.session.commit()
    
    return api_response(
        data={'change_request': cr.to_dict(), 'new_dso': new_dso.to_dict()},
        message='Change request approved and new DSO version created'
    )


@api_bp.route('/change-requests/<int:cr_id>/reject', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER)
@log_activity('change_request', 'reject')
def reject_change_request(cr_id):
    """Reject change request."""
    cr = ChangeRequest.query.get_or_404(cr_id)
    data = request.get_json()
    
    if cr.status != ChangeRequestStatus.PENDING:
        return api_response(message='Change request is not pending', status=400)
    
    cr.reject(current_user.id, data.get('notes'))
    db.session.commit()
    
    return api_response(data=cr.to_dict(), message='Change request rejected')
