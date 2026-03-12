from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Updated to use blueprint endpoint

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)
