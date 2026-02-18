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
from apps.email_service import send_verification_email, verify_token

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

        # Collect profile fields
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()

        if not first_name or not last_name:
            flash('Please enter your first and last name.', 'danger')
            return render_template('signup.html')

        if not date_of_birth:
            flash('Please enter your date of birth.', 'danger')
            return render_template('signup.html')

        user_data = store.get_user(email)

        if user_data:
            current_app.logger.warning(f"Signup failed - email already exists: {email}")
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html')

        user_add_data = SimpleNamespace(
            id=str(uuid.uuid4()),
            email=email,
            password=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
        store.add_user(user_add_data)
        current_app.logger.info(f"New user registered: {email}")

        # Send verification email
        send_verification_email(email)

        flash('Registration successful! Please check your email to verify your account, then log in.', 'success')
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
            return render_template('login.html', email=email)

        if not check_password_hash(user_data["password"], password):
            current_app.logger.warning(f"Login failed - incorrect password: {email}")
            flash('Incorrect password.', 'danger')
            return render_template('login.html', email=email)

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

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@bp.route('/verify-email/<token>')
def verify_email(token):
    """Handle email verification link clicks."""
    email = verify_token(token)
    if not email:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))

    user_data = store.get_user(email)
    if not user_data:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.signup'))

    if user_data.get('email_verified'):
        flash('Your email is already verified.', 'info')
        return redirect(url_for('auth.login'))

    store.update_user(email, {'email_verified': True})
    current_app.logger.info(f"Email verified for: {email}")
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/resend-verification', methods=['POST'])
@limiter.limit("3 per minute")
def resend_verification():
    """Resend the verification email."""
    email = request.form.get('email', '').strip()
    if not email:
        flash('Please provide your email address.', 'danger')
        return redirect(url_for('auth.login'))

    user_data = store.get_user(email)
    if not user_data:
        # Don't reveal whether the account exists
        flash('If an account with that email exists, a verification email has been sent.', 'info')
        return redirect(url_for('auth.login'))

    if user_data.get('email_verified'):
        flash('Your email is already verified.', 'info')
        return redirect(url_for('auth.login'))

    send_verification_email(email)
    flash('If an account with that email exists, a verification email has been sent.', 'info')
    return redirect(url_for('auth.login'))
