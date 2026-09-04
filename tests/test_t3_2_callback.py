import pytest
from flask import session

from app import create_app
from app import storage


class FakeProvider:
    def __init__(self, claims=None, error=None, state_valid=True):
        self.claims = claims
        self.error = error
        self.state_valid = state_valid
        self.verify_calls = 0

    def validate_state(self, state):
        return self.state_valid

    def verify_token(self, code):
        self.verify_calls += 1
        if self.error is not None:
            raise self.error
        return self.claims


CLAIMS = {"sub": "user_123", "email": "a@example.com"}


def _make_app(provider):
    return create_app(auth_provider=provider)


def _make_client(app, data_dir, monkeypatch):
    monkeypatch.setattr(storage, "USER_DATA_DIR", data_dir)
    return app.test_client()


def test_callback_rejects_invalid_state(monkeypatch, tmp_path):
    provider = FakeProvider(claims=CLAIMS, state_valid=False)
    app = _make_app(provider)
    client = _make_client(app, tmp_path / "users", monkeypatch)

    resp = client.get("/auth/callback?code=code-123&state=wrong")

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert "auth_failed" in resp.headers["Location"]
    assert provider.verify_calls == 0


def test_callback_logs_in_existing_user(monkeypatch, tmp_path):
    data_dir = tmp_path / "users"
    data_dir.mkdir()
    (data_dir / "user_123.json").write_text('{"habits": []}', encoding="utf-8")
    app = _make_app(FakeProvider(claims=CLAIMS))
    client = _make_client(app, data_dir, monkeypatch)

    resp = client.get("/auth/callback?code=code-123&state=ok")

    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["user_id"] == "user_123"
    assert len(list(data_dir.glob("*.json"))) == 1


def test_callback_registers_new_user_when_slots_available(monkeypatch, tmp_path):
    data_dir = tmp_path / "users"
    data_dir.mkdir()
    app = _make_app(FakeProvider(claims=CLAIMS))
    client = _make_client(app, data_dir, monkeypatch)

    resp = client.get("/auth/callback?code=code-123&state=ok")

    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["user_id"] == "user_123"
    created = data_dir / "user_123.json"
    assert created.exists()
    assert "habits" in created.read_text(encoding="utf-8")


def test_callback_rejects_new_user_when_limit_reached(monkeypatch, tmp_path):
    data_dir = tmp_path / "users"
    data_dir.mkdir()
    for i in range(1, 6):
        (data_dir / f"user_{i}.json").write_text('{"habits": []}', encoding="utf-8")
    app = _make_app(FakeProvider(claims=CLAIMS))
    client = _make_client(app, data_dir, monkeypatch)

    resp = client.get("/auth/callback?code=code-123&state=ok")

    assert resp.status_code == 403
    body = resp.get_data(as_text=True)
    assert "Límite de usuarios alcanzado." in body
    assert "/login" in body
    with client.session_transaction() as sess:
        assert "user_id" not in sess
    assert not (data_dir / "user_123.json").exists()


def test_callback_rejects_invalid_token(monkeypatch, tmp_path):
    app = _make_app(FakeProvider(claims=CLAIMS, error=ValueError("bad token")))
    client = _make_client(app, tmp_path / "users", monkeypatch)

    resp = client.get("/auth/callback?code=code-123&state=ok")

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert "auth_failed" in resp.headers["Location"]