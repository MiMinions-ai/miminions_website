import re


def normalize_email(email):
    """Normalize email input for consistent user lookups/storage."""
    if not email:
        return ""
    return email.strip().lower()

def validate_email(email):
    """
    Validates email format using regex.
    Returns True if valid, False otherwise.
    """
    normalized = normalize_email(email)
    if not normalized:
        return False
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', normalized))

def validate_password(password):
    """
    Validates password strength.
    Current rule: At least 8 characters.
    """
    if not password:
        return False
    return len(password) >= 8
