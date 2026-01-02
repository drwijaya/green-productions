"""Utility decorators for RBAC and logging."""
from functools import wraps
from flask import request, jsonify, g
from flask_login import current_user
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models.user import UserRole
from ..models.audit import ActivityLog
from ..extensions import db


def require_roles(*roles):
    """Decorator to require specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                try:
                    verify_jwt_in_request()
                except:
                    return jsonify({'error': 'Authentication required'}), 401
            
            user = current_user if current_user.is_authenticated else None
            if user is None:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Convert roles to string values for comparison
            allowed_role_values = []
            for role in roles:
                if hasattr(role, 'value'):
                    allowed_role_values.append(role.value)
                else:
                    allowed_role_values.append(role)
            
            # Check if user has required role (user.role is now a string)
            if user.role not in allowed_role_values:
                return jsonify({
                    'error': 'Access denied',
                    'message': f'Required roles: {allowed_role_values}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(permission):
    """Decorator to require specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not current_user.can_access(permission):
                return jsonify({
                    'error': 'Access denied',
                    'message': f'Permission required: {permission}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_activity(module, action):
    """Decorator to log user activity."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store data before action for comparison
            g.data_before = None
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log the activity
            try:
                user_id = current_user.id if current_user.is_authenticated else None
                
                log = ActivityLog(
                    user_id=user_id,
                    module=module,
                    action=action,
                    record_id=getattr(g, 'record_id', None),
                    record_type=getattr(g, 'record_type', None),
                    data_before=getattr(g, 'data_before', None),
                    data_after=getattr(g, 'data_after', None),
                    description=getattr(g, 'log_description', None),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string[:500] if request.user_agent else None
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                # Don't fail the request if logging fails
                print(f"Activity logging error: {e}")
            
            return result
        return decorated_function
    return decorator


def api_response(data=None, message=None, status=200, errors=None):
    """Standard API response format."""
    response = {
        'success': status < 400,
        'status': status
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status


def paginate_query(query, page=1, per_page=20, max_per_page=100):
    """Paginate a SQLAlchemy query."""
    per_page = min(per_page, max_per_page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'items': pagination.items,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
