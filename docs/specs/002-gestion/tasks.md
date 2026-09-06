 # Tasks — Spec 002: Gestión de Hábitos

Tareas de 20-30 min en orden de dependencia. TDD = escribir tests antes que código. Todo lo nuevo vive en `app/habits/` (lógica pura, sin Flask, sin I/O — Constitución §3) salvo la Fase 4.

---

## Fase 0 — Esqueleto del módulo

- [x] **T0.1** Crear `app/habits/` con `__init__.py` (vacío por ahora), `validation.py`, `streak.py`, `management.py` como ficheros vacíos; carpeta `tests/` ya existe, añadir `tests/test_t0_1_habits_structure.py`.
  - RF/RNF: Constitución §3 (separación de responsabilidades)
  - Hecho cuando: `from app import habits` no falla; test verifica que `app/habits/__init__.py` no importa `flask` (inspección de imports o `grep`).
  - Tipo: configuración/estructura.
  - ✅ Completada: 4/4 tests pasan (`tests/test_t0_1_habits_structure.py`). `app/habits/` con `__init__.py`, `validation.py`, `streak.py`, `management.py` vacíos; `import app.habits` OK; test verifica que ninguno de los 4 ficheros referencia `flask` (grep de contenido, Constitución §3). Los reexports del plan §1 se añadirán al completar Fases 1-3.

---

## Fase 1 — Validación de nombres (`habits/validation.py`)

- [x] **T1.1** `NAME_REGEX`, `NAME_MAX_CHARS = 100`, `NAME_MAX_WORDS = 8`; `validate_name(name: str) -> None` que lanza `ValueError` con mensaje específico para: vacío/solo espacios, carácter fuera de charset (Constitución §9: letras/números/espacios/`_-.`), más de 100 caracteres, más de 8 palabras.
  - RF/RNF: RF-03, Constitución §9
  - Hecho cuando: tests cubren cada motivo de rechazo por separado y el caso válido límite (exactamente 100 chars, exactamente 8 palabras) pasa sin excepción.
  - Tipo: TDD.
  - ✅ Completada: 9/9 tests pasan (`tests/test_t1_1_validation.py`). `NAME_MAX_CHARS=100`, `NAME_MAX_WORDS=8`, `NAME_REGEX` compilado. `validate_name` rechaza (con `ValueError` de mensaje específico, en este orden): vacío/solo espacios → 100 chars → charset → 8 palabras. Casos límite (100 chars y 8 palabras exactos, letras Unicode con tildes/ñ) aceptados. Nota: el `re` de stdlib no soporta `\p{}` (feature del módulo `regex`); `NAME_REGEX` usa `\w` Unicode (equivale a `[\p{L}\p{N}_]`, verificado) y ancla `\Z` en vez de `$` para no dejar pasar un `\n` final (esta versión de §9). Sin Flask/I/O (§3).

- [x] **T1.2** `normalize_name(name: str) -> str`: minúsculas, elimina tildes/diacríticos (Unicode NFKD), colapsa espacios múltiples y los reemplaza por `_`.
  - RF/RNF: RF-02
  - Hecho cuando: tests verifican que `"Estudiar   Python"`, `"ESTUDIAR PYTHON"` y `"Estúdiar Pýthon"` normalizan todos a `"estudiar_python"`.
  - Tipo: TDD.
  - ✅ Completada: 6/6 tests pasan (`tests/test_t1_2_normalize.py`). NFKD + descarte de marcas combinantes + NFC + minúsculas + `strip()` + espacios→`_`. Nota: la `ñ` se conserva a propósito (es letra del alfabeto español, no acento — decisión de clarificación); el marcador combinante de tilde (U+0303) tras `n`/`N` no se descarta y NFC la recompone como `ñ`. `-`/`.` se conservan (no son espacios). Solo stdlib (`unicodedata`, `re`), sin Flask/I/O (§3). Se usará como clave de comparación de duplicados en Fase 3; el nombre original se guarda intacto.

---

## Fase 2 — Motor de racha y salvavidas (`habits/streak.py`)

**Tareas delicadas — es el núcleo del producto. TDD estricto, no continuar si un test falla.**

