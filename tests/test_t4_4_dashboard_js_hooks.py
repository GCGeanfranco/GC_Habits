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


def test_name_input_has_id_habit_name(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert 'name="name" maxlength="100" required id="habit-name"' in body


def test_word_counter_present_with_initial_value(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert 'id="word-counter"' in body
    assert "0 / 8 palabras" in body


def test_mark_done_button_has_btn_mark_done_class(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert 'class="btn-mark-done"' in body
    assert body.count('class="btn-mark-done"') == 1


def test_mark_done_btn_mark_done_class_scales_with_habits(client, data_dir):
    _write_user_file(
        data_dir,
        [
            _make_habit("idfirst01", "Estudiar Python"),
            _make_habit("idsecond2", "Correr"),
        ],
    )
    body = _dashboard(client)
    assert body.count('class="btn-mark-done"') == 2


def test_habit_name_wrapped_with_class_and_title(client, data_dir):
    _write_user_file(data_dir, [_make_habit()])
    body = _dashboard(client)
    assert '<span class="habit-name" title="Estudiar Python">Estudiar Python</span>' in body