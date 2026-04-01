from apps import create_app


class CsrfEnabledTestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


def test_login_requires_csrf_token_when_enabled():
    app = create_app(config_class=CsrfEnabledTestConfig)
    client = app.test_client()

    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 400
