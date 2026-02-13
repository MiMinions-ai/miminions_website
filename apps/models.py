from flask_login import UserMixin
from apps.extensions import login_manager
import apps.store as store

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data["email"]  # Flask-Login requires an "id" attribute
        self.user_id = user_data.get("id")
        self.email = user_data.get("email")
        self.password = user_data.get("password")

    def to_dict(self):
        return {"id": self.user_id, "email": self.email}

@login_manager.user_loader
def load_user(user_id):
    user_data = store.get_user(user_id)
    if user_data:
        return User(user_data)
    return None
