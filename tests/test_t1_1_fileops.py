import json
import logging

from app.storage import fileops


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_read_returns_empty_structure_when_file_missing(tmp_path):
    data = fileops._read_with_corrupt_handling(tmp_path / "missing.json")
    assert data == {"habits": [], "metadata": {}}


def test_read_returns_content_when_file_valid(tmp_path):
    path = tmp_path / "user.json"
    expected = {"habits": [1], "metadata": {"x": 1}}
    path.write_text(json.dumps(expected), encoding="utf-8")
    data = fileops._read_with_corrupt_handling(path)
    assert data == expected


def test_read_backs_up_corrupt_file_and_returns_empty(tmp_path, caplog):
    path = tmp_path / "user.json"
    corrupt_content = "{not valid json"
    path.write_text(corrupt_content, encoding="utf-8")
    with caplog.at_level(logging.ERROR):
        data = fileops._read_with_corrupt_handling(path)
    assert data == {"habits": [], "metadata": {}}
    assert not path.exists()
    backups = list(tmp_path.glob("user.json.corrupt.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == corrupt_content
    assert "corrupto" in caplog.text.lower()


def test_atomic_write_creates_file_without_tmp_residual(tmp_path):
    path = tmp_path / "user.json"
    fileops._atomic_write(path, {"habits": [], "metadata": {}})
    assert _read_json(path) == {"habits": [], "metadata": {}}
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_write_overwrites_existing_file(tmp_path):
    path = tmp_path / "user.json"
    fileops._atomic_write(path, {"a": 1})
    fileops._atomic_write(path, {"a": 2, "b": 3})
    assert _read_json(path) == {"a": 2, "b": 3}


def test_backup_corrupt_renames_with_timestamp(tmp_path):
    path = tmp_path / "user.json"
    path.write_text("data", encoding="utf-8")
    fileops._backup_corrupt(path)
    assert not path.exists()
    backups = list(tmp_path.glob("user.json.corrupt.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "data"