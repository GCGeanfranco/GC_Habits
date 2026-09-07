import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_security_headers_present_on_login(client):
    resp = client.get("/login")
    assert (
        resp.headers.get("Content-Security-Policy")
        == "default-src 'self'; script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com"
    )
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_security_headers_present_on_any_route(client):
    resp = client.get("/dashboard")
    assert resp.headers.get("Content-Security-Policy")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_session_cookie_secure_false_in_development(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    app = create_app()
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code == 200
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert "Secure" not in resp.headers.get("Set-Cookie", "")


def test_session_cookie_secure_true_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    app = create_app()
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code == 302
    assert app.config["SESSION_COOKIE_SECURE"] is True