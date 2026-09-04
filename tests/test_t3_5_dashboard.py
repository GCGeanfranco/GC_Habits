import json

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


def _login(client, user_id="user_1"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_dashboard_redirects_anonymous_to_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_dashboard_empty_state_shows_invitation(client, data_dir):
    storage.create_user_file("user_1")
    _login(client)

    resp = client.get("/dashboard")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Crea tu primer hábito" in body
    assert "Detectamos un problema" not in body


def test_dashboard_shows_recovery_message_on_corrupt_file(client, data_dir):
    (data_dir / "user_1.json").write_text("{corrupt", encoding="utf-8")
    _login(client)

    resp = client.get("/dashboard")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Detectamos un problema con tus datos guardados y los reiniciamos." in body
    assert "Crea tu primer hábito" not in body
    backups = list(data_dir.glob("user_1.json.corrupt.*"))
    assert len(backups) == 1


def test_dashboard_with_habits_lists_them(client, data_dir):
    (data_dir / "user_1.json").write_text(
        json.dumps({"habits": [{"name": "correr"}], "metadata": {}}), encoding="utf-8"
    )
    _login(client)

    resp = client.get("/dashboard")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "correr" in body
    assert "Crea tu primer hábito" not in body
    assert "Detectamos un problema" not in body


def test_dashboard_has_logout_form_with_csrf(client, data_dir):
    storage.create_user_file("user_1")
    _login(client)

    resp = client.get("/dashboard")

    body = resp.get_data(as_text=True)
    assert 'action="/logout"' in body
    assert 'name="csrf_token"' in body