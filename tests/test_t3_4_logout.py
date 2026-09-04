import pytest
from flask import session
from flask_wtf.csrf import generate_csrf

from app import create_app


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"


def _valid_csrf(app):
    with app.test_request_context():
        signed = generate_csrf()
        raw = session["csrf_token"]
    return signed, raw


def test_logout_post_with_csrf_returns_302_and_clears_session(app, client):
    _login(client)
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw

    resp = client.post("/logout", data={"csrf_token": signed})

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_post_without_csrf_returns_400(client):
    _login(client)
    resp = client.post("/logout")
    assert resp.status_code == 400


def test_logout_get_returns_405(client):
    _login(client)
    resp = client.get("/logout")
    assert resp.status_code == 405


def test_logout_requires_authentication(app, client):
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw

    resp = client.post("/logout", data={"csrf_token": signed})

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]