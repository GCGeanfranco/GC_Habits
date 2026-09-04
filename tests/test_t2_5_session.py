import pytest
from flask import session

from app import create_app
from app.auth.session import current_user_id, login_required, login_user, logout_user


@pytest.fixture()
def app():
    app = create_app()

    @login_required
    def protected():
        return "protected"

    app.add_url_rule("/protected", endpoint="protected", view_func=protected)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_login_user_sets_current_user_id(app):
    with app.test_request_context():
        login_user("user_1")
        assert current_user_id() == "user_1"


def test_login_user_marks_session_permanent(app):
    with app.test_request_context():
        login_user("user_1")
        assert session.permanent is True


def test_current_user_id_is_none_without_login(app):
    with app.test_request_context():
        assert current_user_id() is None


def test_logout_user_clears_session(app):
    with app.test_request_context():
        login_user("user_1")
        logout_user()
        assert current_user_id() is None


def test_login_required_redirects_anonymous_to_login(client):
    resp = client.get("/protected")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_required_allows_authenticated(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_1"
    resp = client.get("/protected")
    assert resp.status_code == 200
    assert resp.data == b"protected"