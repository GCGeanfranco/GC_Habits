from datetime import date, timedelta


def catch_up(habit: dict, today: date) -> dict:
    # Limitación aceptada (Spec 002, T5.2): se asume el esquema completo de
    # hábito del plan §2. Un JSON con un hábito incompleto (creado a mano o
    # parcialmente corrupto) lanzaría KeyError aquí y en for_display/mark_done
    # (500 en /dashboard). No se valida el esquema al cargar; evaluar en una
    # spec futura.
    h = dict(habit)
    if h["last_processed_date"] is None:
        return h
    cursor = date.fromisoformat(h["last_processed_date"]) + timedelta(days=1)
    while cursor < today:
        if h["lifelines_available"] == 0:
            h["current_streak"] = 0
            h["last_day_status"] = "fallido"
            if h["lifelines_unlocked"]:
                h["lifelines_unlocked"] = False
                h["lifelines_unlock_date"] = None
                h["lifelines_last_recovery_date"] = None
        else:
            h["lifelines_available"] -= 1
            h["last_day_status"] = "salvado"
        h["last_processed_date"] = cursor.isoformat()
        _maybe_recover_lifeline(h, cursor)
        cursor += timedelta(days=1)
    return h


def _maybe_recover_lifeline(h: dict, current_date: date) -> None:
    if not h["lifelines_unlocked"] or h["lifelines_available"] >= 2:
        return
    anchor = h["lifelines_last_recovery_date"] or h["lifelines_unlock_date"]
    if (current_date - date.fromisoformat(anchor)).days >= 30:
        h["lifelines_available"] = min(2, h["lifelines_available"] + 1)
        h["lifelines_last_recovery_date"] = current_date.isoformat()


def mark_done(habit: dict, today: date) -> tuple[dict, bool]:
    h = catch_up(habit, today)
    if h["last_processed_date"] == today.isoformat():
        return h, True
    continued = h["last_processed_date"] is None or h["last_day_status"] in ("hecho", "salvado")
    h["current_streak"] = h["current_streak"] + 1 if continued else 1
    h["last_day_status"] = "hecho"
    h["last_processed_date"] = today.isoformat()
    if h["current_streak"] > h["record_streak"]:
        h["record_streak"] = h["current_streak"]
    if not h["lifelines_unlocked"] and h["current_streak"] >= 15:
        h["lifelines_unlocked"] = True
        h["lifelines_available"] = 2
        h["lifelines_unlock_date"] = today.isoformat()
        h["lifelines_last_recovery_date"] = None
    return h, False


def for_display(habit: dict, today: date) -> dict:
    return catch_up(habit, today)