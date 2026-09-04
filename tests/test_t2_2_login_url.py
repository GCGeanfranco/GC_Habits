from urllib.parse import parse_qs, urlparse

import pytest
from flask import session

from app import create_app
from app.auth.google import GoogleProvider


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def provider():
    return GoogleProvider("client-id-123", "client-secret", "http://localhost/callback")


def _query(url):
    return parse_qs(urlparse(url).query)


def test_get_login_url_includes_state(app, provider):
    with app.test_request_context():
        url = provider.get_login_url()
    params = _query(url)
    assert "state" in params
    assert len(params["state"][0]) > 0


def test_get_login_url_stores_state_in_session_before_url(app, provider):
    with app.test_request_context():
        url = provider.get_login_url()
        state_in_url = _query(url)["state"][0]
        assert session["oauth_state"] == state_in_url


def test_get_login_url_generates_distinct_states(app, provider):
    with app.test_request_context():
        url1 = provider.get_login_url()
        url2 = provider.get_login_url()
    state1 = _query(url1)["state"][0]
    state2 = _query(url2)["state"][0]
    assert state1 != state2


def test_get_login_url_contains_client_and_redirect(app, provider):
    with app.test_request_context():
        url = provider.get_login_url()
    params = _query(url)
    assert params["client_id"] == ["client-id-123"]
    assert params["redirect_uri"] == ["http://localhost/callback"]
    assert params["response_type"] == ["code"]