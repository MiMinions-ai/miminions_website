import os

from flask import request
from flask_limiter import Limiter
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


def _client_ip_for_rate_limit():
    """Resolve a stable client IP for limiter keys.

    In production behind a trusted proxy, `request.access_route` reflects the
    forwarded chain after ProxyFix normalization. In local/dev, use remote_addr.
    """
    env = os.getenv("FLASK_ENV", "local").lower()
    if env == "production" and request.access_route:
        return request.access_route[0]
    return request.remote_addr or "127.0.0.1"


def _limiter_storage_uri():
    env = os.getenv("FLASK_ENV", "local").lower()
    redis_url = os.getenv("REDIS_URL", "").strip()
    if env == "production" and redis_url:
        return redis_url
    return "memory://"


login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Updated to use blueprint endpoint

csrf = CSRFProtect()

limiter = Limiter(
    key_func=_client_ip_for_rate_limit, storage_uri=_limiter_storage_uri(), default_limits=[]
)
