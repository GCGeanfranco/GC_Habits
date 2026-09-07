import re

import pytest
from flask import render_template_string

from app import create_app


@pytest.fixture()
def client():
    app = create_app()

    @app.route("/_test_base_child")
    def test_base_child():
        return render_template_string(
            '{% extends "base.html" %}{% block content %}OK{% endblock %}'
        )

    return app.test_client()


def test_child_inherits_stylesheet_link(client):
    resp = client.get("/_test_base_child")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '<link rel="stylesheet" href="/static/css/style.css">' in html


def test_child_inherits_logo(client):
    resp = client.get("/_test_base_child")
    html = resp.get_data(as_text=True)
    assert 'src="/static/img/logo_gc_habits_transparent.png"' in html


def test_child_inherits_deferred_script(client):
    resp = client.get("/_test_base_child")
    html = resp.get_data(as_text=True)
    assert '<script src="/static/js/habits.js" defer></script>' in html


def test_no_inline_style_or_script(client):
    resp = client.get("/_test_base_child")
    html = resp.get_data(as_text=True)
    assert "<style" not in html
    scripts = re.findall(r"<script[^>]*>", html)
    assert scripts == ['<script src="/static/js/habits.js" defer>']