import pytest
from flask import Flask

from app import create_app


class FakeProvider:
    pass


def test_app_creates():
    app = create_app()
    assert isinstance(app, Flask)
    assert app.auth_provider is not None


def test_default_provider_is_google():
    from app.auth.google import GoogleProvider

    app = create_app()
    assert isinstance(app.auth_provider, GoogleProvider)


def test_injected_provider_is_used():
    mock = FakeProvider()
    app = create_app(auth_provider=mock)
    assert app.auth_provider is mock


def test_blueprints_registered():
    app = create_app(auth_provider=FakeProvider())
    assert "auth" in app.blueprints
    assert "web" in app.blueprints
