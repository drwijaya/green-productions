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
    import traceback
    try:
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
    except Exception as e:
        print(f"LOGIN ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


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
    from datetime import datetime, timedelta
    from ..models.material import MaterialRequest

    from ..models.qc import QCSheet
    
    # Get stats
    total_orders = Order.query.count()
    active_orders = Order.query.filter(Order.status.in_(['in_production', 'qc_pending'])).count()
    
    # Pending QC - count production tasks that need QC inspection
    pending_qc_tasks = ProductionTask.query.filter(
        ProductionTask.status.in_(['in_progress', 'completed'])
    ).outerjoin(QCSheet).filter(QCSheet.id == None).count()
    
    # Additional stats
    total_customers = Customer.query.count()
    total_employees = Employee.query.filter_by(is_active=True).count()
    
    # Pending material requests - use correct status values
    pending_materials = MaterialRequest.query.filter(
        MaterialRequest.status.in_(['requested', 'in_transit', 'arrived', 'qc_pending'])
    ).count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Production orders with details - include orders with in_progress or assigned tasks
    production_orders = Order.query.filter(
        Order.status.in_(['in_production', 'draft', 'qc_pending'])
    ).join(ProductionTask).filter(
        ProductionTask.status.in_(['pending', 'assigned', 'in_progress'])
    ).distinct().order_by(Order.deadline.asc().nullslast()).limit(5).all()
    
    # Calculate production progress for each order
    for order in production_orders:
        total_tasks = order.production_tasks.count()
        completed_tasks = order.production_tasks.filter(
            ProductionTask.status == 'completed'
        ).count()
        order.progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    

    
    # Calculate Quality Score from QC Analytics Service
    from ..services.qc_analytics import QCAnalyticsService
    quality_data = QCAnalyticsService.calculate_quality_score()
    quality_score = quality_data['quality_score']
    
    return render_template('dashboard/index.html',
        total_orders=total_orders,
        active_orders=active_orders,
        pending_qc=pending_qc_tasks,
        total_customers=total_customers,
        total_employees=total_employees,
        pending_materials=pending_materials,
        recent_orders=recent_orders,
        production_orders=production_orders,

        now=datetime.now().date(),
        quality_score=quality_score
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
    """Order detail page by ID."""
    order = Order.query.get_or_404(order_id)
    dsos = order.dso.order_by(DSO.version.desc()).all()
    tasks = order.production_tasks.order_by(ProductionTask.sequence).all()
    return render_template('orders/detail.html', order=order, dsos=dsos, tasks=tasks)


@views_bp.route('/orders/<order_code>')
@login_required
def order_detail_by_code(order_code):
    """Order detail page by order code (human-readable URL)."""
    order = Order.query.filter_by(order_code=order_code).first_or_404()
    dsos = order.dso.order_by(DSO.version.desc()).all()
    tasks = order.production_tasks.order_by(ProductionTask.sequence).all()
    return render_template('orders/detail.html', order=order, dsos=dsos, tasks=tasks)


@views_bp.route('/dso/<int:dso_id>')
@login_required
def dso_detail(dso_id):
    """DSO detail/edit page by ID."""
    dso = DSO.query.get_or_404(dso_id)
    return render_template('dso/detail.html', dso=dso)


@views_bp.route('/dso/<order_code>/<int:version>')
@login_required
def dso_detail_by_code(order_code, version):
    """DSO detail/edit page by order code and version."""
    # Find order by order_code
    order = Order.query.filter_by(order_code=order_code).first_or_404()
    # Find DSO by order and version
    dso = DSO.query.filter_by(order_id=order.id, version=version).first_or_404()
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
    from sqlalchemy.orm import joinedload
    from ..models.production import ProductionTask, ProductionWorkerLog
    from ..models.qc import QCSheet
    
    # Only show active orders (not completed) for faster loading
    # User can filter to see completed orders if needed
    show_completed = request.args.get('show_completed', 'false') == 'true'
    
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
    
    # Filter statuses based on show_completed parameter
    if show_completed:
        status_filter = ['draft', 'in_production', 'qc_pending', 'completed']
    else:
        status_filter = ['draft', 'in_production', 'qc_pending']
    
    # Load orders with customer - limit to 50 for faster loading
    orders = Order.query.options(
        joinedload(Order.customer)
    ).filter(
        Order.status.in_(status_filter)
    ).order_by(status_order, Order.deadline.asc()).limit(50).all()
    
    # Pre-fetch all data in efficient separate queries
    order_ids = [o.id for o in orders]
    tasks_by_order = {}
    
    if order_ids:
        # Get tasks with supervisor
        all_tasks = ProductionTask.query.options(
            joinedload(ProductionTask.supervisor)
        ).filter(
            ProductionTask.order_id.in_(order_ids)
        ).order_by(ProductionTask.order_id, ProductionTask.sequence).all()
        
        task_ids = [t.id for t in all_tasks]
        
        # Fetch worker logs separately with employees
        worker_logs_by_task = {}
        if task_ids:
            all_worker_logs = ProductionWorkerLog.query.options(
                joinedload(ProductionWorkerLog.employee)
            ).filter(ProductionWorkerLog.task_id.in_(task_ids)).all()
            for log in all_worker_logs:
                if log.task_id not in worker_logs_by_task:
                    worker_logs_by_task[log.task_id] = []
                worker_logs_by_task[log.task_id].append(log)
        
        # Fetch QC sheets separately
        qc_sheets_by_task = {}
        if task_ids:
            all_qc_sheets = QCSheet.query.filter(QCSheet.production_task_id.in_(task_ids)).all()
            for sheet in all_qc_sheets:
                if sheet.production_task_id not in qc_sheets_by_task:
                    qc_sheets_by_task[sheet.production_task_id] = []
                qc_sheets_by_task[sheet.production_task_id].append(sheet)
        
        # Group tasks by order_id and attach prefetched data
        for task in all_tasks:
            task._prefetched_worker_logs = worker_logs_by_task.get(task.id, [])
            task._prefetched_qc_sheets = qc_sheets_by_task.get(task.id, [])
            if task.order_id not in tasks_by_order:
                tasks_by_order[task.order_id] = []
            tasks_by_order[task.order_id].append(task)
    
    # Attach tasks to orders
    for order in orders:
        order._prefetched_tasks = tasks_by_order.get(order.id, [])
    
    return render_template('production/timeline.html', orders=orders, now=date.today(), show_completed=show_completed)



@views_bp.route('/production/qc')
@login_required
def qc_list():
    """QC Reports page - integrated into Production."""
    # QC is now optional - page loads reports via JavaScript
    return render_template('qc/list.html')


@views_bp.route('/production/qc/<int:task_id>')
@login_required
def qc_inspect(task_id):
    """QC inspection/checklist page for a task by ID."""
    import traceback
    try:
        from datetime import datetime
        task = ProductionTask.query.get_or_404(task_id)
        
        # Get assigned workers for this task
        workers = task.worker_logs.all()
        operator_names = [log.employee.name for log in workers if log.employee] if workers else []
        
        return render_template('qc/inspect.html', 
                               task=task, 
                               now=datetime.now(),
                               operator_names=operator_names)
    except Exception as e:
        print(f"QC_INSPECT ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@views_bp.route('/production/qc/<order_code>/<process>')
@login_required
def qc_inspect_by_code(order_code, process):
    """QC inspection/checklist page by order code and process (station)."""
    import traceback
    try:
        from datetime import datetime
        
        # Find order by order_code  
        order = Order.query.filter_by(order_code=order_code).first_or_404()
        
        # Find production task by order and process
        task = ProductionTask.query.filter_by(
            order_id=order.id, 
            process=process.lower()
        ).first_or_404()
        
        # Get assigned workers for this task
        workers = task.worker_logs.all()
        operator_names = [log.employee.name for log in workers if log.employee] if workers else []
        
        return render_template('qc/inspect.html', 
                               task=task, 
                               now=datetime.now(),
                               operator_names=operator_names)
    except Exception as e:
        print(f"QC_INSPECT_BY_CODE ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


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


@views_bp.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Customer detail page with order history."""
    customer = Customer.query.get_or_404(customer_id)
    
    # Get all orders for this customer
    page = request.args.get('page', 1, type=int)
    orders = customer.orders.order_by(Order.created_at.desc()).paginate(page=page, per_page=15)
    
    # Stats
    total_orders = customer.orders.count()
    completed_orders = customer.orders.filter(Order.status == 'completed').count()
    in_production = customer.orders.filter(Order.status == 'in_production').count()
    
    return render_template('admin/customer_detail.html', 
        customer=customer, 
        orders=orders,
        total_orders=total_orders,
        completed_orders=completed_orders,
        in_production=in_production
    )


@views_bp.route('/employees')
@login_required
def employees():
    """Employees list."""
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.order_by(Employee.name).paginate(page=page, per_page=20)
    return render_template('admin/employees.html', employees=employees)


@views_bp.route('/employees/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    """Employee detail page with work history."""
    from ..models.production import ProductionTask, ProductionWorkerLog
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Get supervised tasks
    supervised_tasks = ProductionTask.query.filter_by(
        line_supervisor_id=employee_id
    ).order_by(ProductionTask.created_at.desc()).limit(50).all()
    
    # Get worker logs
    worker_logs = ProductionWorkerLog.query.filter_by(
        employee_id=employee_id
    ).order_by(ProductionWorkerLog.created_at.desc()).limit(50).all()
    
    # Stats
    total_supervised = len(supervised_tasks)
    total_contributions = len(worker_logs)
    total_qty_done = sum(log.qty_completed for log in worker_logs)
    
    return render_template('admin/employee_detail.html',
        employee=employee,
        supervised_tasks=supervised_tasks,
        worker_logs=worker_logs,
        total_supervised=total_supervised,
        total_contributions=total_contributions,
        total_qty_done=total_qty_done
    )


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


# Scanner Routes
@views_bp.route('/scan')
@login_required
def scanner():
    """QR Code scanner page."""
    return render_template('scan/index.html')


@views_bp.route('/scan/result/<order_code>')
@login_required
def scanner_result(order_code):
    """Scanner result page - shows menu options for scanned invoice."""
    order = Order.query.filter_by(order_code=order_code).first()
    
    if not order:
        flash(f'Invoice {order_code} tidak ditemukan', 'error')
        return redirect(url_for('views.scanner'))
    
    return render_template('scan/result.html', order=order)

