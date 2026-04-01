from apps import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


import pytest


@pytest.fixture
def app():
    app = create_app(config_class=TestConfig)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
