import pytest

from app.habits.management import new_habit


def make_existing_list(count):
    return [
        {
            "id": f"id{i:04d}",
            "name": f"Hábito {i}",
            "normalized_name": f"habito_{i}",
        }
        for i in range(count)
    ]


def test_ten_existing_habits_blocks_creation():
    with pytest.raises(ValueError, match="Límite de 10 hábitos alcanzado"):
        new_habit(make_existing_list(10), "Nuevo hábito")


def test_nine_existing_habits_allows_creation():
    habit = new_habit(make_existing_list(9), "Nuevo hábito")
    assert habit["name"] == "Nuevo hábito"
    assert habit["normalized_name"] == "nuevo_habito"


def test_limit_check_takes_precedence_over_invalid_name():
    with pytest.raises(ValueError, match="Límite de 10 hábitos alcanzado"):
        new_habit(make_existing_list(10), "   ")