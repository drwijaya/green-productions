"""Barcode API endpoints."""
from datetime import datetime
from flask import request
from flask_login import login_required, current_user
from . import api_bp
from ..models.barcode import Barcode, BarcodeEvent, BarcodeType
from ..models.production import ProductionTask
from ..models.order import Order
from ..models.employee import Employee
from ..models.user import UserRole
from ..extensions import db
from ..utils.decorators import require_roles, api_response, log_activity
from ..services.barcode_service import generate_barcode_image, generate_qr_code_base64


@api_bp.route('/barcodes/qc-qrcode/<int:order_id>', methods=['GET'])
@login_required
def get_qc_qrcode(order_id):
    """Generate QR code for Invoice.
    
    Returns a base64-encoded QR code image that can be embedded directly in HTML.
    The QR code contains the order_code (e.g., INV-202601-0001)
    """
    order = Order.query.get_or_404(order_id)
    
    # Generate QR code data - use order_code for human-readable scanning
    qr_data = order.order_code
    
    # Generate base64 QR code
    qr_base64 = generate_qr_code_base64(qr_data, size=6)
    
    if not qr_base64:
        return api_response(message='Failed to generate QR code', status=500)
    
    return api_response(data={
        'order_id': order_id,
        'order_code': order.order_code,
        'qr_data': qr_data,
        'qr_image': qr_base64
    })


@api_bp.route('/barcodes', methods=['GET'])
@login_required
def list_barcodes():
    """List barcodes with filters."""
    order_id = request.args.get('order_id', type=int)
    barcode_type = request.args.get('type')
    
    query = Barcode.query
    
    if order_id:
        query = query.filter(Barcode.order_id == order_id)
    if barcode_type:
        try:
            query = query.filter(Barcode.barcode_type == BarcodeType(barcode_type))
        except ValueError:
            pass
    
    barcodes = query.order_by(Barcode.created_at.desc()).all()
    return api_response(data=[b.to_dict(include_events=True) for b in barcodes])


@api_bp.route('/barcodes/<int:barcode_id>', methods=['GET'])
@login_required
def get_barcode(barcode_id):
    """Get barcode by ID."""
    barcode = Barcode.query.get_or_404(barcode_id)
    return api_response(data=barcode.to_dict(include_events=True))


@api_bp.route('/barcodes/generate', methods=['POST'])
@login_required
@require_roles(UserRole.ADMIN, UserRole.OWNER, UserRole.ADMIN_PRODUKSI)
def generate_barcode():
    """Generate new barcode."""
    data = request.get_json()
    
    order_id = data.get('order_id')
    barcode_type = data.get('type', 'order')
    reference_id = data.get('reference_id')
    
    if not order_id:
        return api_response(message='Order ID required', status=400)
    
    try:
        bt = BarcodeType(barcode_type)
    except ValueError:
        return api_response(message='Invalid barcode type', status=400)
    
    barcode_value = Barcode.generate_barcode_value(bt, reference_id or order_id)
    
    barcode = Barcode(
        order_id=order_id,
        barcode_value=barcode_value,
        barcode_type=bt,
        reference_id=reference_id,
        reference_type=data.get('reference_type')
    )
    
    db.session.add(barcode)
    db.session.commit()
    
    # Generate barcode image
    image_url = generate_barcode_image(barcode_value, barcode.id)
    if image_url:
        barcode.image_url = image_url
        db.session.commit()
    
    return api_response(data=barcode.to_dict(), message='Barcode generated', status=201)


@api_bp.route('/barcodes/scan', methods=['POST'])
@login_required
@log_activity('barcode', 'scan')
def scan_barcode():
    """Process scanned barcode."""
    data = request.get_json()
    barcode_value = data.get('barcode_value')
    
    if not barcode_value:
        return api_response(message='Barcode value required', status=400)
    
    barcode = Barcode.query.filter_by(barcode_value=barcode_value).first()
    if not barcode:
        return api_response(message='Barcode not found', status=404)
    
    if not barcode.is_active:
        return api_response(message='Barcode is inactive', status=400)
    
    # Get employee
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    # Create scan event
    event = BarcodeEvent(
        barcode_id=barcode.id,
        event_type=data.get('event_type', 'scan'),
        scanned_by=employee.id if employee else None,
        location=data.get('location'),
        station=data.get('station'),
        data_json=data.get('extra_data')
    )
    
    db.session.add(event)
    db.session.commit()
    
    # Get related data
    response_data = barcode.to_dict(include_events=True)
    
    if barcode.barcode_type == BarcodeType.ORDER:
        order = Order.query.get(barcode.order_id)
        if order:
            response_data['order'] = order.to_dict()
    
    if barcode.barcode_type == BarcodeType.TASK and barcode.reference_id:
        task = ProductionTask.query.get(barcode.reference_id)
        if task:
            response_data['task'] = task.to_dict()
    
    return api_response(data=response_data, message='Barcode scanned successfully')


@api_bp.route('/barcodes/<int:barcode_id>/events', methods=['GET'])
@login_required
def get_barcode_events(barcode_id):
    """Get barcode scan history."""
    barcode = Barcode.query.get_or_404(barcode_id)
    events = barcode.events.order_by(BarcodeEvent.scanned_at.desc()).all()
    return api_response(data=[e.to_dict() for e in events])


@api_bp.route('/barcodes/lookup/<barcode_value>', methods=['GET'])
@login_required
def lookup_barcode(barcode_value):
    """Lookup barcode by value."""
    barcode = Barcode.query.filter_by(barcode_value=barcode_value).first()
    if not barcode:
        return api_response(message='Barcode not found', status=404)
    return api_response(data=barcode.to_dict(include_events=True))
