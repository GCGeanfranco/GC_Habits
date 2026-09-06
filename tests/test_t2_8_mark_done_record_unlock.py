from datetime import date

from app.habits.streak import catch_up, mark_done


def make_habit(**overrides):
    habit = {
        "id": "a1b2c3d4",
        "name": "Estudiar Python",
        "normalized_name": "estudiar_python",
        "current_streak": 5,
        "record_streak": 6,
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


def test_record_not_updated_when_equal():
    habit = make_habit()
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 6
    assert result["record_streak"] == 6


def test_record_updated_when_surpassed():
    habit = make_habit(record_streak=5)
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 6
    assert result["record_streak"] == 6


def test_unlocks_lifelines_at_streak_15():
    habit = make_habit(current_streak=14, record_streak=14)
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 15
    assert result["record_streak"] == 15
    assert result["lifelines_unlocked"] is True
    assert result["lifelines_available"] == 2
    assert result["lifelines_unlock_date"] == "2026-09-22"
    assert result["lifelines_last_recovery_date"] is None


def test_does_not_reset_lifelines_when_already_unlocked():
    habit = make_habit(
        current_streak=20,
        record_streak=21,
        lifelines_available=1,
        lifelines_unlocked=True,
        lifelines_unlock_date="2026-08-01",
        lifelines_last_recovery_date="2026-08-20",
    )
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 21
    assert result["lifelines_available"] == 1
    assert result["lifelines_unlocked"] is True
    assert result["lifelines_unlock_date"] == "2026-08-01"
    assert result["lifelines_last_recovery_date"] == "2026-08-20"


def test_salvado_day_never_updates_record():
    habit = make_habit(
        current_streak=14,
        record_streak=14,
        lifelines_available=1,
        lifelines_unlocked=True,
        lifelines_unlock_date="2026-08-01",
        last_processed_date="2026-09-20",
    )
    caught_up = catch_up(habit, date(2026, 9, 22))
    assert caught_up["current_streak"] == 14
    assert caught_up["record_streak"] == 14
    assert caught_up["last_day_status"] == "salvado"
    result, already = mark_done(habit, date(2026, 9, 22))
    assert already is False
    assert result["current_streak"] == 15
    assert result["record_streak"] == 15