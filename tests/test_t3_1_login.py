import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_login_returns_200_with_google_button(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "Iniciar sesión con Google" in resp.get_data(as_text=True)


def test_login_contains_oauth_url(client):
    resp = client.get("/login")
    assert "accounts.google.com" in resp.get_data(as_text=True)


def test_login_with_auth_failed_error_shows_message(client):
    resp = client.get("/login?error=auth_failed")
    assert resp.status_code == 200
    assert "No se pudo iniciar sesión" in resp.get_data(as_text=True)


def test_login_without_error_shows_no_error_message(client):
    resp = client.get("/login")
    assert "No se pudo iniciar sesión" not in resp.get_data(as_text=True)