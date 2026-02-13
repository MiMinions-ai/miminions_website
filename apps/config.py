import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Default secure to True, override in specific configs if needed
    SESSION_COOKIE_SECURE = True

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
        # Check if Secret Key is set for production
        if not os.getenv("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY environment variable is required for production")
        return ProductionConfig
    
    print(f"WARNING: Running in Local/Development Mode (FLASK_ENV={flask_env}) - Security headers relaxed")
    return TestingConfig
