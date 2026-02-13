import os
import re
import uuid
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from types import SimpleNamespace
import apps.store as store

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required")

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'



@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    if current_user.is_authenticated:
        response.headers["Cache-Control"] = "no-store"
    return response

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data["email"]  # Flask-Login requires an "id" attribute
        self.user_id = user_data.get("id")
        self.email = user_data.get("email")

    def to_dict(self):
        return {"id": self.user_id, "email": self.email}

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
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Validate email format
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('signup.html')

        # Validate password length
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('signup.html')

        user_data = store.get_user(email)

        if user_data:
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html')

        user_add_data = SimpleNamespace(
            id=str(uuid.uuid4()),
            email=email,
            password=generate_password_hash(password)
        )
        store.add_user(user_add_data)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user_data = store.get_user(email)

        if not user_data:
            flash('No account found with that email.', 'danger')
            return render_template('login.html')

        if not check_password_hash(user_data["password"], password):
            flash('Incorrect password.', 'danger')
            return render_template('login.html')

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