- [x] **T2.1** `catch_up(habit, today)` — caso base: sin gap (habit ya procesado ayer o `last_processed_date is None`) devuelve una copia sin cambios; no muta el `dict` de entrada.
  - RF/RNF: RF-07
  - Hecho cuando: test de inmutabilidad (`original == snapshot` tras llamar) pasa; caso `last_processed_date is None` y caso `last_processed_date == today - 1 día` devuelven el hábito sin alterar racha/salvavidas.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 4/4 tests pasan (`tests/test_t2_1_catch_up.py`). `catch_up` copia el dict (`dict(habit)`), retorna la copia intacta si `last_processed_date is None`, y con `last_processed_date` == ayer o == hoy no hay gap (el `while cursor < today` no itera). El bucle queda vacío de lógica de días fallados (solo avanza `cursor`) — T2.2/T2.3 la rellenan. Sin Flask/I/O (§3).

- [x] **T2.2** `catch_up`: un día fallado sin salvavidas disponibles → `current_streak = 0`, `last_day_status = "fallido"`.
  - RF/RNF: RF-09
  - Hecho cuando: test con `lifelines_available = 0` y 1 día de gap reinicia la racha a 0.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 3/3 tests pasan (`tests/test_t2_2_catch_up_failed_day.py`). Cuerpo del `while`: con `lifelines_available == 0` cada día de gap pone `current_streak=0`, `last_day_status="fallido"` y avanza `last_processed_date` 1 día (al final queda `today - 1`). Con 1 y con 3 días de gap el resultado final es el mismo. La rama `lifelines_available > 0` (salvavidas) queda sin definir — es T2.3. Tests de T2.1 siguen verdes (inmutabilidad intacta).

- [x] **T2.3** `catch_up`: un día fallado con al menos 1 salvavida disponible → consume 1 salvavida, `last_day_status = "salvado"`, racha sin cambios.
  - RF/RNF: RF-08
  - Hecho cuando: test con `lifelines_available = 2` y 1 día de gap deja `lifelines_available = 1`, racha intacta, status `"salvado"`.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 4/4 tests pasan (`tests/test_t2_3_catch_up_lifeline.py`). `if/else` dentro del `while`: rama `== 0` (T2.2) intacta; rama `> 0` consume 1 salvavida y pone `"salvado"` sin tocar `current_streak`. La condición se evalúa en cada iteración, así que con 2 salvavidas y 3 días de gap las 2 primeras consumen y la 3ª cae en la rama sin salvavidas (racha a 0, `"fallido"`) — caso de clarificación verificado. `last_processed_date` sigue avanzando siempre.

- [x] **T2.4** `catch_up`: múltiples días de gap (consecutivos o el resultado acumulado de varios) consumen salvavidas de forma independiente día a día; al agotarlos, el siguiente día fallado reinicia la racha a 0.
  - RF/RNF: RF-08, RF-09 (caso de clarificación: gaps múltiples)
  - Hecho cuando: test con `lifelines_available = 2` y 3 días de gap → 2 salvavidas consumidas + racha reiniciada a 0 en el tercer día.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: cubierto por los tests de T2.3 (caso "3 días de gap con `lifelines_available=2`"), que ya verificaba el consumo independiente de salvavidas día a día seguido de reinicio al agotarse. No se requirió código ni tests adicionales.

- [x] **T2.5** `catch_up`: al reiniciar la racha a 0 estando `lifelines_unlocked = True`, re-bloquear (`lifelines_unlocked = False`, `lifelines_unlock_date = None`, `lifelines_last_recovery_date = None`).
  - RF/RNF: RF-13
  - Hecho cuando: test parte de un hábito con racha 15+ y salvavidas desbloqueados, fuerza un reinicio y verifica el re-bloqueo completo.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 4/4 tests pasan (`tests/test_t2_4_catch_up_reblock.py`). Bloque `if h["lifelines_unlocked"]:` dentro de la rama de reinicio (`lifelines_available == 0`) del `while` de `catch_up`: pone `lifelines_unlocked=False`, `lifelines_unlock_date=None`, `lifelines_last_recovery_date=None`. El re-bloqueo solo aplica al reiniciar la racha a 0, nunca en la rama "salvado"; con `lifelines_unlocked=False` de inicio no hay efectos secundarios.

