import time

import pytest

from app import create_app
from app import storage


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "users"
    d.mkdir()
    monkeypatch.setattr(storage, "USER_DATA_DIR", d)
    return d


def test_session_cookie_is_http_only(client):
    resp = client.get("/login")
    assert "HttpOnly" in resp.headers.get("Set-Cookie", "")


def test_stale_session_treated_as_unauthenticated(client, data_dir):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"
        sess["last_activity"] = time.time() - 16 * 24 * 3600

    resp = client.get("/dashboard")

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_session_without_last_activity_is_accepted(client, data_dir):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"

    resp = client.get("/dashboard")

    assert resp.status_code == 200


def test_fresh_session_stays_authenticated(client, data_dir):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"
        sess["last_activity"] = time.time()

    resp = client.get("/dashboard")

    assert resp.status_code == 200


def test_activity_updates_last_activity(client, data_dir):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"
        sess["last_activity"] = time.time() - 3600

    client.get("/dashboard")

    with client.session_transaction() as sess:
        assert time.time() - sess["last_activity"] < 60