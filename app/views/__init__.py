"""Views blueprint for frontend pages."""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from ..models.user import User, UserRole
from ..models.order import Order, OrderStatus
from ..models.dso import DSO
from ..models.production import ProductionTask, TaskStatus
from ..models.qc import QCSheet
from ..models.customer import Customer
from ..models.employee import Employee
from ..extensions import db

views_bp = Blueprint('views', __name__)


@views_bp.route('/health')
def health_check():
    """Health check endpoint for Railway/deployment platforms."""
    try:
        # Try a simple DB query
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)[:50]}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status
    }), 200


@views_bp.route('/')
def index():
    """Landing page - redirect to dashboard or login."""
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return redirect(url_for('views.login'))


@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter(
            (User.email == email) | (User.username == email)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('views.dashboard'))
        
        flash('Email atau password salah', 'error')
    
    return render_template('auth/login.html')


@views_bp.route('/logout')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('views.login'))


@views_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard."""
    # Get stats
    total_orders = Order.query.count()
    active_orders = Order.query.filter(Order.status.in_(['in_production', 'qc_pending'])).count()
    pending_qc = Order.query.filter_by(status='qc_pending').count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html',
        total_orders=total_orders,
        active_orders=active_orders,
        pending_qc=pending_qc,
        recent_orders=recent_orders
    )


@views_bp.route('/orders')
@login_required
def orders():
    """Orders list page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', type=int)
    
    query = Order.query
    
    if search:
        query = query.filter(
            (Order.order_code.ilike(f'%{search}%')) |
            (Order.model.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Order.status == status)
    
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20)
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('orders/list.html', orders=orders, customers=customers)


