from flask_login import UserMixin

import apps.store as store
from apps.extensions import login_manager


class User(UserMixin):
    def __init__(self, user_data):
        if not user_data:
            raise ValueError("User data cannot be None")

        self.id = user_data.get("email")  # Flask-Login requires an "id" attribute
        if not self.id:
            raise ValueError("User must have an email")

        self.user_id = user_data.get("id")
        self.email = user_data.get("email")
        self.password = user_data.get("password")
        self.first_name = user_data.get("first_name", "")
        self.last_name = user_data.get("last_name", "")
        self.date_of_birth = user_data.get("date_of_birth", "")
        self.phone = user_data.get("phone", "")

    @property
    def full_name(self):
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or None

    def to_dict(self):
        return {"id": self.user_id, "email": self.email}


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login sessions.

    Args:
        user_id: The user's email (used as ID)

    Returns:
        User object if found and valid, None otherwise
    """
    try:
        user_data = store.get_user(user_id)
        if user_data:
            return User(user_data)
    except Exception as e:
        # Log the error but don't crash the app
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error loading user {user_id}: {e}")
    return None
