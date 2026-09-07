import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_csp_allows_google_fonts_style(client):
    resp = client.get("/login")
    csp = resp.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "style-src 'self' https://fonts.googleapis.com" in csp


def test_csp_allows_google_fonts_font(client):
    resp = client.get("/login")
    csp = resp.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "font-src 'self' https://fonts.gstatic.com" in csp


def test_csp_default_src_and_script_src_untouched(client):
    resp = client.get("/login")
    csp = resp.headers.get("Content-Security-Policy")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "unsafe-inline" not in csp
