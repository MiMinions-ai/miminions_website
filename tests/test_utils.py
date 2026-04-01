from apps.utils import get_password_validation_errors, validate_password


def test_validate_password_accepts_strong_password():
    strong = "StrongPass123!"
    assert validate_password(strong)
    assert get_password_validation_errors(strong) == []


def test_validate_password_rejects_common_password():
    errors = get_password_validation_errors("password")
    assert "Choose a less common password." in errors


def test_validate_password_rejects_missing_character_classes():
    errors = get_password_validation_errors("alllowercase123")
    assert "Include at least one uppercase letter." in errors
    assert "Include at least one symbol (for example: ! @ # $)." in errors
