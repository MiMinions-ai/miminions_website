from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user
from apps.main import bp

@bp.route('/')
def home():
    return render_template('landing.html')

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
        # In a real application, you would send an email here
        current_app.logger.info(f"Contact form submitted by {request.form.get('email')}")
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

@bp.route('/faqs')
def faq():
    return render_template('faqs.html')
