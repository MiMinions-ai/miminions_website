from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from types import SimpleNamespace
import hashlib
import uuid

from apps.auth import bp
from apps.extensions import limiter
import apps.store as store
from apps.models import User
from apps.utils import (
    normalize_email,
    validate_date_of_birth,
    validate_email,
    get_password_validation_errors,
    validate_max_length,
    validate_name,
    validate_password,
    validate_phone,
)
from apps.email_service import send_verification_email, verify_token


def _email_fingerprint(email):
    normalized = normalize_email(email)
    if not normalized:
        return "unknown"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:12]


def _login_account_key():
    normalized = normalize_email(request.form.get('email', ''))
    if not normalized:
        return f"account:unknown:{request.remote_addr or '127.0.0.1'}"
    return f"account:{normalized}"


def _deduct_on_failed_auth(response):
    return response.status_code >= 400

@bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("60 per minute", methods=["POST"])
def signup():
    form_data = {
        'first_name': request.form.get('first_name', '').strip(),
        'last_name': request.form.get('last_name', '').strip(),
        'date_of_birth': request.form.get('date_of_birth', '').strip(),
        'email': normalize_email(request.form.get('email', '')),
    }

    if request.method == 'POST':
        email = form_data['email']
        password = request.form.get('password', '')  # Do not sanitize password, it gets hashed

        email_fp = _email_fingerprint(email)
        current_app.logger.info("Signup attempt for account=%s", email_fp)

        # Validate email format
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        # Strict fail-fast validation: never auto-correct invalid names.
        first_name = form_data['first_name']
        last_name = form_data['last_name']

        if not first_name or not last_name:
            flash('Please enter your first and last name.', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        if not validate_max_length(first_name, 100) or not validate_max_length(last_name, 100):
            flash('First and last names must be 100 characters or fewer.', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        if not validate_name(first_name) or not validate_name(last_name):
            flash("Names may only contain letters, spaces, hyphens, and apostrophes.", 'danger')
            return render_template('signup.html', form_data=form_data), 400

        # Validate password length
        if not validate_password(password):
            for err in get_password_validation_errors(password):
                flash(err, 'danger')
            return render_template('signup.html', form_data=form_data), 400

        # Validate passwords match
        confirm_password = request.form.get('confirm_password', '')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        date_of_birth = form_data['date_of_birth']

        if not date_of_birth:
            flash('Please enter your date of birth.', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        if not validate_date_of_birth(date_of_birth):
            flash('Enter a valid birth date in YYYY-MM-DD format (age must be between 13 and 120).', 'danger')
            return render_template('signup.html', form_data=form_data), 400

        user_data = store.get_user(email)

        if user_data:
            current_app.logger.warning("Signup failed - account already exists: %s", email_fp)
            flash('An account with this email already exists.', 'danger')
            return render_template('signup.html', form_data=form_data)

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
            current_app.logger.error("Signup failed - database create error for account=%s", email_fp)
            flash('Registration failed due to a database error. Please try again.', 'danger')
            return render_template('signup.html', form_data=form_data)
            
        current_app.logger.info("New user registered: %s", email_fp)

        # Send verification email
        email_sent = send_verification_email(email)
        if email_sent:
            flash('Registration successful! Please check your email to verify your account, then log in.', 'success')
        else:
            flash('Registration successful, but we could not send the verification email. Please use resend verification from login.', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', form_data=form_data)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("30 per minute", methods=["POST"], deduct_when=_deduct_on_failed_auth)
@limiter.limit("12 per 15 minute", methods=["POST"], deduct_when=_deduct_on_failed_auth)
@limiter.limit("8 per 15 minute", methods=["POST"], key_func=_login_account_key, deduct_when=_deduct_on_failed_auth)
def login():
    if request.method == 'POST':
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        remember_me = 'remember_me' in request.form
        email_fp = _email_fingerprint(email)

        current_app.logger.info("Login attempt for account=%s", email_fp)

        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html', email=email), 400

        user_data = store.get_user(email)

        if not user_data:
            current_app.logger.warning("Login failed - account not found: %s", email_fp)
            flash('No account found with that email.', 'danger')
            return render_template('login.html', email=email), 401

        stored_password_hash = user_data.get("password")
        if not stored_password_hash or not check_password_hash(stored_password_hash, password):
            current_app.logger.warning("Login failed - incorrect password for account=%s", email_fp)
            flash('Incorrect password.', 'danger')
            return render_template('login.html', email=email), 401

        if not user_data.get('is_active', True):
            current_app.logger.warning("Login blocked - inactive account=%s", email_fp)
            flash('Your account is inactive. Please contact support.', 'danger')
            return render_template('login.html', email=email), 403

        # Legacy accounts that predate verification may not have this key.
        if not user_data.get('email_verified', True):
            current_app.logger.info("Login blocked - unverified account=%s", email_fp)
            flash('Please verify your email before logging in. You can resend the verification email below.', 'warning')
            return render_template('login.html', email=email, show_resend_verification=True), 403

        try:
            user = User(user_data)
            login_user(user, remember=remember_me)
            current_app.logger.info("User logged in successfully: %s", email_fp)
            current_app.logger.debug("Login success detail email=%s", email)
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as e:
            current_app.logger.error("Failed to create user object for account=%s: %s", email_fp, e)
            flash('Account data is corrupted. Please contact support.', 'danger')
            return render_template('login.html', email=email), 500

    return render_template('login.html')

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    email = current_user.email if current_user.is_authenticated else "unknown"
    email_fp = _email_fingerprint(email)
    logout_user()
    current_app.logger.info("User logged out: %s", email_fp)
    flash('Logged out successfully', 'info')
    return redirect(url_for('main.home'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    submitted_profile = {
        'first_name': request.form.get('first_name', '').strip(),
        'last_name': request.form.get('last_name', '').strip(),
        'date_of_birth': request.form.get('date_of_birth', '').strip(),
        'phone': request.form.get('phone', '').strip(),
    }

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            first_name = submitted_profile['first_name']
            last_name = submitted_profile['last_name']
            date_of_birth = submitted_profile['date_of_birth']
            phone = submitted_profile['phone']

            if not first_name or not last_name:
                flash('First and last name are required.', 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

            if not validate_max_length(first_name, 100) or not validate_max_length(last_name, 100):
                flash('First and last names must be 100 characters or fewer.', 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

            if not validate_name(first_name) or not validate_name(last_name):
                flash("Names may only contain letters, spaces, hyphens, and apostrophes.", 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

            if not validate_date_of_birth(date_of_birth):
                flash('Enter a valid birth date in YYYY-MM-DD format (age must be between 13 and 120).', 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

            if not validate_max_length(phone, 20):
                flash('Phone number must be 20 characters or fewer.', 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

            if not validate_phone(phone):
                flash('Please enter a valid phone number.', 'danger')
                return render_template('profile.html', submitted_profile=submitted_profile), 400

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
                for err in get_password_validation_errors(new_password):
                    flash(err, 'danger')
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

    return render_template('profile.html', submitted_profile=submitted_profile)


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
