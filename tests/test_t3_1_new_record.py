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


def test_first_mark_flashes_new_record(app, client, data_dir):
    habit = _make_habit("Estudiar Python", "estudiar_python")
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    flashes = _flashes(client)
    assert ("new_record", habit["id"]) in flashes
    assert any(category == "success" for category, _ in flashes)


def test_equal_previous_record_after_reset_flashes(app, client, data_dir, monkeypatch):
    day0 = datetime.now(timezone.utc).date() - timedelta(days=8)
    days = iter([day0 + timedelta(days=i) for i in range(1, 6)])
    monkeypatch.setattr("app.web.routes._today_utc", lambda: days.__next__())
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=0,
        record_streak=5,
        last_processed_date=day0.isoformat(),
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    for _ in range(4):
        resp = _post_done(app, client, habit["id"])
        assert resp.status_code == 302
        assert ("new_record", habit["id"]) not in _flashes(client)
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    flashes = _flashes(client)
    assert ("new_record", habit["id"]) in flashes
    assert any(category == "success" for category, _ in flashes)


def test_streak_below_previous_record_does_not_flash(app, client, data_dir):
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=2,
        record_streak=10,
        last_processed_date=yesterday,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    flashes = _flashes(client)
    assert ("new_record", habit["id"]) not in flashes
    assert any(category == "success" for category, _ in flashes)


def test_already_marked_today_does_not_flash_new_record(app, client, data_dir):
    today = datetime.now(timezone.utc).date().isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=5,
        record_streak=5,
        last_processed_date=today,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302
    flashes = _flashes(client)
    assert ("new_record", habit["id"]) not in flashes
    assert any(category == "info" for category, _ in flashes)