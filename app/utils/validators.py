"""Form validators."""
from wtforms.validators import ValidationError
import re


def validate_phone(form, field):
    """Validate Indonesian phone number."""
    if field.data:
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', field.data)
        # Check if it's a valid Indonesian phone number
        if not re.match(r'^(\+62|62|0)[0-9]{8,12}$', phone):
            raise ValidationError('Nomor telepon tidak valid.')


def validate_order_code(form, field):
    """Validate order code format."""
    if field.data:
        if not re.match(r'^ORD-\d{6}-\d{4}$', field.data):
            raise ValidationError('Format kode order tidak valid.')


def validate_positive_number(form, field):
    """Validate positive number."""
    if field.data is not None and field.data < 0:
        raise ValidationError('Nilai harus positif.')


def validate_password_strength(form, field):
    """Validate password strength."""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password minimal 8 karakter.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password harus mengandung huruf kapital.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password harus mengandung huruf kecil.')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password harus mengandung angka.')
