# Plan Técnico — Spec 002: Gestión de Hábitos

---

## 1. Estructura de Módulos

### `app/habits/` (nuevo — lógica pura, sin I/O, sin Flask — Constitución §3)
| Archivo | Responsabilidad | API Pública |
|---------|------------------|-------------|
| `validation.py` | Validación y normalización de nombres (RF-02, RF-03, Constitución §9) | `NAME_REGEX`; `NAME_MAX_CHARS = 100`; `NAME_MAX_WORDS = 8`; `normalize_name(name: str) -> str` (minúsculas, sin tildes, espacios → `_`); `validate_name(name: str) -> None` (lanza `ValueError` con el motivo si no cumple vacío/regex/longitud/palabras) |
| `streak.py` | Motor de racha y salvavidas (RF-07 a RF-14) | `catch_up(habit: dict, today: date) -> dict`; `mark_done(habit: dict, today: date) -> tuple[dict, bool]` (bool = ya estaba marcado hoy); `for_display(habit: dict, today: date) -> dict` |
| `management.py` | Alta de hábitos y reglas de colección (RF-01, RF-17) | `new_habit(existing_habits: list[dict], raw_name: str) -> dict` (valida, normaliza, comprueba duplicado y límite de 10; lanza `ValueError`; devuelve el dict del hábito nuevo con valores iniciales) |
| `__init__.py` | Reexporta la API pública del paquete | `from .validation import validate_name, normalize_name`; `from .streak import catch_up, mark_done, for_display`; `from .management import new_habit` |

**Regla (Constitución §3)**: nada en `app/habits/` importa `flask`, `app.web`, ni `app.auth`. Todas las funciones son puras: reciben `dict`/`list`/`date` y devuelven `dict`/`tuple`, nunca leen ni escriben archivos ni sesión.

**Cubre**: RF-01, RF-02, RF-03, RF-07, RF-08, RF-09, RF-10, RF-11, RF-12, RF-13, RF-14, RF-17

### `app/web/` (extensión de lo existente)
| Archivo | Responsabilidad | API Pública |
|---------|------------------|-------------|
| `routes.py` | Añade `POST /habits` y `POST /habits/<habit_id>/done`; `GET /dashboard` se extiende para listar hábitos | `bp` (mismo blueprint `web`) |
| `templates/dashboard.html` | Se extiende: formulario de alta + tabla/lista de hábitos con botón "Marcar como hecho" + mensajes flash de error | — |

**Cubre**: RF-04, RF-05, RF-06, RF-15, RF-16, RF-18

### `app/storage/`
Sin cambios de API. `load()`/`save()` ya aceptan y persisten cualquier estructura dentro de `data["habits"]` (Constitución §5: `{"habits": [...], "metadata": {...}}`). Esta spec solo cambia el contenido de `habits`, nunca el contrato de `storage`.

---

## 2. Modelo de Datos

Cada elemento de `data["habits"]` (dentro del JSON por usuario ya existente):

```json
{
  "id": "a1b2c3d4",
  "name": "Estudiar Python",
  "normalized_name": "estudiar_python",
  "current_streak": 5,
  "record_streak": 12,
  "lifelines_available": 1,
  "lifelines_unlocked": true,
  "lifelines_unlock_date": "2026-08-20",
  "lifelines_last_recovery_date": "2026-09-19",
  "last_processed_date": "2026-09-20",
  "last_day_status": "hecho",
  "created_at": "2026-09-01T10:00:00Z"
}
```

