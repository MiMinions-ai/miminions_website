from apps.database import db


users_table = db.Table("users")


def get_user(email):
    """Retrieve a user record by email.

    Args:
        email: The user's email address (partition key).

    Returns:
        A dict with user attributes, or None if not found.
    """
    response = users_table.get_item(Key={"email": email})
    return response.get("Item")


def add_user(data):
    """Create a new user record in DynamoDB.

    Args:
        data: A namespace/object with id, email, and password attributes.
    """
    users_table.put_item(
        Item={
            "id": data.id,
            "email": data.email,
            "password": data.password,
            "user_type": "user",
            "is_active": True,
        }
    )