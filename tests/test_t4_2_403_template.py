import pytest

from app import create_app
from app import storage

CLAIMS = {"sub": "t4_2_new_user"}


class FakeProvider:
    def __init__(self, claims):
        self.claims = claims

    def validate_state(self, state):
        return True

    def verify_token(self, code):
        return self.claims


def _make_client(data_dir, monkeypatch):
    app = create_app(auth_provider=FakeProvider(claims=CLAIMS))
    monkeypatch.setattr(storage, "USER_DATA_DIR", data_dir)
    return app.test_client()


def test_403_limit_page_inherits_base_and_keeps_content(monkeypatch, tmp_path):
    data_dir = tmp_path / "users"
    data_dir.mkdir()
    for i in range(1, 6):
        (data_dir / f"user_{i}.json").write_text('{"habits": []}', encoding="utf-8")

    client = _make_client(data_dir, monkeypatch)
    resp = client.get("/auth/callback?code=code-123&state=ok")

    assert resp.status_code == 403
    html = resp.get_data(as_text=True)

    assert '<link rel="stylesheet" href="/static/css/style.css">' in html
    assert 'src="/static/img/logo_gc_habits_transparent.png"' in html

    assert "Límite de usuarios alcanzado." in html
    assert 'href="/login"' in html
    assert "Volver al inicio de sesión" in html

    assert not (data_dir / "t4_2_new_user.json").exists()