import inspect
import json

import pytest
from flask import session

from app import create_app
from app import storage


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "users"
    d.mkdir()
    monkeypatch.setattr(storage, "USER_DATA_DIR", d)
    return d


def test_load_without_user_in_session_raises(app):
    with app.test_request_context():
        with pytest.raises(RuntimeError, match="No hay usuario en sesión"):
            storage.load()


def test_save_without_user_in_session_raises(app):
    with app.test_request_context():
        with pytest.raises(RuntimeError, match="No hay usuario en sesión"):
            storage.save({"habits": []})


def test_load_saves_only_for_session_user(app, data_dir):
    with app.test_request_context():
        session["user_id"] = "user_A"
        storage.save({"habits": [{"name": "correr"}]})
        data = storage.load()
    assert data == {"habits": [{"name": "correr"}]}
    assert (data_dir / "user_A.json").exists()
    assert [p.name for p in data_dir.glob("*.json")] == ["user_A.json"]


def test_load_reads_only_session_user_file(app, data_dir):
    (data_dir / "user_A.json").write_text(
        json.dumps({"habits": ["de A"]}), encoding="utf-8"
    )
    (data_dir / "user_B.json").write_text(
        json.dumps({"habits": ["de B"]}), encoding="utf-8"
    )
    with app.test_request_context():
        session["user_id"] = "user_A"
        assert storage.load() == {"habits": ["de A"]}


def test_operations_follow_session_user(app, data_dir):
    with app.test_request_context():
        session["user_id"] = "user_A"
        storage.save({"habits": ["de A"]})
    with app.test_request_context():
        session["user_id"] = "user_B"
        assert storage.load() == {"habits": [], "metadata": {}}
        storage.save({"habits": ["de B"]})
    assert "de A" in (data_dir / "user_A.json").read_text(encoding="utf-8")
    assert "de B" in (data_dir / "user_B.json").read_text(encoding="utf-8")


def test_load_and_save_signatures_have_no_user_id_param():
    assert "user_id" not in inspect.signature(storage.load).parameters
    assert "user_id" not in inspect.signature(storage.save).parameters