- `id`: `uuid.uuid4().hex[:8]`, generado en `management.new_habit()`. Usado en la URL `/habits/<id>/done`.
- `name`: tal como lo escribió el usuario (para mostrar).
- `normalized_name`: minúsculas + sin tildes + espacios → `_` (usado solo para detectar duplicados, RF-02).
- `current_streak`, `record_streak`: enteros, empiezan en 0.
- `lifelines_available`: 0–2.
- `lifelines_unlocked`: booleano; controla si aplica la ventana de recuperación de 30 días (RF-14).
- `lifelines_unlock_date` / `lifelines_last_recovery_date`: fechas `YYYY-MM-DD` (solo fecha, no hora — el corte es siempre por día calendario UTC); `null` si nunca se desbloquearon.
- `last_processed_date`: `YYYY-MM-DD` o `null` si el hábito nunca fue marcado. Es el ancla desde la que `catch_up()` recalcula.
- `last_day_status`: `"none" | "hecho" | "salvado" | "fallido"` — estado del último día procesado; determina si el próximo marcado continúa la racha (RF-10).
- `created_at`: ISO 8601 UTC con hora, igual que `metadata.created_at` de la Spec 001 (por consistencia, aunque no se usa en la lógica de racha).

---

## 3. Diseño del Motor de Racha y Salvavidas (`app/habits/streak.py`)

**Principio central**: la racha nunca se dispara por un cron ni un scheduler. Se recalcula de forma perezosa (*lazy*) cada vez que el hábito se toca — al listar (`GET /dashboard`) o al marcar (`POST /habits/<id>/done`) — "poniéndose al día" día por día desde `last_processed_date` hasta hoy.

```python
def catch_up(habit: dict, today: date) -> dict:
    """Procesa cronológicamente cada día ya transcurrido (estrictamente
    anterior a `today`) que aún no fue evaluado. No toca el día de hoy.
    RF-07, RF-08, RF-09, RF-13, RF-14."""
    h = dict(habit)
    if h["last_processed_date"] is None:
        return h  # sin historial, nada que poner al día
    cursor = date.fromisoformat(h["last_processed_date"]) + timedelta(days=1)
    while cursor < today:
        if h["lifelines_available"] > 0:
            h["lifelines_available"] -= 1
            h["last_day_status"] = "salvado"          # RF-08, RF-11 (no cuenta para récord)
        else:
            h["current_streak"] = 0
            h["last_day_status"] = "fallido"           # RF-09
            if h["lifelines_unlocked"]:
                h["lifelines_unlocked"] = False
                h["lifelines_unlock_date"] = None
                h["lifelines_last_recovery_date"] = None  # RF-13: re-bloqueo
        h["last_processed_date"] = cursor.isoformat()
        _maybe_recover_lifeline(h, cursor)             # RF-14
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
    """Marca el hábito como hecho hoy. Devuelve (hábito_actualizado, ya_estaba_hecho).
    RF-04, RF-05, RF-10, RF-11, RF-12."""
    h = catch_up(habit, today)
    if h["last_processed_date"] == today.isoformat():
        return h, True                                  # RF-05: ya marcado hoy
    continued = h["last_processed_date"] is None or h["last_day_status"] in ("hecho", "salvado")
    h["current_streak"] = h["current_streak"] + 1 if continued else 1
    h["last_day_status"] = "hecho"
    h["last_processed_date"] = today.isoformat()
    if h["current_streak"] > h["record_streak"]:
        h["record_streak"] = h["current_streak"]        # RF-11
    if not h["lifelines_unlocked"] and h["current_streak"] >= 15:
        h["lifelines_unlocked"] = True                  # RF-12
        h["lifelines_available"] = 2
        h["lifelines_unlock_date"] = today.isoformat()
        h["lifelines_last_recovery_date"] = None
    return h, False


def for_display(habit: dict, today: date) -> dict:
    """Recalculo de solo lectura para el listado (RF-15). No se persiste
    el resultado — ver decisión técnica en §5."""
    return catch_up(habit, today)
```

