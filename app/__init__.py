"""Flask application factory."""
import os
from flask import Flask
from .config import config
from .extensions import db, migrate, jwt, login_manager, csrf, cors, init_supabase


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize Supabase
    with app.app_context():
        init_supabase()
    
    # Configure login manager
    login_manager.login_view = 'views.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'warning'
    
    # Register blueprints
    from .api import api_bp
    from .views import views_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp)
    
    # JWT callbacks
    from .models.user import User
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id if hasattr(user, 'id') else user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.get(identity)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables - skip if connection fails (for healthcheck compatibility)
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created/verified successfully.")
        except Exception as e:
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Set')
            db_host = db_url.split('@')[-1] if '@' in db_url else '***'
            print(f"\n{'='*50}")
            print(f"WARNING: Could not connect to the database on startup.")
            print(f"Database Host: {db_host}")
            print(f"Error: {str(e)}")
            print(f"The app will continue - database operations may fail.")
            print(f"{'='*50}\n")
            # Don't raise - let the app start for health checks
    
    return app
