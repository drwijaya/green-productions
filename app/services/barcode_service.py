"""Barcode generation service."""
import os
import io
import barcode
from barcode.writer import ImageWriter
from .storage_service import upload_file


def generate_barcode_image(barcode_value, barcode_id):
    """Generate barcode image and upload to storage."""
    try:
        # Generate Code128 barcode
        code128 = barcode.get('code128', barcode_value, writer=ImageWriter())
        
        # Save to buffer
        buffer = io.BytesIO()
        code128.write(buffer)
        buffer.seek(0)
        
        # Create file-like object for upload
        class FileWrapper:
            def __init__(self, buffer, filename):
                self.buffer = buffer
                self.filename = filename
                self.content_type = 'image/png'
            
            def read(self):
                return self.buffer.read()
        
        file_wrapper = FileWrapper(buffer, f'barcode_{barcode_id}.png')
        
        # Upload to storage
        result = upload_file(file_wrapper, 'barcodes')
        
        if result['success']:
            return result['url']
        return None
        
    except Exception as e:
        print(f"Barcode generation error: {e}")
        return None


def generate_qr_code(data, size=10):
    """Generate QR code image."""
    try:
        import qrcode
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"QR code generation error: {e}")
        return None


def generate_qr_code_base64(data, size=6):
    """Generate QR code as base64 string for inline HTML display.
    
    Args:
        data: The data to encode in QR code
        size: Box size for QR code (default 6 for smaller display)
    
    Returns:
        Base64 encoded string of PNG image, or None on error
    """
    try:
        import qrcode
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=size,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Encode to base64
        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{base64_str}"
        
    except Exception as e:
        print(f"QR code base64 generation error: {e}")
        return None

