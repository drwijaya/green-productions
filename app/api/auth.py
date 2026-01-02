"""Authentication API endpoints."""
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, current_user
)
from flask_login import login_user, logout_user, current_user as flask_current_user
from . import api_bp
from ..models.user import User
from ..models.audit import ActivityLog
from ..extensions import db
from ..utils.decorators import api_response


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    
    if not data:
        return api_response(message='No data provided', status=400)
    
    email = data.get('email') or data.get('username')
    password = data.get('password')
    
    if not email or not password:
        return api_response(message='Email/username and password required', status=400)
    
    # Find user by email or username
    user = User.query.filter(
        (User.email == email) | (User.username == email)
    ).first()
    
    if not user or not user.check_password(password):
        return api_response(message='Invalid credentials', status=401)
    
    if not user.is_active:
        return api_response(message='Account is deactivated', status=401)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    
    # Flask-Login session
    login_user(user)
    
    # Log activity
    log = ActivityLog(
        user_id=user.id,
        module='auth',
        action='login',
        description=f'User {user.username} logged in',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return api_response(
        data={
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        },
        message='Login successful'
    )


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required(optional=True)
def logout():
    """User logout endpoint."""
    if flask_current_user.is_authenticated:
        # Log activity
        log = ActivityLog(
            user_id=flask_current_user.id,
            module='auth',
            action='logout',
            description=f'User {flask_current_user.username} logged out',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        logout_user()
    
    return api_response(message='Logout successful')


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user = current_user
    if not user:
        return api_response(message='User not found', status=404)
    
    return api_response(data=user.to_dict())


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token."""
    identity = get_jwt_identity()
    user = User.query.get(identity)
    
    if not user or not user.is_active:
        return api_response(message='Invalid user', status=401)
    
    access_token = create_access_token(identity=user)
    
    return api_response(data={'access_token': access_token})


@api_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    data = request.get_json()
    user = current_user
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return api_response(message='Current and new password required', status=400)
    
    if not user.check_password(current_password):
        return api_response(message='Current password is incorrect', status=400)
    
    if len(new_password) < 8:
        return api_response(message='Password must be at least 8 characters', status=400)
    
    user.set_password(new_password)
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=user.id,
        module='auth',
        action='change_password',
        description='Password changed',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return api_response(message='Password changed successfully')
