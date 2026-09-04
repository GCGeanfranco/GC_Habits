import pytest

from app.auth.google import GoogleProvider
from app.auth.provider import AuthProvider


def test_auth_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        AuthProvider()


def test_google_provider_is_subclass_of_auth_provider():
    assert issubclass(GoogleProvider, AuthProvider)


def test_google_provider_is_instance_of_auth_provider():
    provider = GoogleProvider("id", "secret", "http://localhost/callback")
    assert isinstance(provider, AuthProvider)


def test_google_provider_has_no_abstract_methods():
    assert not GoogleProvider.__abstractmethods__


def test_google_provider_exposes_interface_methods():
    provider = GoogleProvider("id", "secret", "http://localhost/callback")
    for name in ("get_login_url", "verify_token", "get_user_info", "validate_state"):
        assert callable(getattr(provider, name))