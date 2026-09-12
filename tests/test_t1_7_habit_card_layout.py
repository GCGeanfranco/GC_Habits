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


def _make_habit(hid="existing01", name="Estudiar Python", **overrides):
    habit = {
        "id": hid,
        "name": name,
        "normalized_name": "estudiar_python",
        "current_streak": 3,
        "record_streak": 3,
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


def _dashboard(client):
    _login(client)
    return client.get("/dashboard").get_data(as_text=True)


def test_habit_name_and_stats_grouped_in_habit_info(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert '<div class="habit-info">' in body
    assert '<span class="habit-name" title="Estudiar Python">Estudiar Python</span>' in body
    assert '<span class="habit-stats">Racha: 3 — Récord: 3</span>' in body


def test_habit_stats_not_coupled_to_name_in_plain_text(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert "— Racha:" not in body
    assert "Racha: 3 — Récord: 3" in body


def test_lifelines_and_csrf_count_stay_intact(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert body.count('class="lifeline lifeline-locked"') == 2
    assert "3/15 días para desbloquear" in body
    assert body.count('name="csrf_token"') == 3