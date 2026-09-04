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


def test_validate_state_returns_true_when_matches(app, provider):
    with app.test_request_context():
        session["oauth_state"] = "state-abc"
        assert provider.validate_state("state-abc") is True


def test_validate_state_returns_false_when_mismatch(app, provider):
    with app.test_request_context():
        session["oauth_state"] = "state-abc"
        assert provider.validate_state("state-evil") is False


def test_validate_state_returns_false_when_no_state_in_session(app, provider):
    with app.test_request_context():
        assert provider.validate_state("state-abc") is False


def test_validate_state_returns_false_when_state_is_none(app, provider):
    with app.test_request_context():
        session["oauth_state"] = "state-abc"
        assert provider.validate_state(None) is False


@pytest.mark.parametrize("incoming", ["state-abc", "state-evil"])
def test_validate_state_consumes_oauth_state_from_session(app, provider, incoming):
    with app.test_request_context():
        session["oauth_state"] = "state-abc"
        provider.validate_state(incoming)
        assert "oauth_state" not in session