import re
from datetime import date, datetime

NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-']+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s().-]{7,20}$")
COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty",
    "letmein",
    "admin",
    "welcome",
    "iloveyou",
    "abc123",
}


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
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
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
    clean = re.sub(r"<[^>]*>", "", input_string)
    return clean.strip()


def validate_password(password):
    """Return True when password meets policy requirements."""
    return len(get_password_validation_errors(password)) == 0


def get_password_validation_errors(password):
    """Return a list of user-facing password policy failures."""
    if not password:
        return ["Password is required."]

    errors = []
    if len(password) < 12:
        errors.append("Use at least 12 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Include at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Include at least one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Include at least one symbol (for example: ! @ # $).")
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Choose a less common password.")
    return errors


def validate_max_length(value, max_length):
    """Validate that a string does not exceed max_length characters."""
    if value is None:
        return True
    return len(value) <= max_length
