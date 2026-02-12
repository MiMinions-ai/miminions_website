from apps.database import db
from boto3.dynamodb.conditions import Attr, Key
from types import SimpleNamespace

dbtables = SimpleNamespace(
    users = db.Table("users"),
)

def get_user(user_id):
    response = dbtables.users.get_item(Key={"email": user_id})
    return response.get("Item")

def add_user(data):
    dbtables.users.put_item(
        Item={"id": data.id, "email": data.email, "password": data.password, "user_type": "user", "is_active": True}
    )