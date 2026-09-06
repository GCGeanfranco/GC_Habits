from datetime import date

from app.habits.streak import _maybe_recover_lifeline, catch_up


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 10,
        "record_streak": 10,
        "lifelines_available": 1,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-06-01",
        "lifelines_last_recovery_date": "2026-07-01",
        "last_processed_date": "2026-09-20",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_recovers_at_exactly_30_days():
    h = {
        "lifelines_available": 1,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-01",
        "lifelines_last_recovery_date": None,
    }
    _maybe_recover_lifeline(h, date(2026, 8, 31))
    assert h["lifelines_available"] == 2
    assert h["lifelines_last_recovery_date"] == "2026-08-31"


def test_no_recovery_at_29_days():
    h = {
        "lifelines_available": 1,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-01",
        "lifelines_last_recovery_date": None,
    }
    _maybe_recover_lifeline(h, date(2026, 8, 30))
    assert h["lifelines_available"] == 1
    assert h["lifelines_last_recovery_date"] is None


def test_no_recovery_when_already_at_max():
    h = {
        "lifelines_available": 2,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-06-01",
        "lifelines_last_recovery_date": "2026-06-01",
    }
    _maybe_recover_lifeline(h, date(2026, 9, 1))
    assert h["lifelines_available"] == 2
    assert h["lifelines_last_recovery_date"] == "2026-06-01"


def test_no_recovery_when_not_unlocked():
    h = {
        "lifelines_available": 1,
        "lifelines_unlocked": False,
        "lifelines_unlock_date": "2026-08-01",
        "lifelines_last_recovery_date": None,
    }
    _maybe_recover_lifeline(h, date(2026, 9, 1))
    assert h["lifelines_available"] == 1
    assert h["lifelines_last_recovery_date"] is None


def test_catch_up_recovers_lifeline_on_salvado_day():
    habit = make_habit(lifelines_available=1, lifelines_last_recovery_date="2026-07-01")
    result = catch_up(habit, today=date(2026, 9, 22))
    assert result["last_day_status"] == "salvado"
    assert result["current_streak"] == 10
    assert result["lifelines_available"] == 1
    assert result["lifelines_last_recovery_date"] == "2026-09-21"
    assert result["last_processed_date"] == "2026-09-21"