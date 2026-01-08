"""Google Drive Service for file uploads using OAuth2."""
import os
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
DEFAULT_FOLDER_ID = '1Rb93R9g7q-KTKSdpNJxIiXn54UUAcvqs'

def get_drive_service():
    """Get authenticated Google Drive service using OAuth2 credentials."""
    import json
    creds = None
    try:
        # 1. Try to load from environment variables first (For Railway/Production)
        env_token = os.environ.get('GOOGLE_DRIVE_TOKEN_JSON')
        if env_token:
            token_data = json.loads(env_token)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # 2. Fallback to local file (For Local Development)
        elif os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # If there are no (valid) credentials available, something is wrong
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
                # Save refreshed token if we are using local file
                if not env_token and os.path.exists(TOKEN_FILE):
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
            else:
                print("Error: No valid credentials found in env or file.")
                return None
                
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error initializing Google Drive service: {e}")
        return None

def upload_to_drive(file_stream, filename, mimetype='application/pdf', folder_id=None):
    """Upload a file to Google Drive using OAuth2."""
    try:
        service = get_drive_service()
        if not service:
            return {'success': False, 'error': 'Google Drive service not available. Token might be missing.'}
        
        folder_id = folder_id or DEFAULT_FOLDER_ID
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        # Handle input stream
        if isinstance(file_stream, bytes):
            file_stream = io.BytesIO(file_stream)
        elif hasattr(file_stream, 'read'):
            if hasattr(file_stream, 'seek'):
                file_stream.seek(0)
            content = file_stream.read()
            file_stream = io.BytesIO(content)
        
        media = MediaIoBaseUpload(
            file_stream,
            mimetype=mimetype,
            resumable=True
        )
        
        # No need for supportsAllDrives for personal My Drive unless it's a Shared Drive
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink'
        ).execute()
        
        file_id = file.get('id')
        
        # Make file publicly readable for preview (optional, depending on requirements)
        try:
            service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except Exception as perm_error:
            print(f"Warning: Could not set public permission: {perm_error}")
        
        view_url = file.get('webViewLink', f'https://drive.google.com/file/d/{file_id}/view')
        preview_url = f'https://drive.google.com/file/d/{file_id}/preview'
        
        return {
            'success': True,
            'file_id': file_id,
            'url': view_url,
            'preview_url': preview_url,
            'filename': filename
        }
    except Exception as e:
        print(f"Google Drive upload error: {e}")
        return {'success': False, 'error': str(e)}

def get_preview_url(file_id):
    return f'https://drive.google.com/file/d/{file_id}/preview'

def delete_from_drive(file_id):
    try:
        service = get_drive_service()
        if not service: return {'success': False, 'error': 'Service unavailable'}
        service.files().delete(fileId=file_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}
