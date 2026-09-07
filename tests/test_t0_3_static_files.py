import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_style_css_served(client):
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type").startswith("text/css")
    assert len(resp.data) > 0


def test_habits_js_served(client):
    resp = client.get("/static/js/habits.js")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type").startswith("text/javascript")
    assert len(resp.data) > 0