- [x] **T2.6** `_maybe_recover_lifeline(habit, current_date)`: recupera 1 salvavida (máx. 2) si han pasado ≥30 días desde `lifelines_last_recovery_date` (o `lifelines_unlock_date` si nunca se recuperó ninguno); no hace nada si `lifelines_unlocked` es `False` o ya hay 2 disponibles.
  - RF/RNF: RF-14
  - Hecho cuando: tests cubren: exactamente 30 días → recupera; 29 días → no recupera; ya en máximo (2) → no recupera; `lifelines_unlocked = False` → no recupera aunque hayan pasado 30+ días.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 5/5 tests pasan (`tests/test_t2_6_recover_lifeline.py`). `_maybe_recover_lifeline(h, current_date)` muta in-place: retorna si no está desbloqueado o ya hay 2; ancla = `lifelines_last_recovery_date` (o `lifelines_unlock_date` si nunca se recuperó); si pasaron ≥30 días recupera 1 (máx. 2) y fija `lifelines_last_recovery_date`. Integrada en `catch_up` al final de cada iteración del `while` (tras actualizar `last_processed_date` y antes de avanzar `cursor`), evalúa el `lifelines_available` ya actualizado por la rama de esa vuelta — test de integración verifica que un día "salvado" recupera el salvavida gastado cuando la última recuperación fue hace >30 días.

- [x] **T2.7** `mark_done(habit, today) -> (habit, ya_estaba_hecho)`: aplica `catch_up` primero; si `last_processed_date == today` devuelve `(habit, True)` sin más cambios; si no, incrementa la racha (o la fija a 1 si el día anterior fue "fallido" o es el primer marcado).
  - RF/RNF: RF-04, RF-05, RF-10
  - Hecho cuando: tests cubren: primer marcado de un hábito nuevo (racha pasa a 1); marcado tras un día "hecho"/"salvado" (incrementa); marcado tras un día "fallido" (racha vuelve a 1, no seguir sumando); doble marcado el mismo día (`ya_estaba_hecho = True`, sin cambios).
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 6/6 tests pasan (`tests/test_t2_7_mark_done.py`). `mark_done` = `catch_up` interno + continuidad: un día `"hecho"`/`"salvado"` previo suma 1 (un "salvado" SÍ cuenta, RF-10); si el día anterior quedó `"fallido"` tras el `catch_up` interno, la racha vuelve a 1; doble marcado hoy → `(h, True)` sin cambios; primer marcado → racha 1. No muta el original (copia vía `catch_up`). Sin actualización de récord ni desbloqueo — eso es T2.8.

- [x] **T2.8** `mark_done`: actualizar `record_streak` solo cuando `current_streak` lo supera tras un día "hecho" (nunca tras un día "salvado" en `catch_up`); desbloquear salvavidas (`lifelines_available = 2`, `lifelines_unlocked = True`, `lifelines_unlock_date = today`) exactamente cuando `current_streak` alcanza 15.
  - RF/RNF: RF-11, RF-12
  - Hecho cuando: tests cubren: récord se actualiza solo con incrementos por "hecho"; racha que pasa de 14 a 15 desbloquea; racha que ya estaba desbloqueada no vuelve a resetear `lifelines_available` a 2 al superar 15 de nuevo.
  - Tipo: TDD. **Tarea delicada.**
  - ✅ Completada: 5/5 tests pasan (`tests/test_t2_8_mark_done_record_unlock.py`). En `mark_done`, tras fijar `current_streak`/`hecho`/`last_processed_date` y antes del `return`: `record_streak` se actualiza solo si `current_streak` lo supera (nunca por días "salvado" — test de integración lo confirma: `catch_up` con día salvado deja el récord intacto); desbloqueo solo si `not lifelines_unlocked and current_streak >= 15` (una vez, no en cada marcado posterior — test con racha 20→21 y `lifelines_available=1` verifica que no se resetea a 2).

- [x] **T2.9** `for_display(habit, today)`: llama a `catch_up` y devuelve el resultado sin que el llamador lo persista (contrato: función pura de solo lectura).
  - RF/RNF: RF-15
  - Hecho cuando: test verifica que `for_display` no muta el original y produce el mismo resultado que `catch_up` directamente.
  - Tipo: TDD.
  - ✅ Completada: 5/5 tests pasan (`tests/test_t2_9_for_display.py`). `for_display` = alias semántico de `catch_up` (mismo resultado en sin-gap / gap salvado / gap reinicio; devuelve copia, no muta el original). Su propósito es marcar en el código que este uso es de solo lectura y nunca se persiste (decisión técnica del plan §5). **Fin de Fase 2**: 36/36 tests en `app/habits/streak.py`.

