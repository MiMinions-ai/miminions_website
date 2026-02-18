import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Default secure to True, override in specific configs if needed
    SESSION_COOKIE_SECURE = True

    # Resend email config
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    MAIL_FROM = os.getenv("MAIL_FROM", "info@miminions.ai")
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "info@miminions.ai")

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = "dev-secret-key-for-testing-only"

class ProductionConfig(Config):
    """Production configuration."""
    SESSION_COOKIE_SECURE = True

def get_config():
    """
    Determine configuration based on environment and arguments.
    """
    # Check FLASK_ENV environment variable
    flask_env = os.getenv("FLASK_ENV", "local").lower()
    
    # Also check for command-line flags
    load_local = any(arg in sys.argv for arg in ["--local", "--test", "--deploy"])
    
    if flask_env == "production" and not load_local:
        # Validate all required production secrets
        missing = [k for k in ("SECRET_KEY", "JWT_SECRET_KEY", "RESEND_API_KEY") if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing required environment variables for production: {', '.join(missing)}")
        return ProductionConfig
    
    print(f"WARNING: Running in Local/Development Mode (FLASK_ENV={flask_env}) - Security headers relaxed")
    return TestingConfig
