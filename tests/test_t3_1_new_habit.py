import pytest

from app.habits.management import new_habit
from app.habits.validation import normalize_name


def make_existing(name="Estudiar Python", normalized_name=None):
    return {
        "id": "existing01",
        "name": name,
        "normalized_name": normalized_name or normalize_name(name),
    }


def test_valid_creation_returns_default_habit():
    habit = new_habit([], "  Estudiar Python  ")
    assert habit["name"] == "Estudiar Python"
    assert habit["normalized_name"] == "estudiar_python"
    assert habit["current_streak"] == 0
    assert habit["record_streak"] == 0
    assert habit["lifelines_available"] == 0
    assert habit["lifelines_unlocked"] is False
    assert habit["lifelines_unlock_date"] is None
    assert habit["lifelines_last_recovery_date"] is None
    assert habit["last_processed_date"] is None
    assert habit["last_day_status"] == "none"
    assert len(habit["id"]) == 8
    assert habit["id"].isalnum()


def test_two_calls_generate_different_ids():
    first = new_habit([], "Leer")
    second = new_habit([], "Leer")
    assert first["id"] != second["id"]


def test_rejects_exact_duplicate_name():
    existing = make_existing("Estudiar Python")
    with pytest.raises(ValueError, match="Ya existe un hábito"):
        new_habit([existing], "Estudiar Python")


def test_rejects_duplicate_after_normalization():
    existing = make_existing("Estudiar Python")
    with pytest.raises(ValueError, match="Ya existe un hábito"):
        new_habit([existing], "ESTUDIAR   PYTHON")


def test_invalid_name_propagates_validation_error():
    with pytest.raises(ValueError, match="vacío"):
        new_habit([], "   ")


def test_empty_existing_habits_works():
    habit = new_habit([], "Correr")
    assert habit["name"] == "Correr"
    assert habit["normalized_name"] == "correr"