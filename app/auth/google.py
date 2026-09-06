import json
import secrets
import time
import urllib.parse
import urllib.request
from urllib.parse import urlencode

from flask import session
from google.oauth2 import id_token

from .provider import AuthProvider

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
ALLOWED_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class _UrllibResponse:
    def __init__(self, status, data):
        self.status = status
        self.data = data


class _UrllibRequest:
    def __call__(self, url, method="GET", headers=None, body=None, **kwargs):
        req = urllib.request.Request(
            url, data=body, headers=headers or {}, method=method
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return _UrllibResponse(response.status, response.read())


class GoogleProvider(AuthProvider):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_login_url(self) -> str:
        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def verify_token(self, code: str) -> dict:
        token_data = self._exchange_code(code)
        id_token_str = token_data["id_token"]
        # Tolerancia de reloj (30s) para la verificación del id_token: el
        # reloj del servidor local puede ir unos segundos atrasado respecto
        # al de Google (detectado en pruebas locales: "Token used too early").
        # 30s es un valor conservador estándar para verificación OIDC.
        claims = id_token.verify_oauth2_token(
            id_token_str, _UrllibRequest(), self.client_id,
            clock_skew_in_seconds=30,
        )
        if claims.get("iss") not in ALLOWED_ISSUERS:
            raise ValueError("Emisor del token no permitido (iss).")
        if int(claims.get("exp", 0)) <= time.time():
            raise ValueError("Token expirado.")
        return claims

    def _exchange_code(self, code: str) -> dict:
        data = urllib.parse.urlencode(
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode("utf-8")
        request = urllib.request.Request(GOOGLE_TOKEN_URL, data=data)
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_user_info(self, credentials) -> dict:
        raise NotImplementedError

    def validate_state(self, state: str) -> bool:
        expected = session.pop("oauth_state", None)
        if not state or not expected:
            return False
        return secrets.compare_digest(expected, state)