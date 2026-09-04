import json
from datetime import datetime

import pytest

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


def _write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_user_exists_true_when_file_exists(data_dir):
    _write(data_dir / "user_A.json", {"habits": []})
    assert storage.user_exists("user_A") is True


def test_user_exists_false_when_no_file(data_dir):
    assert storage.user_exists("user_A") is False


def test_count_users_counts_only_json_files(data_dir):
    for name in ("user_1.json", "user_2.json", "user_3.json"):
        _write(data_dir / name, {"habits": []})
    (data_dir / "notes.txt").write_text("not json", encoding="utf-8")
    (data_dir / "user_4.json.corrupt.20260901T000000").write_text(
        "x", encoding="utf-8"
    )
    (data_dir / "user_5.json.tmp").write_text("x", encoding="utf-8")
    assert storage.count_users() == 3


def test_create_user_file_creates_empty_structure(data_dir):
    result = storage.create_user_file("user_A")
    assert result is None
    path = data_dir / "user_A.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["habits"] == []
    assert "created_at" in data["metadata"]


def test_create_user_file_sets_iso_utc_created_at(data_dir):
    storage.create_user_file("user_A")
    data = json.loads((data_dir / "user_A.json").read_text(encoding="utf-8"))
    created_at = data["metadata"]["created_at"]
    assert created_at.endswith("Z")
    parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0