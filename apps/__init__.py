import logging
import os
import uuid
from datetime import datetime
from flask import Flask, request, render_template, g, has_request_context
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from apps.config import get_config
from apps.extensions import login_manager, csrf, limiter


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, "request_id", "-") if has_request_context() else "-"
        return True

def create_app(config_class=None):
    if config_class is None:
        config_class = get_config()

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Only trust forwarded headers in production behind a verified proxy.
    if os.getenv("FLASK_ENV", "local").lower() == "production":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    configure_logging(app)
    
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from apps.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from apps.main import bp as main_bp
    app.register_blueprint(main_bp)

    register_handlers(app)

    @app.context_processor
    def inject_template_globals():
        return {"current_year": datetime.utcnow().year}

    return app

def configure_logging(app):
    request_id_filter = RequestIdFilter()

    if not app.logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    for handler in logging.getLogger().handlers:
        handler.addFilter(request_id_filter)

    for handler in app.logger.handlers:
        handler.addFilter(request_id_filter)

    app.logger.setLevel(logging.INFO)

def register_handlers(app):
    @app.before_request
    def assign_request_id():
        incoming = request.headers.get("X-Request-ID", "").strip()
        g.request_id = incoming or str(uuid.uuid4())

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'"
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
