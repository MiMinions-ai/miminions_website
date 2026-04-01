from werkzeug.security import generate_password_hash

import apps.auth.routes as auth_routes
import apps.main.routes as main_routes


def _verified_user(email="user@example.com"):
    return {
        "id": "u-1",
        "email": email,
        "password": generate_password_hash("StrongPass123!"),
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "2000-01-01",
        "phone": "",
        "is_active": True,
        "email_verified": True,
    }


def test_signup_success(client, monkeypatch):
    monkeypatch.setattr(auth_routes.store, "get_user", lambda email: None)
    monkeypatch.setattr(auth_routes.store, "add_user", lambda data: True)
    monkeypatch.setattr(auth_routes, "send_verification_email", lambda email: True)

    response = client.post(
        "/signup",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "2000-01-01",
            "email": "jane@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Registration successful" in response.data


def test_login_success(client, monkeypatch):
    monkeypatch.setattr(auth_routes.store, "get_user", lambda email: _verified_user(email))

    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "StrongPass123!"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_login_unverified_user_blocked(client, monkeypatch):
    user = _verified_user("pending@example.com")
    user["email_verified"] = False
    monkeypatch.setattr(auth_routes.store, "get_user", lambda email: user)

    response = client.post(
        "/login",
        data={"email": "pending@example.com", "password": "StrongPass123!"},
        follow_redirects=True,
    )

    assert response.status_code == 403
    assert b"Please verify your email" in response.data


def test_contact_submission_success(client, monkeypatch):
    monkeypatch.setattr(main_routes, "send_contact_email", lambda n, e, p, m: True)

    response = client.post(
        "/contact",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1 555 123 4567",
            "message": "Hello, I have a question.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Thank you for your message" in response.data


def test_health_does_not_leak_internal_error(client, monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("sensitive-db-error")

    monkeypatch.setattr(main_routes.users_table, "get_item", _boom)

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["error"] == "database unavailable"
