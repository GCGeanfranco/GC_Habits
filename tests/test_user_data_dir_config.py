import importlib
from pathlib import Path

import app.storage as storage_module


def _reload_storage():
    return importlib.reload(storage_module)


def test_user_data_dir_reads_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("USER_DATA_DIR", str(tmp_path))
    module = _reload_storage()
    try:
        assert module.USER_DATA_DIR == tmp_path
    finally:
        monkeypatch.delenv("USER_DATA_DIR", raising=False)
        _reload_storage()


def test_user_data_dir_defaults_to_data_users(monkeypatch):
    monkeypatch.delenv("USER_DATA_DIR", raising=False)
    module = _reload_storage()
    assert module.USER_DATA_DIR == Path("/data/users")