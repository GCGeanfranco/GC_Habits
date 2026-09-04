import threading
import time

import pytest

from app.storage.lock import RegistrationLock


def test_lock_serializes_threads():
    lock = RegistrationLock()
    state = {"active": 0, "max_active": 0}

    def worker():
        with lock:
            state["active"] += 1
            state["max_active"] = max(state["max_active"], state["active"])
            time.sleep(0.05)
            state["active"] -= 1

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert state["max_active"] == 1


def test_atomic_check_then_create_under_lock():
    users = set()
    calls = []

    def mock_exists(uid):
        return uid in users

    def mock_create(uid):
        users.add(uid)
        calls.append(f"create:{uid}")

    def mock_count():
        return len(users)

    def register(uid):
        with RegistrationLock():
            if mock_exists(uid):
                calls.append(f"login:{uid}")
            elif mock_count() < 5:
                mock_create(uid)
            else:
                calls.append(f"limit:{uid}")

    register("u1")
    register("u2")
    register("u1")

    assert calls == ["create:u1", "create:u2", "login:u1"]
    assert len(users) == 2


def test_lock_released_after_exception():
    lock = RegistrationLock()
    with pytest.raises(RuntimeError):
        with lock:
            raise RuntimeError("boom")
    with lock:
        pass