from flask import Blueprint, render_template

from app import storage
from app.auth.session import login_required

bp = Blueprint("web", __name__, template_folder="templates")


@bp.route("/dashboard")
@login_required
def dashboard():
    data, recovered = storage.load_with_status()
    return render_template("dashboard.html", data=data, recovered=recovered)