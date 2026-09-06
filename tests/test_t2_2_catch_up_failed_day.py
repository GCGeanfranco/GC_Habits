from datetime import date

from app.habits.streak import catch_up


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 5,
        "record_streak": 12,
        "lifelines_available": 0,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-20",
        "lifelines_last_recovery_date": "2026-09-19",
        "last_processed_date": "2026-09-20",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_one_failed_day_without_lifelines_resets_streak():
    habit = make_habit(lifelines_available=0, last_processed_date="2026-09-20")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 0
    assert result["last_day_status"] == "fallido"
    assert result["last_processed_date"] == "2026-09-21"
    assert result["record_streak"] == 12


def test_three_failed_days_without_lifelines_reset_streak():
    habit = make_habit(lifelines_available=0, last_processed_date="2026-09-18")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 0
    assert result["last_day_status"] == "fallido"
    assert result["last_processed_date"] == "2026-09-21"


def test_catch_up_does_not_mutate_original_dict():
    habit = make_habit(lifelines_available=0, last_processed_date="2026-09-18")
    snapshot = dict(habit)
    catch_up(habit, today=date(2026, 9, 22))
    assert habit == snapshot