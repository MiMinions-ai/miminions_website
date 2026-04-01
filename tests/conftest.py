import os
import sys

# Add project root to path before importing apps
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from apps import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


@pytest.fixture
def app():
    app = create_app(config_class=TestConfig)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
