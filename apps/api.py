import openai, os, boto3
from flask import jsonify
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def create_thread(assistant_id, user_id):
    try:
        threads = openai.beta.threads.create()
        threads_data = threads.model_dump()
        thread_item = {
            "id": assistant_id,
            "thread_id":  threads_data["id"],
            "user_id": user_id
        }
        return thread_item
    except Exception as e:
        print("create thread: " + str(e))

def create_message(data):
    try:    
        openai.beta.threads.messages.create(
            thread_id=data["thread_id"], 
            role=data["role"], 
            content=data["content"]
        )
    except Exception as e:
        print("create msg: " + str(e))
        

def get_message(thread_id):
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value

def create_run(data):
    run = openai.beta.threads.runs.create(
        thread_id=data["thread_id"],
        assistant_id=data["assistant_id"],
    )
    return run

def retrieve_run(data):
    run_status = openai.beta.threads.runs.retrieve(
        thread_id=data["thread_id"], run_id=data["run_id"]
    )
    return run_status



##############

def create_assistant(data, user_id, vector_store_id):
    response = openai.beta.assistants.create(
        name=data.get("name"),
        model=data.get("model", "gpt-4-turbo"),
        tools=[{"type": data.get("tools_type")}],
        instructions=data.get("instructions", ""),
        description=data.get("description", ""),
        metadata={"user_id": user_id},
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
    )
    return response.model_dump()

def update_assistant(data, assistant_id, user_id, vector_store_id):
    response = openai.beta.assistants.update(
        assistant_id,
        name=data.get("name"),
        model=data.get("model", "gpt-4-turbo"),
        tools=[{"type": data.get("tools_type")}],
        instructions=data.get("instructions", ""),
        metadata={"user_id": user_id},
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
    )
    return response.model_dump()

def list_assistants():
    response = openai.beta.assistants.list()
    return [assistant.model_dump() for assistant in response.data]

def get_assistant(assistant_id):
    # try:
    #     response = openai.beta.assistants.retrieve(assistant_id)
    #     return jsonify(response.dict())
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 404
    return True

def list_threads(assistant_id, user_id):
    response = openai.beta.threads.list()
    return jsonify([threads.model_dump() for threads in response.data])

def del_assistant(assistant_id):
    openai.beta.assistants.delete(assistant_id)


def uploadFilesOnS3(file):
    # Create folder if not exists
    os.makedirs(os.getenv("LOCAL_UPLOAD_FOLDER"), exist_ok=True)
    # Save locally
    local_path = os.path.join(os.getenv("LOCAL_UPLOAD_FOLDER"), file.filename)
    file.save(local_path)

    s3 = boto3.client('s3')
    s3.upload_file(local_path, os.getenv("S3_BUCKET"), file.filename)
    s3_url = f"https://{os.getenv("S3_BUCKET")}.s3.{os.getenv("S3_REGION")}.amazonaws.com/{file.filename}"
    return s3_url
    
def create_files(file):
    uploaded_file = openai.files.create(
        file=(file.filename, file.stream),
        purpose='assistants'
    )
    return uploaded_file.id

def create_vector_store(file_ids, name):
    vector_store = openai.vector_stores.create(
        name=name,
        file_ids=[file_ids]
    )
    return vector_store.id