import time
from datetime import timedelta
from functools import wraps

from flask import redirect, session, url_for

SESSION_INACTIVITY_TIMEOUT = timedelta(days=15)


def login_user(user_id: str) -> None:
    session.permanent = True
    session["user_id"] = user_id


def logout_user() -> None:
    session.clear()


def current_user_id():
    return session.get("user_id")


def refresh_session_activity() -> None:
    if session.get("user_id") is None:
        return
    last_activity = session.get("last_activity")
    now = time.time()
    if last_activity is None:
        session["last_activity"] = now
        return
    if now - last_activity > SESSION_INACTIVITY_TIMEOUT.total_seconds():
        logout_user()
        return
    session["last_activity"] = now


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user_id() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped