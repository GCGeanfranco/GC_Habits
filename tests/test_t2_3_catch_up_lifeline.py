from datetime import date

from app.habits.streak import catch_up


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 5,
        "record_streak": 12,
        "lifelines_available": 2,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-20",
        "lifelines_last_recovery_date": "2026-09-19",
        "last_processed_date": "2026-09-20",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_one_failed_day_consumes_one_lifeline_and_keeps_streak():
    habit = make_habit(last_processed_date="2026-09-20")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 5
    assert result["lifelines_available"] == 1
    assert result["last_day_status"] == "salvado"
    assert result["last_processed_date"] == "2026-09-21"
    assert result["record_streak"] == 12


def test_two_failed_days_consume_one_lifeline_each():
    habit = make_habit(last_processed_date="2026-09-19")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 5
    assert result["lifelines_available"] == 0
    assert result["last_day_status"] == "salvado"
    assert result["last_processed_date"] == "2026-09-21"


def test_three_failed_days_exhaust_lifelines_then_reset_streak():
    habit = make_habit(last_processed_date="2026-09-18")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["lifelines_available"] == 0
    assert result["current_streak"] == 0
    assert result["last_day_status"] == "fallido"
    assert result["last_processed_date"] == "2026-09-21"


def test_catch_up_does_not_mutate_original_dict():
    habit = make_habit(last_processed_date="2026-09-18")
    snapshot = dict(habit)
    catch_up(habit, today=date(2026, 9, 22))
    assert habit == snapshot