**Por qué esto cubre los casos límite acordados en clarificación**:
- Días fallados consecutivos o separados: cada vuelta del `while` consume 1 salvavida de forma independiente (punto 1 de clarificación).
- Detección sin acción del usuario: `catch_up()` se invoca también desde el listado (punto 2).
- Ventana de 30 días solo activa mientras `lifelines_unlocked`: `_maybe_recover_lifeline()` retorna de inmediato si no está desbloqueado (punto 3).
- Racha que llega a 15 el mismo día de un fallo previo: `catch_up()` resuelve todos los días atrasados en orden cronológico antes de que `mark_done()` procese "hoy", así que nunca compiten en el mismo instante.
- Un día "salvado" nunca incrementa `record_streak` porque solo `mark_done()` (nunca `catch_up()`) actualiza el récord.

---

## 4. Contrato de Rutas

| Método | Path | Protegida | Códigos | Descripción |
|--------|------|-----------|---------|-------------|
| GET | `/dashboard` | Sí | 200 | Lista hábitos con racha/récord recalculados vía `for_display()` (RF-15, RF-16). Sin cambios de persistencia. |
| POST | `/habits` | Sí | 302 → `/dashboard` (éxito o error, con flash) | Crea hábito (RF-01, RF-02, RF-03, RF-17). Requiere CSRF (Constitución §9). |
| POST | `/habits/<habit_id>/done` | Sí | 302 → `/dashboard`, 404 si `habit_id` no existe | Marca como hecho (RF-04, RF-05, RF-06). Requiere CSRF. |

Todas las respuestas de mutación son `302` con mensaje flash (éxito, duplicado, límite alcanzado, ya completado hoy) — igual patrón que `POST /logout` en la Spec 001, no se usa JSON/AJAX en este MVP.

---

## 5. Decisiones Técnicas

| Decisión | Alternativa descartada | Justificación |
|----------|------------------------|----------------|
| Recalcular racha/salvavidas de forma pura (`catch_up`) y **no persistir** el resultado en `GET /dashboard` | Persistir también en el listado | Una petición `GET` sin efectos secundarios es más simple y segura (sin riesgo de guardar datos parcialmente si algo falla a mitad de render); el recálculo es barato (máx. 10 hábitos, O(días transcurridos)) y determinista, así que recalcularlo en cada `GET` no tiene coste real |
| Fechas de racha (`last_processed_date`, `lifelines_*_date`) como `YYYY-MM-DD` (solo fecha) | Timestamps ISO 8601 completos con hora | El corte de "día" es siempre por fecha calendario UTC (RNF de la spec), nunca por instante; usar solo fecha evita bugs de comparar horas irrelevantes |
| `normalize_name()` vive en `habits/validation.py`, separado de la app Flask | Validar/normalizar directamente en `web/routes.py` | Constitución §3: `habits/` debe ser lógica pura sin Flask; así se testea sin `test_client` ni sesión mockeada |
| ID de hábito: `uuid.uuid4().hex[:8]` | ID posicional (índice en la lista) | Un ID posicional se invalida si en el futuro se permite reordenar o borrar (fuera de alcance ahora, pero evita deuda técnica igual a la de `USER_DATA_DIR`) |
| Un solo campo ancla (`lifelines_last_recovery_date` o, en su ausencia, `lifelines_unlock_date`) para calcular la ventana de 30 días | Guardar un historial completo de recuperaciones | No hay requisito de historial (fuera de alcance de esta spec); un único ancla basta para "¿cuándo toca la próxima recuperación?" |
| Detectar "ya marcado hoy" comparando `last_processed_date == today` tras `catch_up()` | Guardar un set/lista de fechas completadas | Sin historial día a día (fuera de alcance), comparar solo la última fecha procesada es suficiente y evita crecer el JSON indefinidamente |
| Sin lock adicional en `POST /habits/<id>/done` | `threading.Lock` por hábito, igual que `RegistrationLock` | Nota de implementación de la Spec 001: un solo worker Gunicorn ya serializa las peticiones; no hay condición de carrera real que proteger aquí |

---

## 6. Estrategia de Tests

