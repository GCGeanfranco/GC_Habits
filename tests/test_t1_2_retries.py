import json
import os

import pytest

from app.storage import fileops


def test_atomic_write_retries_three_times_then_raises(monkeypatch, tmp_path):
    calls = {"n": 0}

    def failing_replace(src, dst):
        calls["n"] += 1
        raise OSError("simulated disk error")

    monkeypatch.setattr(fileops.os, "replace", failing_replace)
    monkeypatch.setattr(fileops, "sleep", lambda _: None)

    with pytest.raises(RuntimeError):
        fileops._atomic_write(tmp_path / "user.json", {"a": 1})

    assert calls["n"] == 3


def test_atomic_write_succeeds_on_second_attempt(monkeypatch, tmp_path):
    original_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("transient error")
        original_replace(src, dst)

    monkeypatch.setattr(fileops.os, "replace", flaky_replace)
    monkeypatch.setattr(fileops, "sleep", lambda _: None)

    path = tmp_path / "user.json"
    fileops._atomic_write(path, {"a": 1})

    assert calls["n"] == 2
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}


def test_atomic_write_calls_replace_once_on_success(monkeypatch, tmp_path):
    original_replace = os.replace
    calls = {"n": 0}

    def counting_replace(src, dst):
        calls["n"] += 1
        original_replace(src, dst)

    monkeypatch.setattr(fileops.os, "replace", counting_replace)

    fileops._atomic_write(tmp_path / "user.json", {"a": 1})
    assert calls["n"] == 1


def test_atomic_write_backs_off_between_attempts(monkeypatch, tmp_path):
    sleeps = []

    def failing_replace(src, dst):
        raise OSError("simulated disk error")

    monkeypatch.setattr(fileops.os, "replace", failing_replace)
    monkeypatch.setattr(fileops, "sleep", sleeps.append)

    with pytest.raises(RuntimeError):
        fileops._atomic_write(tmp_path / "user.json", {"a": 1})

    assert sleeps == [0.1, 0.2]