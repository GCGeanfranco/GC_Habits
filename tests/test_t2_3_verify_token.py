import time
import urllib.error

import pytest

from app.auth.google import GoogleProvider


@pytest.fixture()
def provider():
    return GoogleProvider("client-id-123", "client-secret", "http://localhost/callback")


def _valid_claims(**overrides):
    claims = {
        "sub": "google-sub-123",
        "email": "user@example.com",
        "iss": "https://accounts.google.com",
        "aud": "client-id-123",
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return claims


def _mock_exchange(monkeypatch, provider, token_response=None, error=None):
    def fake_exchange(code):
        if error is not None:
            raise error
        return token_response

    monkeypatch.setattr(provider, "_exchange_code", fake_exchange)


def _mock_verify(monkeypatch, claims=None, error=None):
    import google.oauth2.id_token

    def fake_verify(token, request, audience, clock_skew_in_seconds=0):
        if error is not None:
            raise error
        return claims

    monkeypatch.setattr(google.oauth2.id_token, "verify_oauth2_token", fake_verify)


def test_verify_token_returns_claims_for_valid_token(monkeypatch, provider):
    claims = _valid_claims()
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, claims=claims)

    result = provider.verify_token("auth-code")

    assert result == claims


def test_verify_token_rejects_wrong_audience(monkeypatch, provider):
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, error=ValueError("Token has wrong audience"))

    with pytest.raises(ValueError):
        provider.verify_token("auth-code")


def test_verify_token_rejects_disallowed_issuer(monkeypatch, provider):
    claims = _valid_claims(iss="evil.example.com")
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, claims=claims)

    with pytest.raises(ValueError, match="iss"):
        provider.verify_token("auth-code")


def test_verify_token_rejects_missing_issuer(monkeypatch, provider):
    claims = _valid_claims()
    del claims["iss"]
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, claims=claims)

    with pytest.raises(ValueError, match="iss"):
        provider.verify_token("auth-code")


def test_verify_token_rejects_expired_token(monkeypatch, provider):
    claims = _valid_claims(exp=int(time.time()) - 60)
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, claims=claims)

    with pytest.raises(ValueError, match="expirado"):
        provider.verify_token("auth-code")


def test_verify_token_rejects_missing_exp(monkeypatch, provider):
    claims = _valid_claims()
    del claims["exp"]
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})
    _mock_verify(monkeypatch, claims=claims)

    with pytest.raises(ValueError, match="expirado"):
        provider.verify_token("auth-code")


def test_verify_token_passes_clock_skew_to_verify(monkeypatch, provider):
    import google.oauth2.id_token

    calls = {}

    def fake_verify(token, request, audience, clock_skew_in_seconds=0):
        calls["clock_skew_in_seconds"] = clock_skew_in_seconds
        return _valid_claims()

    monkeypatch.setattr(google.oauth2.id_token, "verify_oauth2_token", fake_verify)
    _mock_exchange(monkeypatch, provider, token_response={"id_token": "fake-token"})

    provider.verify_token("auth-code")

    assert calls["clock_skew_in_seconds"] == 30


def test_verify_token_propagates_network_error(monkeypatch, provider):
    _mock_exchange(
        monkeypatch,
        provider,
        error=urllib.error.URLError("no network"),
    )

    with pytest.raises(urllib.error.URLError):
        provider.verify_token("auth-code")