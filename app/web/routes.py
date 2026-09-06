from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app import storage
from app.auth.session import login_required
from app.habits.management import new_habit
from app.habits.streak import for_display, mark_done

bp = Blueprint("web", __name__, template_folder="templates")


def _today_utc():
    return datetime.now(timezone.utc).date()


@bp.route("/dashboard")
@login_required
def dashboard():
    data, recovered = storage.load_with_status()
    today = _today_utc()
    habits_display = [for_display(h, today) for h in data["habits"]]
    return render_template(
        "dashboard.html",
        data=data,
        recovered=recovered,
        habits=habits_display,
    )


@bp.route("/habits", methods=["POST"])
@login_required
def create_habit():
    data = storage.load()
    raw_name = request.form.get("name", "")
    try:
        habit = new_habit(data["habits"], raw_name)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("web.dashboard"))
    data["habits"].append(habit)
    storage.save(data)
    flash(f"Hábito '{habit['name']}' creado.", "success")
    return redirect(url_for("web.dashboard"))


@bp.route("/habits/<habit_id>/done", methods=["POST"])
@login_required
def mark_habit_done(habit_id):
    data = storage.load()
    idx = next(
        (i for i, h in enumerate(data["habits"]) if h["id"] == habit_id),
        None,
    )
    if idx is None:
        abort(404)
    habit = data["habits"][idx]
    updated, already_done = mark_done(habit, _today_utc())
    data["habits"][idx] = updated
    storage.save(data)
    if already_done:
        flash(f"'{updated['name']}' ya estaba marcado como hecho hoy.", "info")
    else:
        flash(
            f"'{updated['name']}' marcado como hecho. Racha: {updated['current_streak']} días.",
            "success",
        )
    return redirect(url_for("web.dashboard"))