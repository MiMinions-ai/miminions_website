import re


def normalize_email(email):
    """Normalize email input for consistent user lookups/storage."""
    if not email:
        return ""
    return email.strip().lower()


def validate_email(email):
    """
    Validates email format using a standard regex.
    Returns True if valid, False otherwise.
    """
    if not email:
        return False
    # Standard email regex pattern
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.fullmatch(pattern, email))


def validate_name(name):
    """
    Validates that the name contains only alphabetic characters and spaces.
    Returns True if valid, False otherwise.
    """
    if not name:
        return False
    # Only allow letters and spaces
    pattern = r'^[a-zA-Z\s]+$'
    return bool(re.fullmatch(pattern, name))


def sanitize_input(input_string):
    """
    Sanitizes string input by removing potential script tags and dangerous characters.
    Although strict validation handles most cases, this is an extra safety layer.
    """
    if not input_string:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', input_string)
    # Remove potential SQL injection characters for good measure
    clean = clean.replace("'", "").replace('"', "").replace(';', "").replace('--', "")
    return clean.strip()


def validate_password(password):
    """
    Validates password strength.
    Current rule: At least 8 characters.
    """
    if not password:
        return False
    return len(password) >= 8
