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


def _make_habit(hid="existing01", name="Estudiar Python", **overrides):
    habit = {
        "id": hid,
        "name": name,
        "normalized_name": "estudiar_python",
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


def _write_user_file(data_dir, habits, user_id="user_1"):
    (data_dir / f"{user_id}.json").write_text(
        json.dumps({"habits": habits, "metadata": {}}), encoding="utf-8"
    )


def _dashboard(client):
    _login(client)
    return client.get("/dashboard")


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


def test_locked_lifelines_show_two_locked_slots_and_progress(client, data_dir):
    habit = _make_habit(current_streak=8)
    _write_user_file(data_dir, [habit])
    body = _dashboard(client).get_data(as_text=True)
    assert "8/15 días para desbloquear" in body
    assert body.count('class="lifeline lifeline-locked"') == 2


def test_unlocked_lifelines_with_one_available_shows_one_active_one_used(client, data_dir):
    habit = _make_habit(
        current_streak=15,
        record_streak=15,
        lifelines_available=1,
        lifelines_unlocked=True,
        lifelines_unlock_date="2026-01-01",
    )
    _write_user_file(data_dir, [habit])
    body = _dashboard(client).get_data(as_text=True)
    assert body.count('class="lifeline lifeline-active"') == 1
    assert body.count('class="lifeline lifeline-used"') == 1
    assert 'class="lifeline lifeline-locked"' not in body


def test_unlocked_lifelines_with_two_available_shows_two_active(client, data_dir):
    habit = _make_habit(
        current_streak=15,
        record_streak=15,
        lifelines_available=2,
        lifelines_unlocked=True,
        lifelines_unlock_date="2026-01-01",
    )
    _write_user_file(data_dir, [habit])
    body = _dashboard(client).get_data(as_text=True)
    assert body.count('class="lifeline lifeline-active"') == 2
    assert 'class="lifeline lifeline-used"' not in body


def test_new_record_badge_appears_once_then_is_consumed(app, client, data_dir):
    habit = _make_habit()
    _write_user_file(data_dir, [habit])
    resp = _post_done(app, client, habit["id"])
    assert resp.status_code == 302

    resp = client.get("/dashboard")
    assert "¡Nuevo récord!" in resp.get_data(as_text=True)

    resp = client.get("/dashboard")
    assert "¡Nuevo récord!" not in resp.get_data(as_text=True)


def test_dashboard_empty_state_still_shows_welcome(client, data_dir):
    storage.create_user_file("user_1")
    body = _dashboard(client).get_data(as_text=True)
    assert "¡Bienvenido! Crea tu primer hábito para empezar." in body


def test_dashboard_recovered_notice_still_shown(client, data_dir):
    (data_dir / "user_1.json").write_text("{corrupt", encoding="utf-8")
    body = _dashboard(client).get_data(as_text=True)
    assert "Detectamos un problema con tus datos guardados y los reiniciamos." in body


def test_dashboard_keeps_create_done_and_logout_forms(client, data_dir):
    habit = _make_habit()
    _write_user_file(data_dir, [habit])
    body = _dashboard(client).get_data(as_text=True)
    assert 'action="/habits"' in body
    assert 'name="name"' in body
    assert "Crear hábito" in body
    assert 'action="/habits/existing01/done"' in body
    assert "Marcar como hecho" in body
    assert 'action="/logout"' in body
    assert body.count('name="csrf_token"') == 3