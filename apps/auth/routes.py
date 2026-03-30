from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from types import SimpleNamespace
import uuid

from apps.auth import bp
from apps.extensions import limiter
import apps.store as store
from apps.models import User
from apps.utils import (
    normalize_email,
    validate_date_of_birth,
    validate_email,
    validate_name,
    validate_password,
    validate_phone,
)
from apps.email_service import send_verification_email, verify_token

@bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("60 per minute", methods=["POST"])
def signup():
    if request.method == 'POST':
        raw_email = request.form.get('email', '')
        email = normalize_email(raw_email)
        password = request.form.get('password', '')  # Do not sanitize password, it gets hashed

        current_app.logger.info(f"Signup attempt for email: {email}")

        # Validate email format
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('signup.html'), 400

        # Strict fail-fast validation: never auto-correct invalid names.
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        if not first_name or not last_name:
            flash('Please enter your first and last name.', 'danger')
            return render_template('signup.html'), 400

        if not validate_name(first_name) or not validate_name(last_name):
            flash("Names may only contain letters, spaces, hyphens, and apostrophes.", 'danger')
            return render_template('signup.html'), 400

        # Validate password length
        if not validate_password(password):
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('signup.html'), 400

        # Validate passwords match
        confirm_password = request.form.get('confirm_password', '')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html'), 400

        date_of_birth = request.form.get('date_of_birth', '').strip()

        if not date_of_birth:
            flash('Please enter your date of birth.', 'danger')
            return render_template('signup.html'), 400

        if not validate_date_of_birth(date_of_birth):
            flash('Enter a valid birth date in YYYY-MM-DD format (age must be between 13 and 120).', 'danger')
            return render_template('signup.html'), 400

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
        
        # Try to create the user
        user_created = store.add_user(user_add_data)
        if not user_created:
            current_app.logger.error(f"Failed to create user in database: {email}")
            flash('Registration failed due to a database error. Please try again.', 'danger')
            return render_template('signup.html')
            
        current_app.logger.info(f"New user registered: {email}")

        # Send verification email
        email_sent = send_verification_email(email)
        if email_sent:
            flash('Registration successful! Please check your email to verify your account, then log in.', 'success')
        else:
            flash('Registration successful, but we could not send the verification email. Please use resend verification from login.', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("120 per minute", methods=["POST"])
def login():
    if request.method == 'POST':
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        remember_me = 'remember_me' in request.form

        current_app.logger.info(f"Login attempt for email: {email}")

        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html', email=email)

        user_data = store.get_user(email)

        if not user_data:
            current_app.logger.warning(f"Login failed - user not found: {email}")
            flash('No account found with that email.', 'danger')
            return render_template('login.html', email=email)

        stored_password_hash = user_data.get("password")
        if not stored_password_hash or not check_password_hash(stored_password_hash, password):
            current_app.logger.warning(f"Login failed - incorrect password: {email}")
            flash('Incorrect password.', 'danger')
            return render_template('login.html', email=email)

        if not user_data.get('is_active', True):
            current_app.logger.warning(f"Login failed - inactive account: {email}")
            flash('Your account is inactive. Please contact support.', 'danger')
            return render_template('login.html', email=email)

        # Legacy accounts that predate verification may not have this key.
        if not user_data.get('email_verified', True):
            current_app.logger.info(f"Login blocked - unverified email: {email}")
            flash('Please verify your email before logging in. You can resend the verification email below.', 'warning')
            return render_template('login.html', email=email, show_resend_verification=True)

        try:
            user = User(user_data)
            login_user(user, remember=remember_me)
            current_app.logger.info(f"User logged in successfully: {email}")
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as e:
            current_app.logger.error(f"Failed to create user object for {email}: {e}")
            flash('Account data is corrupted. Please contact support.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    email = current_user.email if current_user.is_authenticated else "unknown"
    logout_user()
    current_app.logger.info(f"User logged out: {email}")
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.home'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            date_of_birth = request.form.get('date_of_birth', '').strip()
            phone = request.form.get('phone', '').strip()

            if not first_name or not last_name:
                flash('First and last name are required.', 'danger')
                return render_template('profile.html'), 400

            if not validate_name(first_name) or not validate_name(last_name):
                flash("Names may only contain letters, spaces, hyphens, and apostrophes.", 'danger')
                return render_template('profile.html'), 400

            if not validate_date_of_birth(date_of_birth):
                flash('Enter a valid birth date in YYYY-MM-DD format (age must be between 13 and 120).', 'danger')
                return render_template('profile.html'), 400

            if not validate_phone(phone):
                flash('Please enter a valid phone number.', 'danger')
                return render_template('profile.html'), 400

            updated_user = store.update_user(current_user.email, {
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'phone': phone,
            })
            if not updated_user:
                flash('We could not update your profile because your account was not found. Please log in again.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))

            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            user_data = store.get_user(current_user.email)
            if not user_data:
                flash('Your account was not found. Please log in again.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))

            stored_password_hash = user_data.get('password')
            if not stored_password_hash or not check_password_hash(stored_password_hash, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))

            if not validate_password(new_password):
                flash('New password must be at least 8 characters long.', 'danger')
                return redirect(url_for('auth.profile'))

            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('auth.profile'))

            if new_password == current_password:
                flash('New password must be different from your current password.', 'danger')
                return redirect(url_for('auth.profile'))

            updated_user = store.update_user(current_user.email, {
                'password': generate_password_hash(new_password),
            })
            if not updated_user:
                flash('We could not change your password because your account was not found. Please log in again.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))

            flash('Password changed successfully.', 'success')

        else:
            flash('Unknown profile action.', 'warning')

        return redirect(url_for('auth.profile'))

    return render_template('profile.html')


@bp.route('/verify-email/<token>')
def verify_email(token):
    """Handle email verification link clicks."""
    verified_email = verify_token(token)
    if not verified_email:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))

    email = normalize_email(verified_email)

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
@limiter.limit("30 per minute", methods=["POST"])
def resend_verification():
    """Resend the verification email."""
    email = normalize_email(request.form.get('email', ''))
    if not validate_email(email):
        flash('Please provide a valid email address.', 'danger')
        return redirect(url_for('auth.login'))

    user_data = store.get_user(email)
    if not user_data:
        # Don't reveal whether the account exists
        flash('If an account with that email exists, a verification email has been sent.', 'info')
        return redirect(url_for('auth.login'))

    if user_data.get('email_verified'):
        flash('Your email is already verified.', 'info')
        return redirect(url_for('auth.login'))

    if send_verification_email(email):
        flash('If an account with that email exists, a verification email has been sent.', 'info')
    else:
        flash('We could not send a verification email right now. Please try again shortly.', 'danger')
    return redirect(url_for('auth.login'))
