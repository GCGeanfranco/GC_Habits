import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_logo_served_from_static(client):
    resp = client.get("/static/img/logo_gc_habits_transparent.png")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type") == "image/png"
    assert len(resp.data) > 0