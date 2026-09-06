from datetime import date

from app.habits.streak import catch_up, for_display


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


def test_for_display_matches_catch_up_no_gap():
    habit = make_habit()
    today = date(2026, 9, 22)
    assert for_display(habit, today) == catch_up(habit, today)


def test_for_display_matches_catch_up_gap_salvado():
    habit = make_habit(
        lifelines_available=1,
        lifelines_unlocked=True,
        lifelines_unlock_date="2026-08-01",
        last_processed_date="2026-09-20",
    )
    today = date(2026, 9, 22)
    assert for_display(habit, today) == catch_up(habit, today)


def test_for_display_matches_catch_up_gap_reset():
    habit = make_habit(current_streak=8, last_processed_date="2026-09-18")
    today = date(2026, 9, 22)
    assert for_display(habit, today) == catch_up(habit, today)


def test_for_display_returns_copy_not_original():
    habit = make_habit()
    today = date(2026, 9, 22)
    assert for_display(habit, today) is not habit


def test_for_display_does_not_mutate_original():
    habit = make_habit(current_streak=8, last_processed_date="2026-09-18")
    snapshot = dict(habit)
    for_display(habit, date(2026, 9, 22))
    assert habit == snapshot