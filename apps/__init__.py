import logging
from flask import Flask, request, render_template
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from apps.config import get_config
from apps.extensions import login_manager, csrf, limiter

def create_app(config_class=None):
    if config_class is None:
        config_class = get_config()

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Trust X-Forwarded-Proto/Host from the EB load balancer so that
    # url_for(..., _external=True) generates https:// URLs in production.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    configure_logging(app)
    
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from apps.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from apps.main import bp as main_bp
    app.register_blueprint(main_bp)

    register_handlers(app)

    return app

def configure_logging(app):
    if not app.logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    app.logger.setLevel(logging.INFO)

def register_handlers(app):
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
        try:
            if current_user.is_authenticated:
                response.headers["Cache-Control"] = "no-store"
        except:
             pass
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {request.path}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        return render_template('500.html'), 500
