from apps.database import db
from boto3.dynamodb.conditions import Attr, Key
from types import SimpleNamespace

dbtables = SimpleNamespace(
    assistants = db.Table("assistants"),
    threads = db.Table("user_threads"),
    messages = db.Table("user_messages"),
    vector_files = db.Table("vector_files"),
    users = db.Table("users"),
)

def get_user(user_id):
    response = dbtables.users.get_item(Key={"email": user_id})
    return response.get("Item")

def add_user(data):
    dbtables.users.put_item(
        Item={"id": data.id, "email": data.email, "password": data.password, "user_type": "user", "is_active": True}
    )

def get_thread(assistant_id, user_id):
    # response = dbtables.threads.scan(
    #     FilterExpression=Attr("id").eq(assistant_id)
    # )

    response = dbtables.threads.query(
        KeyConditionExpression=Key('id').eq(assistant_id) & Key('user_id').eq(user_id)
    )
    return response

def create_thread(data):
    dbtables.threads.put_item(Item=data)

def create_message(data):
    try:
        dbtables.messages.put_item(Item=data)
    except Exception as e:
        print(str(e))
        #return jsonify({"api error": str(e)}), 400

def get_agents():
    response = dbtables.assistants.scan(
        #FilterExpression=Attr("user_id").eq(current_user.user_id)
    )
    return response.get("Items", [])

def add_assistant(assistant_data, user_id, vector_id):
    assistant_item = {
        "id": assistant_data["id"],
        "description":  assistant_data["description"],
        "instructions":  assistant_data["instructions"],
        "model":  assistant_data["model"],
        "name":  assistant_data["name"],
        "object": "assistant",
        "tools_type":  assistant_data["tools"][0]["type"],
        "vector_id": vector_id,
        "user_id": user_id
    }
    dbtables.assistants.put_item(Item=assistant_item)

def update_assistant(assistant_data, assistant_id, user_id, vector_id):
    assistant_item = {
        "id": assistant_id,
        "description":  assistant_data["description"],
        "instructions":  assistant_data["instructions"],
        "model":  assistant_data["model"],
        "name":  assistant_data["name"],
        "object": "assistant",
        "tools_type":  assistant_data["tools_type"],
        "vector_id": vector_id if not "" else assistant_data["vector_id"],
        "user_id": user_id
    }
    dbtables.assistants.put_item(Item=assistant_item)

def list_assistants(user_id):
    response = dbtables.assistants.scan(
        FilterExpression=Attr("user_id").eq(user_id)
    )
    return response.get("Items", [])

def get_assistant(assistant_id):
    #response = dbtables.assistants.get_item(Key={"id": assistant_id})
    response = dbtables.assistants.query(
        KeyConditionExpression=Key("id").eq(assistant_id)
    )
    return response.get("Items", [])

def del_assistant(assistant_id):
    dbtables.assistants.delete_item(Key={"id": assistant_id})


def create_files(data):
    dbtables.vector_files.put_item(Item=data)