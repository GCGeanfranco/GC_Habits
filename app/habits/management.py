import uuid

from app.habits.validation import normalize_name, validate_name


def new_habit(existing_habits: list[dict], raw_name: str) -> dict:
    if len(existing_habits) >= 10:
        raise ValueError("Límite de 10 hábitos alcanzado")
    validate_name(raw_name)
    normalized = normalize_name(raw_name)
    if any(h["normalized_name"] == normalized for h in existing_habits):
        raise ValueError(f"Ya existe un hábito con el nombre '{raw_name}'")
    return {
        "id": uuid.uuid4().hex[:8],
        "name": raw_name.strip(),
        "normalized_name": normalized,
        "current_streak": 0,
        "record_streak": 0,
        "lifelines_available": 0,
        "lifelines_unlocked": False,
        "lifelines_unlock_date": None,
        "lifelines_last_recovery_date": None,
        "last_processed_date": None,
        "last_day_status": "none",
    }