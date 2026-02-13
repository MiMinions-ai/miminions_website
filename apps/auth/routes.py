from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from types import SimpleNamespace
import uuid

from apps.auth import bp
from apps.extensions import limiter
import apps.store as store
from apps.models import User
from apps.utils import validate_email, validate_password

@bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        current_app.logger.info(f"Signup attempt for email: {email}")

        # Validate email format
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('signup.html')

        # Validate password length
        if not validate_password(password):
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('signup.html')

        # Validate passwords match
        confirm_password = request.form.get('confirm_password', '')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')

        user_data = store.get_user(email)

        if user_data:
            current_app.logger.warning(f"Signup failed - email already exists: {email}")
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html')

        user_add_data = SimpleNamespace(
            id=str(uuid.uuid4()),
            email=email,
            password=generate_password_hash(password)
        )
        store.add_user(user_add_data)
        current_app.logger.info(f"New user registered: {email}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        current_app.logger.info(f"Login attempt for email: {email}")

        user_data = store.get_user(email)

        if not user_data:
            current_app.logger.warning(f"Login failed - user not found: {email}")
            flash('No account found with that email.', 'danger')
            return render_template('login.html')

        if not check_password_hash(user_data["password"], password):
            current_app.logger.warning(f"Login failed - incorrect password: {email}")
            flash('Incorrect password.', 'danger')
            return render_template('login.html')

        user = User(user_data)
        login_user(user)
        current_app.logger.info(f"User logged in successfully: {email}")
        flash('Login successful!', 'success')
        return redirect(url_for('main.home'))

    return render_template('login.html')

@bp.route("/logout")
@login_required
def logout():
    email = current_user.email if current_user.is_authenticated else "unknown"
    logout_user()
    current_app.logger.info(f"User logged out: {email}")
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.home'))
