from flask import render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import current_user
from apps.main import bp
from apps.store import users_table
from apps.email_service import send_contact_email
from apps.utils import validate_email

@bp.route('/')
def home():
    return render_template('landing.html')

@bp.route('/health')
def health():
    """Health check endpoint for Elastic Beanstalk."""
    try:
        # Test DynamoDB connection with a health check item
        users_table.get_item(Key={"email": "__healthcheck__"})
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/use-cases')
def use_cases():
    return render_template('use-cases.html')

@bp.route('/documentation')
def documentation():
    return render_template('documentation.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please fill in all required fields.', 'danger')
            return render_template('contact.html')

        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('contact.html')

        success = send_contact_email(name, email, phone, message)
        if success:
            current_app.logger.info(f"Contact form submitted by {email}")
            flash('Thank you for your message! We will get back to you soon.', 'success')
        else:
            current_app.logger.error(f"Failed to send contact form email from {email}")
            flash('Something went wrong sending your message. Please try again later.', 'danger')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

@bp.route('/faqs')
def faq():
    return render_template('faqs.html')
