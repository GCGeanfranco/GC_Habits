import json
from datetime import datetime, timedelta, timezone

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


def _post_done(app, client, habit_id):
    _login(client)
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw
    return client.post(f"/habits/{habit_id}/done", data={"csrf_token": signed})


def _user_data(data_dir, user_id="user_1"):
    return json.loads((data_dir / f"{user_id}.json").read_text(encoding="utf-8"))


def _write_user_file(data_dir, habits, user_id="user_1"):
    (data_dir / f"{user_id}.json").write_text(
        json.dumps({"habits": habits, "metadata": {}}), encoding="utf-8"
    )


def _make_habit(name, normalized, **overrides):
    habit = {
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
    habit.update(overrides)
    return habit


def _flashes(client):
    with client.session_transaction() as sess:
        return sess.get("_flashes", [])


def test_mark_habit_done_success(app, client, data_dir):
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=5,
        record_streak=12,
        last_processed_date=yesterday,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    data = _user_data(data_dir)
    assert data["habits"][0]["current_streak"] == 6
    assert data["habits"][0]["last_day_status"] == "hecho"
    assert any(category == "success" for category, _ in _flashes(client))


def test_mark_habit_done_already_marked_today(app, client, data_dir):
    today = datetime.now(timezone.utc).date().isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=5,
        last_processed_date=today,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    data = _user_data(data_dir)
    assert data["habits"][0]["current_streak"] == 5
    assert any(category == "info" for category, _ in _flashes(client))


def test_mark_habit_done_unknown_id_returns_404(app, client, data_dir):
    _write_user_file(data_dir, [_make_habit("Estudiar Python", "estudiar_python")])
    resp = _post_done(app, client, "doesnotexist")
    assert resp.status_code == 404


def test_mark_habit_done_without_csrf_returns_400(app, client, data_dir):
    _write_user_file(data_dir, [_make_habit("Estudiar Python", "estudiar_python")])
    _login(client)
    resp = client.post("/habits/someid/done")
    assert resp.status_code == 400


def test_mark_habit_done_anonymous_redirects_to_login(app, client, data_dir):
    signed, raw = _valid_csrf(app)
    with client.session_transaction() as sess:
        sess["csrf_token"] = raw
    resp = client.post("/habits/someid/done", data={"csrf_token": signed})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert not (data_dir / "user_1.json").exists()


def test_mark_one_habit_does_not_affect_others(app, client, data_dir):
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    first = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        id="idfirst01",
        current_streak=5,
        last_processed_date=yesterday,
        last_day_status="hecho",
    )
    second = _make_habit(
        "Correr",
        "correr",
        id="idsecond2",
        current_streak=3,
        last_processed_date=yesterday,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [first, second])
    resp = _post_done(app, client, first["id"])
    assert resp.status_code == 302
    data = _user_data(data_dir)
    by_id = {h["id"]: h for h in data["habits"]}
    assert by_id[first["id"]]["current_streak"] == 6
    assert by_id[second["id"]]["current_streak"] == 3
    assert by_id[second["id"]]["last_day_status"] == "hecho"