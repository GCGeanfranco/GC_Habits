import re

import pytest

from app import create_app

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


@pytest.fixture()
def client():
    return create_app().test_client()


def test_login_keeps_google_login_link_with_correct_href(client):
    resp = client.get("/login")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    match = re.search(
        r'<a href="([^"]+)" class="btn-google">Iniciar sesión con Google</a>',
        html,
    )
    assert match is not None
    href = match.group(1)
    assert href.startswith(GOOGLE_AUTH_URL + "?")
    assert "client_id=test-client-id" in href


def test_login_shows_error_message_when_error_param_passed(client):
    resp = client.get("/login?error=auth_failed")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "No se pudo iniciar sesión. Inténtalo de nuevo." in html


def test_login_without_error_shows_no_error_message(client):
    resp = client.get("/login")
    assert "No se pudo iniciar sesión. Inténtalo de nuevo." not in resp.get_data(
        as_text=True
    )


def test_login_inherits_stylesheet_link_and_logo_from_base(client):
    resp = client.get("/login")
    html = resp.get_data(as_text=True)
    assert '<link rel="stylesheet" href="/static/css/style.css">' in html
    assert 'src="/static/img/logo_gc_habits_transparent.png"' in html


def test_login_wrapper_uses_login_page_class(client):
    resp = client.get("/login")
    html = resp.get_data(as_text=True)
    assert 'class="login-page"' in html