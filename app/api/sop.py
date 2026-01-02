"""SOP API endpoints."""
from datetime import datetime
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.sop import SOPDocument, SOPAcknowledgment
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, paginate_query, log_activity
from ..services.storage_service import upload_file


@api_bp.route('/sop', methods=['GET'])
@login_required
def list_sop_documents():
    """List SOP documents."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = SOPDocument.query
    
    if category:
        query = query.filter(SOPDocument.category == category)
    if active_only:
        query = query.filter(SOPDocument.is_active == True)
    
    query = query.order_by(SOPDocument.title.asc())
    result = paginate_query(query, page, per_page)
    
    return api_response(data={
        'documents': [d.to_dict(include_stats=True) for d in result['items']],
        'pagination': result['pagination']
    })


@api_bp.route('/sop/<int:sop_id>', methods=['GET'])
@login_required
def get_sop_document(sop_id):
    """Get SOP document by ID."""
    sop = SOPDocument.query.get_or_404(sop_id)
    data = sop.to_dict(include_stats=True)
    data['is_acknowledged'] = sop.is_acknowledged_by(current_user.id)
    return api_response(data=data)


@api_bp.route('/sop', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('sop', 'create')
def create_sop_document():
    """Create SOP document."""
    data = request.get_json()
    
    if not data.get('title'):
        return api_response(message='Title required', status=400)
    
    # Generate document code
    count = SOPDocument.query.count() + 1
    doc_code = f"SOP-{datetime.now().strftime('%Y')}-{count:04d}"
    
    sop = SOPDocument(
        title=data['title'],
        document_code=doc_code,
        category=data.get('category'),
        version=data.get('version', '1.0'),
        revision_number=data.get('revision_number', 0),
        description=data.get('description'),
        is_active=data.get('is_active', True),
        created_by=current_user.id
    )
    
    if data.get('effective_date'):
        sop.effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d')
    if data.get('revision_date'):
        sop.revision_date = datetime.strptime(data['revision_date'], '%Y-%m-%d')
    
    db.session.add(sop)
    db.session.commit()
    
    return api_response(data=sop.to_dict(), message='SOP created', status=201)


@api_bp.route('/sop/<int:sop_id>', methods=['PUT'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
@log_activity('sop', 'update')
def update_sop_document(sop_id):
    """Update SOP document."""
    sop = SOPDocument.query.get_or_404(sop_id)
    data = request.get_json()
    
    if 'title' in data:
        sop.title = data['title']
    if 'category' in data:
        sop.category = data['category']
    if 'version' in data:
        sop.version = data['version']
    if 'revision_number' in data:
        sop.revision_number = data['revision_number']
    if 'revision_date' in data:
        sop.revision_date = datetime.strptime(data['revision_date'], '%Y-%m-%d') if data['revision_date'] else None
    if 'effective_date' in data:
        sop.effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d') if data['effective_date'] else None
    if 'description' in data:
        sop.description = data['description']
    if 'is_active' in data:
        sop.is_active = data['is_active']
    
    db.session.commit()
    return api_response(data=sop.to_dict(), message='SOP updated')


@api_bp.route('/sop/<int:sop_id>/upload', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def upload_sop_file(sop_id):
    """Upload SOP file."""
    sop = SOPDocument.query.get_or_404(sop_id)
    
    if 'file' not in request.files:
        return api_response(message='No file provided', status=400)
    
    file = request.files['file']
    result = upload_file(file, 'sop')
    
    if not result['success']:
        return api_response(message='Upload failed', status=500)
    
    sop.file_url = result['url']
    sop.file_type = file.filename.rsplit('.', 1)[-1].lower()
    db.session.commit()
    
    return api_response(data=sop.to_dict(), message='File uploaded')


@api_bp.route('/sop/<int:sop_id>/acknowledge', methods=['POST'])
@login_required
@log_activity('sop', 'acknowledge')
def acknowledge_sop(sop_id):
    """Acknowledge SOP document."""
    sop = SOPDocument.query.get_or_404(sop_id)
    
    # Check if already acknowledged
    existing = SOPAcknowledgment.query.filter_by(
        sop_id=sop_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        return api_response(message='Already acknowledged')
    
    ack = SOPAcknowledgment(
        sop_id=sop_id,
        user_id=current_user.id,
        version_acknowledged=sop.version,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:500] if request.user_agent else None
    )
    
    db.session.add(ack)
    db.session.commit()
    
    return api_response(data=ack.to_dict(), message='SOP acknowledged', status=201)


@api_bp.route('/sop/<int:sop_id>/acknowledgments', methods=['GET'])
@login_required
def get_sop_acknowledgments(sop_id):
    """Get SOP acknowledgments."""
    sop = SOPDocument.query.get_or_404(sop_id)
    acks = sop.acknowledgments.order_by(SOPAcknowledgment.acknowledged_at.desc()).all()
    return api_response(data=[a.to_dict() for a in acks])


@api_bp.route('/sop/categories', methods=['GET'])
@login_required
def get_sop_categories():
    """Get SOP categories."""
    categories = db.session.query(SOPDocument.category).distinct().all()
    return api_response(data=[c[0] for c in categories if c[0]])
