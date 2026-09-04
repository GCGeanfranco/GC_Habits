import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=None,
)


def create_app(auth_provider=None):
    load_dotenv()
    app = Flask(__name__)

    flask_env = os.environ.get("FLASK_ENV", "development")
    is_production = flask_env == "production"

    secret_key = os.environ.get("FLASK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "Falta FLASK_SECRET_KEY en el entorno. Defínela en .env o como variable de entorno."
        )
    app.config["SECRET_KEY"] = secret_key
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=15)

    from app.auth.session import refresh_session_activity

    app.before_request(refresh_session_activity)

    if auth_provider is None:
        from app.auth.google import GoogleProvider

        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "")
        missing = [
            name
            for name, value in (
                ("GOOGLE_CLIENT_ID", client_id),
                ("GOOGLE_CLIENT_SECRET", client_secret),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Falta {', '.join(missing)} en el entorno. "
                "Defínelas en .env o como variables de entorno."
            )
        auth_provider = GoogleProvider(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    app.auth_provider = auth_provider

    from app.auth.routes import bp as auth_bp
    from app.web.routes import bp as web_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)

    CSRFProtect(app)

    limiter.init_app(app)

    Talisman(
        app,
        content_security_policy={"default-src": "'self'", "script-src": "'self'"},
        force_https=is_production,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
        session_cookie_secure=is_production,
    )

    return app
