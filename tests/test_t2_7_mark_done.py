from datetime import date

from app.habits.streak import mark_done


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 5,
        "record_streak": 12,
        "lifelines_available": 0,
        "lifelines_unlocked": False,
        "lifelines_unlock_date": None,
        "lifelines_last_recovery_date": None,
        "last_processed_date": "2026-09-21",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_first_mark_sets_streak_to_1():
    habit = make_habit(
        current_streak=0, record_streak=0, last_processed_date=None, last_day_status="none"
    )
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 1
    assert result["last_day_status"] == "hecho"
    assert result["last_processed_date"] == "2026-09-22"


def test_continues_after_done_day():
    habit = make_habit()
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 6
    assert result["last_day_status"] == "hecho"
    assert result["last_processed_date"] == "2026-09-22"


def test_continues_after_salvado_day():
    habit = make_habit(current_streak=10, last_day_status="salvado")
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 11
    assert result["last_day_status"] == "hecho"
    assert result["last_processed_date"] == "2026-09-22"


def test_already_marked_today_returns_true_and_unchanged():
    habit = make_habit(last_processed_date="2026-09-22")
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is True
    assert result == habit


def test_restarts_to_1_after_internal_catch_up_failure():
    habit = make_habit(current_streak=8, last_processed_date="2026-09-18")
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 1
    assert result["last_day_status"] == "hecho"
    assert result["last_processed_date"] == "2026-09-22"


def test_mark_done_does_not_mutate_original_dict():
    habit = make_habit(current_streak=8, last_processed_date="2026-09-18")
    snapshot = dict(habit)
    mark_done(habit, date(2026, 9, 22))
    assert habit == snapshot