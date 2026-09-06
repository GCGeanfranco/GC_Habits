import os
from datetime import datetime, timezone
from pathlib import Path

from flask import session

from .fileops import _atomic_write, _read_with_corrupt_flag, _read_with_corrupt_handling

USER_DATA_DIR = Path(os.environ.get("USER_DATA_DIR", "/data/users"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_user_id() -> str:
    user_id = session.get("user_id")
    if not user_id:
        raise RuntimeError("No hay usuario en sesión")
    return user_id


def _user_path(user_id: str) -> Path:
    return USER_DATA_DIR / f"{user_id}.json"


def load() -> dict:
    return _read_with_corrupt_handling(_user_path(_get_user_id()))


def load_with_status():
    return _read_with_corrupt_flag(_user_path(_get_user_id()))


def save(data: dict) -> None:
    _atomic_write(_user_path(_get_user_id()), data)


def user_exists(user_id: str) -> bool:
    return _user_path(user_id).exists()


def count_users() -> int:
    return len(list(USER_DATA_DIR.glob("*.json")))


def create_user_file(user_id: str) -> None:
    _atomic_write(
        _user_path(user_id), {"habits": [], "metadata": {"created_at": _now_iso()}}
    )