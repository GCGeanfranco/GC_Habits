import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_login_limited_to_5_per_15_minutes(client):
    for _ in range(5):
        assert client.get("/login").status_code == 200
    assert client.get("/login").status_code == 429


def test_callback_has_independent_counter(client):
    for _ in range(5):
        assert client.get("/auth/callback").status_code == 302
    assert client.get("/auth/callback").status_code == 429


def test_login_and_callback_counters_are_independent(client):
    for _ in range(5):
        client.get("/login")
    assert client.get("/login").status_code == 429
    assert client.get("/auth/callback").status_code == 302