import pytest

from app import create_app


def test_create_app_requires_flask_secret_key(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Falta FLASK_SECRET_KEY en el entorno"):
        create_app()


def test_default_provider_requires_google_client_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    with pytest.raises(RuntimeError, match="Falta GOOGLE_CLIENT_ID en el entorno"):
        create_app()


def test_default_provider_requires_google_client_secret(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="Falta GOOGLE_CLIENT_SECRET en el entorno"):
        create_app()


def test_default_provider_reports_all_missing_google_vars(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    with pytest.raises(RuntimeError) as excinfo:
        create_app()
    assert "GOOGLE_CLIENT_ID" in str(excinfo.value)
    assert "GOOGLE_CLIENT_SECRET" in str(excinfo.value)


def test_secret_key_configured_on_app(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "clave-test")
    app = create_app()
    assert app.config["SECRET_KEY"] == "clave-test"


def test_google_credentials_loaded_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "id-test")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret-test")
    app = create_app()
    assert app.auth_provider.client_id == "id-test"
    assert app.auth_provider.client_secret == "secret-test"


def test_google_secrets_not_required_with_injected_provider(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

    class FakeProvider:
        pass

    app = create_app(auth_provider=FakeProvider())
    assert isinstance(app.auth_provider, FakeProvider)