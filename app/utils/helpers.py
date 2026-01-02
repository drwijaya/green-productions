"""Utility helpers."""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving extension."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    safe_name = secure_filename(original_filename.rsplit('.', 1)[0])[:20]
    return f"{safe_name}_{timestamp}_{unique_id}.{ext}"


def format_currency(value, currency='Rp'):
    """Format number as currency."""
    if value is None:
        return f"{currency} 0"
    return f"{currency} {value:,.0f}".replace(',', '.')


def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """Format datetime for display."""
    if dt is None:
        return '-'
    return dt.strftime(format)


def format_date(dt, format='%d/%m/%Y'):
    """Format date for display."""
    if dt is None:
        return '-'
    return dt.strftime(format)


def calculate_percentage(value, total):
    """Calculate percentage safely."""
    if total == 0:
        return 0
    return round((value / total) * 100, 2)


def sanitize_html(text):
    """Basic HTML sanitization."""
    if not text:
        return text
    # Remove script tags
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove on* attributes
    text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    return text


def get_priority_label(priority):
    """Get priority label from number."""
    labels = {
        1: 'Normal',
        2: 'High',
        3: 'Urgent'
    }
    return labels.get(priority, 'Normal')


def get_priority_color(priority):
    """Get priority color class."""
    colors = {
        1: 'secondary',
        2: 'warning',
        3: 'danger'
    }
    return colors.get(priority, 'secondary')


def get_status_color(status):
    """Get status color class."""
    status_colors = {
        'draft': 'secondary',
        'pending': 'warning',
        'pending_approval': 'info',
        'pending_dso': 'info',
        'approved': 'success',
        'in_progress': 'primary',
        'in_production': 'primary',
        'qc_in_progress': 'info',
        'qc_pending': 'warning',
        'qc_failed': 'danger',
        'completed': 'success',
        'pass': 'success',
        'fail': 'danger',
        'rework': 'warning',
        'cancelled': 'dark',
        'rejected': 'danger',
        'on_hold': 'secondary'
    }
    return status_colors.get(status, 'secondary')
