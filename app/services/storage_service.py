"""Supabase Storage service."""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from ..extensions import get_supabase

BUCKET_NAME = 'erp-files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """Generate unique filename."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{timestamp}_{unique_id}.{ext}"


def upload_file(file, folder='uploads'):
    """Upload file to Supabase Storage."""
    try:
        if not file or not file.filename:
            return {'success': False, 'error': 'No file provided'}
        
        if not allowed_file(file.filename):
            return {'success': False, 'error': 'File type not allowed'}
        
        filename = generate_unique_filename(file.filename)
        file_path = f"{folder}/{filename}"
        
        # Read file content
        file_content = file.read()
        
        supabase = get_supabase()
        if not supabase:
            # Fallback: save locally
            local_path = os.path.join('app', 'static', 'uploads', folder)
            os.makedirs(local_path, exist_ok=True)
            full_path = os.path.join(local_path, filename)
            with open(full_path, 'wb') as f:
                f.write(file_content)
            return {
                'success': True,
                'url': f'/static/uploads/{folder}/{filename}',
                'path': file_path
            }
        
        # Upload to Supabase
        response = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            file_content,
            {'content-type': file.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        
        return {
            'success': True,
            'url': public_url,
            'path': file_path
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_file(file_path):
    """Delete file from Supabase Storage."""
    try:
        supabase = get_supabase()
        if not supabase:
            return {'success': False, 'error': 'Supabase not configured'}
        
        # Extract path from URL if full URL provided
        if file_path.startswith('http'):
            file_path = file_path.split(f'{BUCKET_NAME}/')[-1]
        
        supabase.storage.from_(BUCKET_NAME).remove([file_path])
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_public_url(file_path):
    """Get public URL for a file."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
        
        return supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    except Exception:
        return None
