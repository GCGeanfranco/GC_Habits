from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)

from app import limiter, storage
from app.auth.session import login_required, login_user, logout_user
from app.storage.lock import RegistrationLock

bp = Blueprint("auth", __name__)

ERROR_MESSAGES = {
    "auth_failed": "No se pudo iniciar sesión. Inténtalo de nuevo.",
}


@bp.route("/login")
@limiter.limit("5 per 15 minutes")
def login():
    login_url = current_app.auth_provider.get_login_url()
    error_message = ERROR_MESSAGES.get(request.args.get("error"))
    return render_template(
        "login.html", login_url=login_url, error_message=error_message
    )


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/auth/callback")
@limiter.limit("5 per 15 minutes")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    provider = current_app.auth_provider

    if not provider.validate_state(state):
        return redirect(url_for("auth.login", error="auth_failed"))

    try:
        claims = provider.verify_token(code)
    except (KeyError, OSError, ValueError):
        return redirect(url_for("auth.login", error="auth_failed"))

    user_id = claims["sub"]

    # Nota: login_user() se ejecuta dentro del lock por simplicidad, aunque
    # no compite por el recurso que el lock protege (conteo/creación de
    # archivos). Aceptable con el tráfico esperado (máx. 5 usuarios, 1
    # worker). Si el proyecto escala, extraer login_user() fuera del bloque.
    with RegistrationLock():
        if storage.user_exists(user_id):
            login_user(user_id)
        elif storage.count_users() < 5:
            storage.create_user_file(user_id)
            login_user(user_id)
        else:
            return render_template("403_limit.html"), 403

    return redirect(url_for("web.dashboard"))