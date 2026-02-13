import re

def validate_email(email):
    """
    Validates email format using regex.
    Returns True if valid, False otherwise.
    """
    if not email:
        return False
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))

def validate_password(password):
    """
    Validates password strength.
    Current rule: At least 8 characters.
    """
    if not password:
        return False
    return len(password) >= 8
