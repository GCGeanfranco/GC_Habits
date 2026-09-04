import pytest
from flask import session
from flask_wtf.csrf import generate_csrf

from app import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.add_url_rule("/test-post", "test_post", lambda: "ok", methods=["POST"])
    app.add_url_rule("/test-get", "test_get", lambda: "ok", methods=["GET"])
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_post_without_csrf_token_returns_400(client):
    resp = client.post("/test-post")
    assert resp.status_code == 400


def test_post_with_valid_csrf_token_succeeds(app, client):
    with app.test_request_context():
        signed_token = generate_csrf()
        raw_token = session["csrf_token"]
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw_token
    resp = client.post("/test-post", data={"csrf_token": signed_token})
    assert resp.status_code == 200


def test_get_without_csrf_token_succeeds(client):
    resp = client.get("/test-get")
    assert resp.status_code == 200