import re
from datetime import date, datetime


NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-']+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s().-]{7,20}$")


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
    Validates that the name uses a strict whitelist.
    Allowed characters: letters, spaces, hyphens, apostrophes.
    Returns True if valid, False otherwise.
    """
    if not name:
        return False
    return bool(NAME_PATTERN.fullmatch(name.strip()))


def validate_phone(phone):
    """
    Validates phone number format.
    Empty values are allowed, otherwise only digits and common separators.
    """
    if not phone:
        return True
    return bool(PHONE_PATTERN.fullmatch(phone.strip()))


def validate_date_of_birth(date_of_birth, min_age=13, max_age=120):
    """
    Validates date of birth in ISO format (YYYY-MM-DD) and age bounds.
    """
    if not date_of_birth:
        return False

    try:
        dob = datetime.strptime(date_of_birth.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False

    today = date.today()
    if dob > today:
        return False

    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return min_age <= age <= max_age


def sanitize_input(input_string):
    """
    Sanitizes generic free-text input by removing HTML/script-like tags.
    Do not use this for strict fields that should fail validation (e.g. names).
    """
    if not input_string:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', input_string)
    return clean.strip()


def validate_password(password):
    """
    Validates password strength.
    Current rule: At least 8 characters.
    """
    if not password:
        return False
    return len(password) >= 8