---

## Fase 3 — Alta de hábitos (`habits/management.py`)

- [x] **T3.1** `new_habit(existing_habits: list[dict], raw_name: str) -> dict`: valida (`validate_name`), normaliza (`normalize_name`), comprueba duplicado contra `normalized_name` de `existing_habits` (`ValueError` si coincide), genera `id = uuid.uuid4().hex[:8]` y devuelve el hábito con valores iniciales (racha 0, récord 0, 0 salvavidas, `last_processed_date = None`, `last_day_status = "none"`).
  - RF/RNF: RF-01, RF-02
  - Hecho cuando: tests cubren: alta válida; nombre duplicado exacto; nombre duplicado tras normalización (mayúsculas/tildes/espacios); nombre inválido delega el `ValueError` de `validate_name`.
  - Tipo: TDD.
  - ✅ Completada: 6/6 tests pasan (`tests/test_t3_1_new_habit.py`). `new_habit` valida → normaliza → rechaza duplicado comparando `normalized_name` (exacto o tras normalización) → devuelve dict con valores iniciales (`name` = `raw_name.strip()`, `id` = `uuid.uuid4().hex[:8]`, racha/récord/salvavidas 0, `last_processed_date=None`, `last_day_status="none"`). IDs distintos entre llamadas. El `ValueError` de nombre inválido propaga el de `validate_name` (mensaje de validation, no genérico). Importa solo stdlib (`uuid`) + `app.habits.validation` — sin Flask (§3, verificado por test de estructura). Sin límite de 10 aún — es T3.2.

- [x] **T3.2** `new_habit`: rechaza con `ValueError` si `len(existing_habits) >= 10` antes de cualquier otra validación (o después — decidir orden y documentarlo en el test).
  - RF/RNF: RF-17
  - Hecho cuando: test con 10 hábitos existentes y un alta nueva lanza `ValueError` mencionando el límite.
  - Tipo: TDD.
  - ✅ Completada: 3/3 tests pasan (`tests/test_t3_2_new_habit_limit.py`). Orden decidido y testeado: el chequeo de límite es la PRIMERA línea de `new_habit` (antes de `validate_name`/normalización), así que con 10 hábitos existentes y un nombre inválido se lanza el `ValueError` de límite, no el de nombre vacío (verificado por el mensaje exacto). Con 9 hábitos el alta funciona. Tests de T3.1 intactos (9/9 en `app/habits/management.py`). **Fin de Fase 3.**

---

## Fase 4 — Rutas web e interfaz

- [x] **T4.1** `web/routes.py`: `POST /habits` (CSRF, `@login_required`) — llama a `habits.new_habit`, guarda con `storage.save()` si es válido, flash de éxito o de error (duplicado/límite/nombre inválido), redirect a `/dashboard`.
  - RF/RNF: RF-01, RF-02, RF-03, RF-17
  - Hecho cuando: tests de integración cubren: alta exitosa (302 + hábito en `storage.load()`); duplicado (302 + flash de error, sin persistir); límite de 10 (302 + flash); sin CSRF (400); sin sesión (302 a `/login`).
  - Tipo: TDD.
  - ✅ Completada: 6/6 tests pasan (`tests/test_t4_1_create_habit.py`). Ruta `POST /habits` en el blueprint `web` con `@login_required`: `storage.load()` (no `load_with_status()`, coherente con fileops que ya sanea corrupción → estructura `{"habits": [...]}`) → `new_habit` → guarda si es válido; `ValueError` (duplicado/límite/nombre inválido) → flash de error. Redirect a `/dashboard` con CSRF global activo (§9). Flash verificado vía `session["_flashes"]` (la zona de flash visible se añade en T4.4).

