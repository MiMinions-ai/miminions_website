import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _is_set(name):
    value = os.getenv(name)
    return bool(value and value.strip())


def _require_env(names, context):
    missing = [name for name in names if not _is_set(name)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables for {context}: {', '.join(missing)}"
        )


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
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
    flask_env = os.getenv("FLASK_ENV", "local").lower()
    force_local = "--local" in sys.argv
    force_test = "--test" in sys.argv

    if force_test:
        logger.warning("Running in testing mode (--test)")
        return TestingConfig

    if flask_env == "production" and not force_local:
        _require_env(
            ["SECRET_KEY", "JWT_SECRET_KEY", "RESEND_API_KEY", "MAIL_FROM", "CONTACT_EMAIL"],
            "production",
        )
        return ProductionConfig

    _require_env(["SECRET_KEY"], "development/local")
    if not _is_set("JWT_SECRET_KEY"):
        logger.warning("JWT_SECRET_KEY not set in development/local; falling back to SECRET_KEY")

    logger.info("Running in development mode (FLASK_ENV=%s)", flask_env)
    return DevelopmentConfig
