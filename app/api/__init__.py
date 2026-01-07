"""API blueprints package."""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import and register API routes after blueprint creation to avoid circular imports
from . import auth, users, customers, orders, dso, production, qc, barcodes, sop, reports, employees, permissions, vendors, materials, qc_monitoring