- [x] **T4.2** `web/routes.py`: `POST /habits/<habit_id>/done` (CSRF, `@login_required`) — busca el hábito por `id`, llama a `habits.mark_done`, guarda, flash según `ya_estaba_hecho`, redirect a `/dashboard`; `habit_id` inexistente → 404.
  - RF/RNF: RF-04, RF-05, RF-06
  - Hecho cuando: tests cubren: marcado exitoso; ya marcado hoy (flash distinto, sin duplicar); `habit_id` inexistente (404); sin CSRF (400).
  - Tipo: TDD.
  - ✅ Completada: 6/6 tests pasan (`tests/test_t4_2_mark_habit_done.py`). Ruta `POST /habits/<habit_id>/done` con `@login_required` + CSRF global: busca el índice por `id` con `enumerate()` en una sola pasada (ver decisión técnica abajo), `mark_done(habit, _today_utc())`, guarda y flash de éxito/info según `already_done`; `habit_id` inexistente → `abort(404)`; sin CSRF → 400; anónimo → 302 `/login`. Test con 2 hábitos confirma que marcar uno no afecta al otro. **Decisión técnica**: se usa `next((i for i,h in enumerate(...) if h["id"] == habit_id), None)` en vez de `data["habits"].index(habit)` — `list.index` compara por igualdad estructural de dicts y devolvería la primera coincidencia si hubiera dos dicts idénticos, mientras que buscar por `id` (único, uuid) en la misma pasada es determinista y no depende de la igualdad de dicts.

- [x] **T4.3** `web/routes.py`: extender `GET /dashboard` para recorrer `data["habits"]`, aplicar `habits.for_display(h, hoy_utc())` a cada uno (sin persistir) y pasar la lista resultante a la plantilla; invitación a crear el primer hábito si la lista está vacía.
  - RF/RNF: RF-15, RF-16
  - Hecho cuando: tests cubren: lista vacía (mensaje de invitación); lista con hábitos (racha/récord recalculados, verificado mockeando la fecha "hoy" varios días adelante del `last_processed_date` guardado); el archivo en disco no cambia tras el `GET` (verifica la decisión de no persistir en lectura).
  - Tipo: TDD.
  - ✅ Completada: 4/4 tests pasan (`tests/test_t4_3_dashboard_habits.py`). `dashboard` aplica `for_display(h, _today_utc())` a cada hábito en una lista NUEVA `habits` (no toca `data["habits"]` ni llama a `storage.save()`). Tests: invitación con lista vacía; 2 hábitos con gap de 5 días y sin salvavidas se muestran con "Racha: 0" aunque el valor guardado sea mayor; **crítico**: tras el `GET`, `storage.load()` directo sigue devolviendo el `current_streak` ORIGINAL (el archivo no cambió); sin gap muestra el valor guardado. Ajuste mínimo de `dashboard.html` (iterar `habits` y mostrar `Racha: N`); `tests/test_t3_5_dashboard.py::test_dashboard_with_habits_lists_them` se actualizó a un hábito con el esquema completo de la Spec 002 (el dict mínimo `{"name": ...}` de Spec 001 rompería `for_display`; en producción Spec 001 nunca creó hábitos, lista siempre vacía — migración aditiva, RF-18).

- [x] **T4.4** `web/templates/dashboard.html`: formulario de alta (`POST /habits`, campo nombre, CSRF), lista de hábitos (nombre, racha actual, récord) con botón "Marcar como hecho" por hábito (`POST /habits/<id>/done`, CSRF), zona de mensajes flash.
  - RF/RNF: RF-15, RF-16
  - Hecho cuando: test de integración sobre `GET /dashboard` verifica presencia del formulario, la lista renderizada y los botones con el `habit_id` correcto en la URL de cada uno.
  - Tipo: TDD (verificación de render, no unitario de lógica).
  - ✅ Completada: 4/4 tests pasan (`tests/test_t4_4_dashboard_template.py`). Plantilla completa: zona flash (`get_flashed_messages(with_categories=true)`), formulario de alta (`action="/habits"`, input `name` con `maxlength=100` y `required`), lista con nombre/racha/récord y botón "Marcar como hecho" por hábito (`action="/habits/<id>/done"` verificado para 2 ids distintos, sin mezclas), todos los formularios con token CSRF (mismo patrón `{{ csrf_token() }}` que logout; verificado 4/4 con 2 hábitos). Nota: el flash se renderiza escapado por Jinja2 (`'` → `&#39;`, §9), el test lo contempla. **Fin de Fase 4.**

---

## Fase 5 — Validación final

