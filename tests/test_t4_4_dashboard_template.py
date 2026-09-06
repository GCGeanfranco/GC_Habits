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


def _make_habit(hid, name, normalized):
    return {
        "id": hid,
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


def _write_user_file(data_dir, habits, user_id="user_1"):
    (data_dir / f"{user_id}.json").write_text(
        json.dumps({"habits": habits, "metadata": {}}), encoding="utf-8"
    )


def _get_dashboard(client):
    _login(client)
    return client.get("/dashboard")


def test_dashboard_has_create_habit_form(client, data_dir):
    _write_user_file(data_dir, [_make_habit("idfirst01", "Estudiar Python", "estudiar_python")])
    body = _get_dashboard(client).get_data(as_text=True)
    assert 'action="/habits"' in body
    assert 'name="name"' in body
    assert "Crear hábito" in body
    assert 'name="csrf_token"' in body


def test_dashboard_has_done_button_per_habit_with_correct_id(client, data_dir):
    first = _make_habit("idfirst01", "Estudiar Python", "estudiar_python")
    second = _make_habit("idsecond2", "Correr", "correr")
    _write_user_file(data_dir, [first, second])
    body = _get_dashboard(client).get_data(as_text=True)
    assert 'action="/habits/idfirst01/done"' in body
    assert 'action="/habits/idsecond2/done"' in body
    assert body.count('action="/habits/idfirst01/done"') == 1
    assert body.count('action="/habits/idsecond2/done"') == 1
    assert "Marcar como hecho" in body


def test_dashboard_all_forms_include_csrf_token(client, data_dir):
    first = _make_habit("idfirst01", "Estudiar Python", "estudiar_python")
    second = _make_habit("idsecond2", "Correr", "correr")
    _write_user_file(data_dir, [first, second])
    body = _get_dashboard(client).get_data(as_text=True)
    assert body.count('name="csrf_token"') == 4


def test_dashboard_renders_flash_messages(client, data_dir):
    _write_user_file(data_dir, [_make_habit("idfirst01", "Estudiar Python", "estudiar_python")])
    with client.session_transaction() as sess:
        sess["_flashes"] = [("success", "Hábito 'X' creado.")]
    body = _get_dashboard(client).get_data(as_text=True)
    assert "Hábito" in body and "creado." in body
    assert "&#39;X&#39;" in body or "'X'" in body