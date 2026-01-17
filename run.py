import os
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, url_for, session, Response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
#from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from dotenv import load_dotenv
from types import SimpleNamespace
# from werkzeug.utils import secure_filename
# from decimal import Decimal
import json
# import requests
# import asyncio
# import string
# import random


import uuid
import time
import apps.store as store
import apps.api as api
#from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")  # Change this in production
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "defaultjwtsecret")  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Flask-Session Configuration
app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
app.config["SESSION_PERMANENT"] = False  # Ensure session expires on browser close
app.config["SESSION_USE_SIGNER"] = True  # Sign session cookies for security
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "defaultjwtsecret")  
#Session(app)
#CORS(app)


jwt = JWTManager(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'



@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Cache-Control"] = "no-cache"
    return response

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data["email"]  # Flask-Login requires an "id" attribute
        self.user_id = user_data.get("id")
        self.email = user_data.get("email")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}

@login_manager.user_loader
def load_user(user_id):
    user_data = store.get_user(user_id)
    if user_data:
        return User(user_data)
    return None

@app.route('/')
def home():
    # Logged-in users go to agents dashboard, others see landing page
    if current_user.is_authenticated:
        return redirect(url_for('agents'))
    return render_template('landing.html')

@app.route("/protected", methods=["GET"])
def protected():
    return jsonify({"session": current_user.user_id})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_add_data = SimpleNamespace(
            id =  str(uuid.uuid4()),
            email = email,
            password = generate_password_hash(password)
        )

        user_data = store.get_user(email)

        if not user_data:
            store.add_user(user_add_data)
            flash('Register successful!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Already Registered', 'danger')
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_data = store.get_user(email)

        if user_data and not check_password_hash(user_data["password"], password):
            flash('Invalid credentials', 'danger')
        else:
            user = User(user_data)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('agents'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/agents')
@login_required
def agents():
    response = store.get_agents()
    session["agents"] = response
    return render_template("agents.html", agents=response, u=current_user.user_id)

@app.route('/agents/chat/<assistant_id>', methods=['GET'])
@login_required
def chat(assistant_id):
    if not session.get("threads", {}).get(current_user.user_id):
        session["threads"][str(current_user.user_id)] = {}

    assistant_response = session.get("assistant", store.get_assistant(assistant_id))
    get_response = store.get_thread(assistant_id, current_user.user_id)

    if "Items" in get_response and get_response["Count"] > 0:
        #if str(assistant_id) not in session["threads"][str(current_user.user_id)]:
        session["threads"][str(current_user.user_id)][str(assistant_id)] = get_response["Items"][0]
        session.modified = True
    else:
        thread_item = api.create_thread(assistant_id, current_user.user_id)
        store.create_thread(thread_item)
        session["threads"][str(current_user.user_id)][str(assistant_id)] = thread_item

    return render_template('chat.html', id=str(current_user.user_id), aid=assistant_id, assistant_data=assistant_response[0], thread=session.get("threads"))

@app.route("/message/<assistant_id>/<thread_id>", methods=["POST"])
def message(assistant_id, thread_id):
    try:
        data = request.json
        message = data.get("message")

        api.create_message(
            {
                "thread_id": thread_id,
                "role": "user",
                "content": message,
            }
        )

        run = api.create_run(
            {
                "thread_id": thread_id,
                "assistant_id": assistant_id
            }
        )

        while True:
            run_status = api.retrieve_run(
                {
                    "thread_id": thread_id, 
                    "run_id": run.id
                }
            )
            if run_status.status == "completed":
                break
            time.sleep(0.1)  # Wait for a second before checking again

        # Retrieve and return the latest message from the assistant
        response = api.get_message(thread_id)

        user_message_data = {
            "id": str(uuid.uuid4()),
            "run_id": run.id,
            "user_id": current_user.user_id,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "message": message,
            "role": "user"
        }
        store.create_message(user_message_data)

        bot_message_data = {
            "id": str(uuid.uuid4()),
            "run_id": run.id,
            "user_id": current_user.user_id,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "message": response,
            "role": "bot"
        }
        store.create_message(bot_message_data)
        
        return jsonify({"message": str(response)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/use-cases')
def use_cases():
    return render_template('use-cases.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faqs')
def faq():
    return render_template('faqs.html')




######### API

def get_user_id_from_token():
    try:
        current_user_id = get_jwt_identity().split(":::")
        if current_user_id:
            return current_user_id[0]
        return "Invalid token"
    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
    

@app.route('/apilogin', methods=['POST'])
def apilogin():
    data = request.json
    
    if request.method == 'POST':
        email = data.get('email')
        password = data.get('password')

        user_data = store.get_user(email)

        if user_data and ((not check_password_hash(user_data["password"], password)) or user_data["user_type"] == "user" or user_data["is_active"] == False):
            return jsonify({"error": 'Invalid credentials'}), 400
        else:
            access_token = create_access_token(identity=user_data["id"]+":::"+user_data["email"])
            return jsonify(access_token=access_token)
    return jsonify({"error": 'Invalid credentials 1'}), 400


@app.route('/assistants', methods=['POST'])
@jwt_required()
def create_assistant():
    try:
        vector_id = uploadFiles(request)
        user_id = get_user_id_from_token()
        assistant_item = api.create_assistant(request.form, user_id, vector_id)
        store.add_assistant(assistant_item, user_id, vector_id)
        return jsonify(assistant_item), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/assistants', methods=['GET'])
@jwt_required()
def list_assistants():
    try:
        user_id = get_user_id_from_token()
        response = api.list_assistants()
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/assistants/<assistant_id>", methods=["GET"])
@jwt_required()
def get_assistant(assistant_id):
    try:
        response = store.get_assistant(assistant_id)
        if response:
            return jsonify(response[0]), 200
        return jsonify({"error": "Assistant not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
   

@app.route('/assistants/<assistant_id>', methods=['PATCH'])
@jwt_required()
def update_assistant(assistant_id):
    data = request.json
    try:
        user_id = get_user_id_from_token()
        assistant_item = api.update_assistant(data, assistant_id, user_id)
        store.update_assistant(data, assistant_id, user_id, "")
        return jsonify(assistant_item), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/assistants/<assistant_id>', methods=['DELETE'])
@jwt_required()
def delete_assistant(assistant_id):
    try:
        api.del_assistant(assistant_id)
        store.del_assistant(assistant_id)
        return jsonify({"message": "Assistant deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/threads/<assistant_id>', methods=['GET'])
@jwt_required()
def list_threads(assistant_id):
    try:
        user_id = get_user_id_from_token()
        #response = api.list_threads(assistant_id, user_id)
        response = store.get_thread(assistant_id, user_id)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

def uploadFiles(request):
    file = request.files['file']
    if not file:
        return jsonify({"error": "No file provided"}), 400

    s3_file_id = api.uploadFilesOnS3(file)
    file_id = api.create_files(file)
    vector_id = api.create_vector_store(file_id, request.form["name"])
    store.create_files({"id": file_id, "file_id": file_id, "vector_id": vector_id, "name": request.form["name"], "file_path": s3_file_id})
    return vector_id

@app.route('/attach_file/<assistant_id>', methods=['POST'])
@jwt_required()
def attach_file(assistant_id):
    data = request.form
    try:
        user_id = get_user_id_from_token()
        vector_id = uploadFiles(request)
        assistant_item = api.update_assistant(data, assistant_id, user_id, vector_id)
        store.update_assistant(data, assistant_id, user_id, vector_id)
        return jsonify(assistant_item), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400



if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5010, debug=True)
