import json
from datetime import datetime, timedelta, timezone

import pytest
from flask import session

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


def _make_habit(name, normalized, **overrides):
    habit = {
        "id": "existing01",
        "name": name,
        "normalized_name": normalized,
        "current_streak": 7,
        "record_streak": 9,
        "lifelines_available": 0,
        "lifelines_unlocked": False,
        "lifelines_unlock_date": None,
        "lifelines_last_recovery_date": None,
        "last_processed_date": None,
        "last_day_status": "none",
    }
    habit.update(overrides)
    return habit


def _write_user_file(data_dir, habits, user_id="user_1"):
    (data_dir / f"{user_id}.json").write_text(
        json.dumps({"habits": habits, "metadata": {}}), encoding="utf-8"
    )


def _get_dashboard(client):
    _login(client)
    return client.get("/dashboard")


def test_dashboard_empty_still_shows_invitation(client, data_dir):
    storage.create_user_file("user_1")
    resp = _get_dashboard(client)
    assert resp.status_code == 200
    assert "Crea tu primer hábito" in resp.get_data(as_text=True)


def test_dashboard_recalculates_streak_to_zero_on_gap(client, data_dir):
    old = (datetime.now(timezone.utc).date() - timedelta(days=5)).isoformat()
    first = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        id="idfirst01",
        current_streak=7,
        last_processed_date=old,
        last_day_status="hecho",
    )
    second = _make_habit(
        "Correr",
        "correr",
        id="idsecond2",
        current_streak=4,
        last_processed_date=old,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [first, second])
    resp = _get_dashboard(client)
    body = resp.get_data(as_text=True)
    assert body.count("Racha: 0") == 2


def test_dashboard_does_not_persist_recalculation(client, data_dir, app):
    old = (datetime.now(timezone.utc).date() - timedelta(days=5)).isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=7,
        last_processed_date=old,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _get_dashboard(client)
    assert resp.status_code == 200
    assert "Racha: 0" in resp.get_data(as_text=True)
    with app.test_request_context():
        session["user_id"] = "user_1"
        persisted = storage.load()
    assert persisted["habits"][0]["current_streak"] == 7


def test_dashboard_no_gap_shows_stored_streak(client, data_dir):
    today = datetime.now(timezone.utc).date().isoformat()
    habit = _make_habit(
        "Estudiar Python",
        "estudiar_python",
        current_streak=5,
        last_processed_date=today,
        last_day_status="hecho",
    )
    _write_user_file(data_dir, [habit])
    resp = _get_dashboard(client)
    assert "Racha: 5" in resp.get_data(as_text=True)