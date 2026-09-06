import json

import pytest
from flask import session
from flask_wtf.csrf import generate_csrf

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


def _valid_csrf(app):
    with app.test_request_context():
        signed = generate_csrf()
        raw = session["csrf_token"]
    return signed, raw


def _post_habit(app, client, name):
    _login(client)
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw
    return client.post("/habits", data={"name": name, "csrf_token": signed})


def _user_data(data_dir, user_id="user_1"):
    return json.loads((data_dir / f"{user_id}.json").read_text(encoding="utf-8"))


def _write_user_file(data_dir, habits, user_id="user_1"):
    (data_dir / f"{user_id}.json").write_text(
        json.dumps({"habits": habits, "metadata": {}}), encoding="utf-8"
    )


def _make_habit(name, normalized):
    return {
        "id": "existing01",
        "name": name,
        "normalized_name": normalized,
        "current_streak": 0,
        "record_streak": 0,
        "lifelines_available": 0,
        "lifelines_unlocked": False,
        "lifelines_unlock_date": None,
        "lifelines_last_recovery_date": None,
        "last_processed_date": None,
        "last_day_status": "none",
    }


def _flashes(client):
    with client.session_transaction() as sess:
        return sess.get("_flashes", [])


def test_create_habit_success(app, client, data_dir):
    storage.create_user_file("user_1")
    resp = _post_habit(app, client, "Estudiar Python")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    data = _user_data(data_dir)
    assert len(data["habits"]) == 1
    assert data["habits"][0]["name"] == "Estudiar Python"
    assert data["habits"][0]["normalized_name"] == "estudiar_python"


def test_create_habit_duplicate_not_persisted(app, client, data_dir):
    _write_user_file(data_dir, [_make_habit("Estudiar Python", "estudiar_python")])
    resp = _post_habit(app, client, "Estudiar Python")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    data = _user_data(data_dir)
    assert len(data["habits"]) == 1
    assert any(category == "error" for category, _ in _flashes(client))


def test_create_habit_limit_not_persisted(app, client, data_dir):
    habits = [_make_habit(f"Hábito {i}", f"habito_{i}") for i in range(10)]
    _write_user_file(data_dir, habits)
    resp = _post_habit(app, client, "Hábito 11")
    assert resp.status_code == 302
    data = _user_data(data_dir)
    assert len(data["habits"]) == 10
    assert any(category == "error" for category, _ in _flashes(client))


def test_create_habit_invalid_name_not_persisted(app, client, data_dir):
    storage.create_user_file("user_1")
    resp = _post_habit(app, client, "   ")
    assert resp.status_code == 302
    data = _user_data(data_dir)
    assert data["habits"] == []


def test_create_habit_without_csrf_returns_400(app, client, data_dir):
    storage.create_user_file("user_1")
    _login(client)
    resp = client.post("/habits", data={"name": "Estudiar Python"})
    assert resp.status_code == 400


def test_create_habit_anonymous_redirects_to_login(app, client, data_dir):
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw
    resp = client.post("/habits", data={"name": "Estudiar Python", "csrf_token": signed})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert not (data_dir / "user_1.json").exists()