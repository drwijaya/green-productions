"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import os

# Try to import supabase, but make it optional
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()

# Supabase client (initialized later)
supabase_client = None


def init_supabase():
    """Initialize Supabase client."""
    global supabase_client
    if not SUPABASE_AVAILABLE:
        return None
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if url and key:
        supabase_client = create_client(url, key)
    return supabase_client


def get_supabase():
    """Get Supabase client instance."""
    global supabase_client
    if not SUPABASE_AVAILABLE:
        return None
    if supabase_client is None:
        init_supabase()
    return supabase_client
