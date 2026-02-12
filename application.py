import os
import uuid
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from types import SimpleNamespace
import apps.store as store

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "defaultsecret")

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
    return render_template('landing.html')

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
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

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


# Elastic Beanstalk looks for 'application' variable
application = app

if __name__ == "__main__":
    application.run()