@views_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail page."""
    order = Order.query.get_or_404(order_id)
    dsos = order.dso.order_by(DSO.version.desc()).all()
    tasks = order.production_tasks.order_by(ProductionTask.sequence).all()
    return render_template('orders/detail.html', order=order, dsos=dsos, tasks=tasks)


@views_bp.route('/dso/<int:dso_id>')
@login_required
def dso_detail(dso_id):
    """DSO detail/edit page."""
    dso = DSO.query.get_or_404(dso_id)
    return render_template('dso/detail.html', dso=dso)


@views_bp.route('/dso')
@login_required
def dso_management():
    """DSO Management page - view all DSOs by status."""
    # Get counts for each status
    from sqlalchemy import func
    
    not_created_count = Order.query.filter_by(dso_status='not_created').count()
    draft_count = Order.query.filter_by(dso_status='draft').count()
    created_count = Order.query.filter_by(dso_status='created').count()
    
    return render_template('dso/management.html',
        not_created_count=not_created_count,
        draft_count=draft_count,
        created_count=created_count
    )


@views_bp.route('/production')
@login_required
def production():
    """Production timeline page."""
    from datetime import date
    from sqlalchemy import case
    # Get orders with production history (draft, in_production, qc_pending, or completed)
    # Rank statuses: in_production (1), qc_pending (2), draft (3), completed (4)
    status_order = case(
        {
            'in_production': 1,
            'qc_pending': 2,
            'draft': 3,
            'completed': 4
        },
        value=Order.status,
        else_=5
    )
    
    orders = Order.query.filter(
        Order.status.in_(['draft', 'in_production', 'qc_pending', 'completed'])
    ).order_by(status_order, Order.deadline.asc()).all()
    return render_template('production/timeline.html', orders=orders, now=date.today())


@views_bp.route('/production/qc')
@login_required
def qc_list():
    """QC Reports page - integrated into Production."""
    # QC is now optional - page loads reports via JavaScript
    return render_template('qc/list.html')


@views_bp.route('/production/qc/<int:task_id>')
@login_required
def qc_inspect(task_id):
    """QC inspection/checklist page for a task."""
    from datetime import datetime
    task = ProductionTask.query.get_or_404(task_id)
    
    # Get assigned workers for this task
    workers = task.worker_logs.all()
    operator_names = [log.employee.name for log in workers if log.employee] if workers else []
    
    return render_template('qc/inspect.html', 
                           task=task, 
                           now=datetime.now(),
                           operator_names=operator_names)


@views_bp.route('/production/qc/inspect/<int:sheet_id>')
@login_required
def qc_sheet_detail(sheet_id):
    """View existing QC sheet detail."""
    sheet = QCSheet.query.get_or_404(sheet_id)
    return render_template('qc/sheet_detail.html', sheet=sheet)


@views_bp.route('/qc/monitoring')
@login_required
def qc_monitoring():
    """QC Monitoring Dashboard."""
    return render_template('qc/monitoring.html')


@views_bp.route('/customers')
@login_required
def customers():
    """Customers list."""
    page = request.args.get('page', 1, type=int)
    customers = Customer.query.order_by(Customer.name).paginate(page=page, per_page=20)
    return render_template('admin/customers.html', customers=customers)


@views_bp.route('/employees')
@login_required
def employees():
    """Employees list."""
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.order_by(Employee.name).paginate(page=page, per_page=20)
    return render_template('admin/employees.html', employees=employees)


@views_bp.route('/users')
@login_required
def users():
    """Users management - Admin only."""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('views.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@views_bp.route('/admin/users/<int:user_id>/permissions')
@login_required
def user_permissions(user_id):
    """Manage permissions for a specific user."""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('views.dashboard'))
    
    user = User.query.get_or_404(user_id)
    return render_template('admin/permissions.html', user=user)


@views_bp.route('/reports')
@login_required
def reports():
    """Reports page - list of orders for generating reports."""
    return render_template('reports/index.html')


@views_bp.route('/reports/<int:order_id>')
@login_required
def invoice_report(order_id):
    """Comprehensive invoice report for a specific order."""
    from ..models.order import Order
    order = Order.query.get_or_404(order_id)
    return render_template('reports/invoice_report.html', order=order)


@views_bp.route('/barcode')
@login_required
def barcode_center():
    """Barcode center."""
    return render_template('barcode/center.html')


@views_bp.route('/sop')
@login_required
def sop_list():
    """SOP documents list."""
    from ..models.sop import SOPDocument
    page = request.args.get('page', 1, type=int)
    documents = SOPDocument.query.filter_by(is_active=True).order_by(SOPDocument.title).paginate(page=page, per_page=20)
    return render_template('sop/list.html', documents=documents)


@views_bp.route('/sop/<int:sop_id>/view')
@login_required
def sop_view(sop_id):
    """View SOP document (inline)."""
    from ..models.sop import SOPDocument
    from ..services.storage_service import create_signed_url
    from flask import send_from_directory, current_app
    import os
    
    sop = SOPDocument.query.get_or_404(sop_id)
    
    if not sop.file_url:
        flash('Dokumen tidak memiliki file', 'warning')
        return redirect(url_for('views.sop_list'))
    
    # Check if remote URL
    if sop.file_url.startswith('http'):
        # Try to get a signed URL for secure access
        signed_url = create_signed_url(sop.file_url)
        if signed_url:
            return redirect(signed_url)
        return redirect(sop.file_url)
    
    # Serve local file
    if sop.file_url.startswith('/static/'):
        # Extract relative path from /static/
        # e.g. /static/uploads/sop/file.pdf -> uploads/sop/file.pdf
        rel_path = sop.file_url.replace('/static/', '', 1)
        return send_from_directory(
            os.path.join(current_app.root_path, 'static'),
            rel_path,
            as_attachment=False  # Encode as inline to view in browser
        )
        
    return redirect(sop.file_url)


# Materials Management Routes
@views_bp.route('/materials')
@login_required
def materials_list():
    """Materials list page."""
    return render_template('materials/list.html')


@views_bp.route('/materials/new')
@login_required
def materials_new():
    """Create new material request."""
    return render_template('materials/form.html', material_request=None)


@views_bp.route('/materials/<int:request_id>')
@login_required
def materials_detail(request_id):
    """Material request detail page."""
    from ..models.material import MaterialRequest
    material_request = MaterialRequest.query.get_or_404(request_id)
    return render_template('materials/detail.html', material_request=material_request)


@views_bp.route('/materials/<int:request_id>/edit')
@login_required
def materials_edit(request_id):
    """Edit material request."""
    from ..models.material import MaterialRequest
    material_request = MaterialRequest.query.get_or_404(request_id)
    return render_template('materials/form.html', material_request=material_request)


@views_bp.route('/materials/<int:request_id>/qc')
@login_required
def materials_qc(request_id):
    """Material QC checklist page."""
    from datetime import datetime
    from ..models.material import MaterialRequest
    material_request = MaterialRequest.query.get_or_404(request_id)
    return render_template('materials/qc.html', material_request=material_request, now=datetime.now())


# Vendors Management Routes
@views_bp.route('/vendors')
@login_required
def vendors_list():
    """Vendors list page."""
    return render_template('vendors/list.html')