- [x] **T5.1** Ejecutar la suite completa y verificar cobertura: 100% en `app/habits/` (validation, streak, management), ≥80% en las rutas nuevas de `app/web/routes.py`.
  - RF/RNF: NFR de la spec (cobertura), Constitución §4
  - Hecho cuando: `pytest -v` 100% verde; `coverage` reporta 100% en `app/habits/*` y ≥80% en `app/web/routes.py`; actualizar `.github/workflows/tests.yml` si el paso de cobertura por archivo (creado en Spec 001 para `storage/`) necesita extenderse a `habits/`.
  - Tipo: validación.
  - ✅ Completada: suite completa **181 passed** (4 fallos preexistentes en `tests/test_t0_3_secrets.py`, ajenos a la Spec 002 — verificados con `git stash` en T0.1: el `.env` local anula el `monkeypatch.delenv`; no bloquean). Cobertura: `app/habits/validation.py` 100%, `app/habits/streak.py` 100%, `app/habits/management.py` 100%, `app/web/routes.py` 100% (objetivo ≥80%). Total 96%. Workflow actualizado: el paso de cobertura por archivo ahora usa un mapa de umbrales (`app/storage/` ≥80%, `app/habits/` 100%, `app/web/routes.py` ≥80%); YAML validado con PyYAML y el script embebido ejecutado localmente contra `coverage.json` real (generado con el mismo comando de CI) → "OK: cobertura por archivo cumple umbrales".

- [x] **T5.2** Recorrer manualmente el checklist de "Criterios de finalización" de `spec.md` (Spec 002) y confirmar cada uno con evidencia (test o demo manual).
  - RF/RNF: todos (RF-01 a RF-18)
  - Hecho cuando: los 4 criterios de finalización de la spec están marcados con la evidencia correspondiente (tests verdes, demo manual documentada); ninguna regla de Constitución §3/§4/§9 violada; formato del JSON de usuario sigue siendo compatible con el de la Spec 001 (migración aditiva verificada con un archivo real de la Spec 001 sin campo `habits` poblado).
  - Tipo: validación.
  - ✅ Completada: 4/4 criterios verificados con evidencia real. (1) RF-01 a RF-18 mapeados a tests verdes (80/80 tests de Spec 002; detalle RF→archivo en la nota del commit/sesión). (2) Cobertura 100% en `app/habits/` y 100% en `app/web/routes.py` (≥80%) — T5.1. (3) Demo manual contra la app corriendo por HTTP real (servidor werkzeug + cookies/sesión/CSRF reales), con reloj simulado parcheando `routes._today_utc` (única simulación; no se esperaron días reales): crear hábito, marcar 4 días seguidos (racha 4), 3 días sin marcar sin salvavidas → listado Racha 0/Récord 4 (sin persistir); racha 15 → desbloqueo 2 salvavidas; fallo con salvavidas → racha intacta (16); fallo sin salvavidas → Racha 0/Récord 16 + re-bloqueo persistido (racha 1, salvavidas 0, unlocked False). (4) Migración: archivo real Spec 001 exacto (`habits: []`, `metadata.created_at`) → `storage.load()` idéntico, GET /dashboard 200, POST /habits OK, `metadata` intacta tras guardar (aditivo, RF-18). **Riesgo conocido declarado** (KeyError si un hábito del JSON carece de campos del esquema nuevo — JSON válido pero parcial): aceptado para el MVP, documentado en comentario en `app/habits/streak.py::catch_up`; evaluar validación de esquema en una spec futura. Suite: 181 passed, 4 fallos preexistentes en `tests/test_t0_3_secrets.py` (ajenos, verificados en T0.1). **Veredicto: Spec 002 completa.**

---

### Notas
- Fase 2 (T2.1 a T2.9) es el núcleo delicado: cada tarea debe pasar sus tests antes de continuar a la siguiente, ya que T2.6 a T2.9 dependen del comportamiento exacto de `catch_up` construido en T2.1–T2.5.
- Orden de dependencia estricto: F0 → F1 → F2 → F3 → F4 → F5. Dentro de F4, T4.1 y T4.2 pueden hacerse en paralelo entre sí (ambas dependen de F2/F3, no una de otra), pero T4.3 y T4.4 dependen de que ambas rutas de mutación ya existan para poder enlazarlas desde la plantilla.
- Al final de cada tarea: `pytest` y confirmar que no se viola la separación `habits/` sin Flask (Constitución §3).