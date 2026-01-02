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


@views_bp.route('/production')
@login_required
def production():
    """Production timeline page."""
    from datetime import date
    # Get orders with active production (draft or in production)
    orders = Order.query.filter(
        Order.status.in_(['draft', 'in_production'])
    ).order_by(Order.deadline.asc()).all()
    return render_template('production/timeline.html', orders=orders, now=date.today())


@views_bp.route('/qc')
@login_required
def qc_list():
    """QC Reports page - optional quality documentation."""
    # QC is now optional - page loads reports via JavaScript
    return render_template('qc/list.html')


@views_bp.route('/qc/<int:task_id>')
@login_required
def qc_inspect(task_id):
    """QC inspection/checklist page for a task."""
    from datetime import datetime
    task = ProductionTask.query.get_or_404(task_id)
    return render_template('qc/inspect.html', task=task, now=datetime.now())


@views_bp.route('/qc/inspect/<int:sheet_id>')
@login_required
def qc_sheet_detail(sheet_id):
    """View existing QC sheet detail."""
    sheet = QCSheet.query.get_or_404(sheet_id)
    return render_template('qc/sheet_detail.html', sheet=sheet)


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
    if current_user.role != UserRole.ADMIN:
        flash('Access denied', 'error')
        return redirect(url_for('views.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


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
