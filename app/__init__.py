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
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"\n{'='*50}")
            print(f"ERROR: Could not connect to the database.")
            print(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Set').split('@')[-1] if '@' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else '***'}")
            print(f"Error details: {str(e)}")
            print(f"{'='*50}\n")
            raise e
    
    return app
