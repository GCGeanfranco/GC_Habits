from datetime import date

from app.habits.streak import catch_up


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 20,
        "record_streak": 20,
        "lifelines_available": 0,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-01",
        "lifelines_last_recovery_date": None,
        "last_processed_date": "2026-09-20",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_streak_reset_reblocks_lifelines():
    habit = make_habit()
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 0
    assert result["last_day_status"] == "fallido"
    assert result["lifelines_unlocked"] is False
    assert result["lifelines_unlock_date"] is None
    assert result["lifelines_last_recovery_date"] is None
    assert result["lifelines_available"] == 0


def test_streak_reset_without_unlocked_lifelines_leaves_fields_untouched():
    habit = make_habit(lifelines_unlocked=False, lifelines_unlock_date=None)
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["current_streak"] == 0
    assert result["last_day_status"] == "fallido"
    assert result["lifelines_unlocked"] is False
    assert result["lifelines_unlock_date"] is None
    assert result["lifelines_last_recovery_date"] is None


def test_saved_day_does_not_reblock_lifelines():
    habit = make_habit(lifelines_available=2, lifelines_last_recovery_date="2026-09-19")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["last_day_status"] == "salvado"
    assert result["current_streak"] == 20
    assert result["lifelines_available"] == 1
    assert result["lifelines_unlocked"] is True
    assert result["lifelines_unlock_date"] == "2026-08-01"
    assert result["lifelines_last_recovery_date"] == "2026-09-19"


def test_catch_up_does_not_mutate_original_dict():
    habit = make_habit()
    snapshot = dict(habit)
    catch_up(habit, today=date(2026, 9, 22))
    assert habit == snapshot