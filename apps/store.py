from apps.database import db
from apps.utils import normalize_email


users_table = db.Table("users")


def get_user(email):
    """Retrieve a user record by email.

    Args:
        email: The user's email address (partition key).

    Returns:
        A dict with user attributes, or None if not found.
    """
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    response = users_table.get_item(Key={"email": normalized_email})
    return response.get("Item")


def add_user(data):
    """Create a new user record in DynamoDB.

    Args:
        data: A namespace/object with id, email, and password attributes.
    """
    normalized_email = normalize_email(getattr(data, "email", ""))
    users_table.put_item(
        Item={
            "id": data.id,
            "email": normalized_email,
            "password": data.password,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "date_of_birth": data.date_of_birth,
            "phone": getattr(data, "phone", ""),
            "user_type": "user",
            "is_active": True,
            "email_verified": False,
        }
    )


def update_user(email, updates):
    """Update fields on an existing user record.

    Args:
        email: The user's email address (partition key).
        updates: A dict of field names to new values.
    """
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    user = get_user(normalized_email)
    if not user:
        return None

    safe_updates = dict(updates or {})
    if "email" in safe_updates:
        safe_updates["email"] = normalize_email(safe_updates["email"])

    user.update(safe_updates)
    user["email"] = normalize_email(user.get("email", normalized_email))
    users_table.put_item(Item=user)
    return user
