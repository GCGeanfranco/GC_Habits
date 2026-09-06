from datetime import date

from app.habits.streak import catch_up


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 5,
        "record_streak": 12,
        "lifelines_available": 1,
        "lifelines_unlocked": True,
        "lifelines_unlock_date": "2026-08-20",
        "lifelines_last_recovery_date": "2026-09-19",
        "last_processed_date": "2026-09-20",
        "last_day_status": "hecho",
        "created_at": "2026-09-01T10:00:00Z",
    }
    habit.update(overrides)
    return habit


def test_catch_up_returns_copy_and_does_not_mutate_original():
    habit = make_habit()
    snapshot = dict(habit)
    result = catch_up(habit, date(2026, 9, 21))
    assert habit == snapshot
    assert result is not habit


def test_catch_up_with_no_history_returns_unchanged_copy():
    habit = make_habit(last_processed_date=None, last_day_status="none")
    result = catch_up(habit, date(2026, 9, 21))
    assert result == habit


def test_catch_up_with_yesterday_processed_returns_unchanged_copy():
    habit = make_habit(last_processed_date="2026-09-20")
    result = catch_up(habit, today=date(2026, 9, 21))
    assert result == habit


def test_catch_up_with_today_processed_returns_unchanged_copy():
    habit = make_habit(last_processed_date="2026-09-21")
    result = catch_up(habit, today=date(2026, 9, 21))
    assert result == habit