### Módulos y cobertura objetivo
| Módulo | Cobertura objetivo | Tests unitarios clave |
|--------|---------------------|------------------------|
| `habits/validation.py` | 100% | `normalize_name`: tildes, mayúsculas, espacios múltiples; `validate_name`: vacío, solo espacios, 101 caracteres, 9 palabras, carácter fuera de charset, caso válido límite (100 chars, 8 palabras) |
| `habits/streak.py` | 100% | `catch_up`: 0 días de gap, 1 día con salvavida, 1 día sin salvavida (reset), múltiples días mixtos, recuperación a los 30 días exactos, recuperación no aplica si no desbloqueado; `mark_done`: primer día, continuación, ya marcado hoy, reinicio tras fallo, desbloqueo exacto en racha 15, récord se actualiza solo con "hecho" nunca con "salvado"; `for_display`: no muta el original (verificar inmutabilidad del `dict` de entrada) |
| `habits/management.py` | 100% | `new_habit`: alta válida, nombre duplicado (con variantes de tildes/mayúsculas), 10 hábitos ya existentes (rechazo), nombre inválido delega en `validate_name` |
| `web/routes.py` (nuevas rutas) | ≥80% | `POST /habits`: éxito, duplicado, límite, sin CSRF (400); `POST /habits/<id>/done`: éxito, ya hecho, id inexistente (404), sin CSRF; `GET /dashboard`: con hábitos, sin hábitos (RF-16), tras varios días simulados (mock de `date.today`) |

### Test de inmutabilidad (buena práctica de función pura)
```python
def test_catch_up_no_muta_el_original():
    original = {...}
    snapshot = dict(original)
    catch_up(original, today)
    assert original == snapshot
```

### Test de racha con múltiples días de gap (caso de clarificación #1)
```python
def test_dos_dias_fallados_consumen_dos_salvavidas_independientes():
    habit = habito_con_racha(15, lifelines_available=2, last_processed_date="2026-09-01")
    resultado = catch_up(habit, today=date(2026, 9, 4))  # 2 días de gap (02 y 03)
    assert resultado["lifelines_available"] == 0
    assert resultado["current_streak"] == 15  # se mantiene, ambos días salvados
```

### Test de reinicio y re-bloqueo (clarificación: pregunta original resuelta)
```python
def test_racha_se_reinicia_y_salvavidas_se_rebloquean():
    habit = habito_con_racha(15, lifelines_available=0, last_processed_date="2026-09-01")
    resultado = catch_up(habit, today=date(2026, 9, 3))  # 1 día de gap sin salvavidas
    assert resultado["current_streak"] == 0
    assert resultado["lifelines_unlocked"] is False
    assert resultado["lifelines_available"] == 0
```

---

## Resumen de Cobertura RF

| RF | Sección del Plan |
|----|--------------------|
| RF-01 | 1 (`habits/management.py`), 2 |
| RF-02 | 1 (`habits/validation.py`, `management.py`), 2, 5 |
| RF-03 | 1 (`habits/validation.py`), 2 |
| RF-04 | 1 (`web/routes.py`), 3 (`mark_done`), 4 |
| RF-05 | 3 (`mark_done`), 4, 6 |
| RF-06 | 4 (404) |
| RF-07 | 3 (`catch_up`) |
| RF-08 | 3 (`catch_up`), 6 |
| RF-09 | 3 (`catch_up`), 6 |
| RF-10 | 3 (`mark_done`) |
| RF-11 | 2, 3 (`mark_done`, récord) |
| RF-12 | 3 (`mark_done`, desbloqueo) |
| RF-13 | 3 (`catch_up`, re-bloqueo), 6 |
| RF-14 | 3 (`_maybe_recover_lifeline`) |
| RF-15 | 3 (`for_display`), 4 |
| RF-16 | 1 (`web/routes.py`, `dashboard.html`) |
| RF-17 | 1 (`habits/management.py`) |
| RF-18 | 2 (modelo de datos aditivo dentro de `data["habits"]`) |

---

**Listo para tareas**. Dudas abiertas de la spec resueltas (normalización confirmada: guion bajo). Próximo paso: descomponer este plan en `tasks.md`.