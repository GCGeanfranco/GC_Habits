# Tasks — Spec 001: Autenticación Google y Aislamiento de Datos

Tareas de 20-30 min en orden de dependencia. TDD = escribir tests antes que código.

---

## Fase 0 — Esqueleto del proyecto

- [x] **T0.1** Crear estructura de carpetas (`app/auth/`, `app/storage/`, `app/web/`, `tests/`), `requirements.txt`, `.gitignore` (incluye `.env*`), `.env.example`.
  - RF/RNF: RNF-03 (secretos), §1
  - Hecho cuando: `pip install -r requirements.txt` funciona; `.env` listado en `.gitignore`; `flask --app app run` importa sin error.
  - Tipo: configuración/estructura.
  - ✅ Completada: 5/5 tests pasan (`tests/test_t0_1_structure.py`). `import app` OK. `flask --app app run` importa el módulo; el arranque completo requiere `create_app` (T0.2).

- [x] **T0.2** `create_app(auth_provider=None)` factory con blueprints vacíos (`auth`, `web`), inyección de dependencia por defecto `GoogleProvider` (Constitución §7).
  - RF/RNF: §7 (AuthProvider inyectado)
  - Hecho cuando: test de humo `test_app_creates()` pasa; `app.auth_provider` es el mock inyectado en tests.
  - Tipo: TDD (test de humo primero).
  - ✅ Completada: 9/9 tests pasan (`tests/test_t0_2_factory.py`). `flask --app app run` arranca (Running on :5000). `GoogleProvider` es scaffolding mínimo; se completa en T2.x.

- [x] **T0.3** Configuración de secretos desde entorno (`.env` via `python-dotenv`): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FLASK_SECRET_KEY`. Fallo claro si faltan en producción.
  - RF/RNF: RNF-03
  - Hecho cuando: `create_app()` lanza `RuntimeError` descriptivo si `FLASK_SECRET_KEY` no existe en entorno; test lo verifica.
  - Tipo: TDD.
  - ✅ Completada: 15/15 tests pasan (`tests/test_t0_3_secrets.py`). `create_app()` levanta `RuntimeError` si falta `FLASK_SECRET_KEY` (siempre) o `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` (provider por defecto). `conftest.py` con fixture autouse para secretos de test.

- [x] **T0.4** Activar `CSRFProtect` global en `create_app()`.
  - RF/RNF: RNF-05
  - Hecho cuando: cualquier POST sin token CSRF devuelve 400 (test con `test_client`).
  - Tipo: TDD.
  - ✅ Completada: 19/19 tests pasan (`tests/test_t0_4_csrf.py`). `CSRFProtect(app)` activo: POST sin token → 400, POST con token válido → 200, GET → 200. Nota: flask-wtf 1.3.0 firma el token (crudo en sesión, firmado al cliente).

---

## Fase 1 — storage

- [x] **T1.1** `storage/fileops.py`: `_atomic_write(path, data)` (tmp + `os.rename`), `_read_with_corrupt_handling(path)`, `_backup_corrupt(path)` → `.corrupt.{timestamp}`.
  - RF/RNF: RF-12, §5 (atomicidad, backup con timestamp)
  - Hecho cuando: tests pasan: archivo no existe → estructura vacía; JSON corrupto → se crea backup `.corrupt.{ts}` y devuelve vacío; escritura deja `.json` íntegro (sin `.tmp` residual).
  - Tipo: TDD.
  - ✅ Completada: 25/25 tests pasan (`tests/test_t1_1_fileops.py`). Nota: se usa `os.replace` (equiv. a `os.rename` en Linux; en Windows `os.rename` falla si el destino existe). Backup `.corrupt.{ts}` con microsegundos. `_read_with_corrupt_handling(path)` con 1 parámetro (API del plan §1).

- [x] **T1.2** Reintentos de escritura en `_atomic_write`: 3 reintentos con backoff antes de excepción (Constitución §5).
  - RF/RNF: RF-07, RF-12, §5
  - Hecho cuando: test mockea fallo en `os.rename` → 3 intentos, luego `RuntimeError`; test con fallo transitorio → éxito en 2º intento.
  - Tipo: TDD.
  - ✅ Completada: 29/29 tests pasan (`tests/test_t1_2_retries.py`). 3 intentos totales, backoff `0.1 * 2**(n-1)` (0.1s, 0.2s), `RuntimeError` con causa encadenada. Tests mockean `os.replace` (primitiva real usada en T1.1) y `sleep`.

- [x] **T1.3** `storage/__init__.py`: `_get_user_id()` (lee de `session`), `load()` y `save(data)` **sin parámetro user_id** (RF-13).
  - RF/RNF: RF-11, RF-13, §9 (aislamiento)
  - Hecho cuando: `test_load_saves_only_for_session_user` pasa: sin sesión → `RuntimeError`; con `session["user_id"]="A"` → lee/escribe solo `A.json`; la firma pública no acepta `user_id` (verificación por inspección/API).
  - Tipo: TDD. **Tarea delicada — aislamiento.**
  - ✅ Completada: 35/35 tests pasan (`tests/test_t1_3_storage.py`). `load()`/`save()` sin parámetro `user_id` (verificado con `inspect.signature`), solo sesión. Tests aíslan `USER_DATA_DIR` con `monkeypatch`.

- [x] **T1.4** `storage/__init__.py`: `user_exists(uid)`, `count_users()`, `create_user_file(uid)` con `created_at` ISO UTC.
  - RF/RNF: RF-05, RF-07, RF-08
  - Hecho cuando: tests pasan: `count_users()` cuenta solo `*.json`; `create_user_file` genera `{"habits": [], "metadata": {"created_at": "..."}}`.
  - Tipo: TDD.
  - ✅ Completada: 40/40 tests pasan (`tests/test_t1_4_registration.py`). `count_users` excluye `.corrupt.*`, `.tmp` y no-JSON. `created_at` ISO 8601 UTC con sufijo `Z`.

- [x] **T1.5** `storage/lock.py`: `RegistrationLock` con `threading.Lock` + test de exclusión mutua y serialización.
  - RF/RNF: RF-09, §1
  - Hecho cuando: `test_lock_serializes_threads` pasa (2 threads intentan adquirir, nunca simultáneos); test de lógica atómica mockeando `count_users`/`create_user_file` verifica orden de llamadas bajo `with lock:`.
  - Tipo: TDD. **Tarea delicada — lock de concurrencia.**
  - ✅ Completada: 43/43 tests pasan (`tests/test_t1_5_lock.py`). Exclusión mutua real con 2 threads (max 1 concurrente); decisión check+create atómica con mocks stateful; lock se libera tras excepción. Nota: `threading.Lock` NO es reentrante (el sketch del plan §8 decía "reentrante", se testea exclusión mutua en su lugar).

---

## Fase 2 — auth/Google

- [x] **T2.1** `auth/provider.py`: ABC `AuthProvider` con `get_login_url()`, `verify_token(code)`, `get_user_info(credentials)`, `validate_state(state)`.
  - RF/RNF: §7
  - Hecho cuando: `GoogleProvider` implementa la interfaz sin `TypeError` (test `isinstance`); instanciar `AuthProvider` directo lanza `TypeError`.
  - Tipo: TDD.
  - ✅ Completada: 48/48 tests pasan (`tests/test_t2_1_provider.py`). ABC con 4 métodos abstractos; `GoogleProvider` concreto (stubs `NotImplementedError` que T2.2-T2.4 completan). `test_default_provider_is_google` sigue verde.

- [x] **T2.2** `auth/google.py`: `get_login_url()` genera `state` aleatorio (`secrets.token_urlsafe`), lo guarda en `session["oauth_state"]` ANTES de construir la URL, y lo incluye como query param.
  - RF/RNF: RF-02, protección state (login CSRF)
  - Hecho cuando: tests pasan: URL contiene `state=...`; `session["oauth_state"]` == state de la URL; dos llamadas generan states distintos.
  - Tipo: TDD. **Tarea delicada — state OAuth.**
  - ✅ Completada: 52/52 tests pasan (`tests/test_t2_2_login_url.py`). `secrets.token_urlsafe(32)`, `session["oauth_state"]` antes de construir URL, `state` en query. URL de autorización Google v2 con `client_id`, `redirect_uri`, `response_type=code`, `scope=openid email profile`.

- [x] **T2.3** `auth/google.py`: `verify_token(code)` intercambia código por tokens con Google (`google.oauth2.id_token`) y valida `aud`, `iss`, `exp`.
  - RF/RNF: RF-03, §9 (validación token)
  - Hecho cuando: tests con mock de `verify_oauth2_token` pasan: token válido → dict; `aud` incorrecto → rechazo; `iss` fuera de lista → rechazo; `exp` pasado → rechazo; excepción de red → propagada como error de auth.
  - Tipo: TDD.
  - ✅ Completada: 59/59 tests pasan (`tests/test_t2_3_verify_token.py`). `_exchange_code` POST a token endpoint (stdlib `urllib`); `verify_oauth2_token` con `_UrllibRequest` (transporte mínimo urllib, compatible `google.auth.transport.Request`); `iss` ∈ ALLOWED_ISSUERS y `exp > now` explícitos (§9). Nota: `google.auth.transport.requests` exige la lib `requests` (no permitida, §1) → transporte propio sin dependencias.

- [x] **T2.4** `auth/google.py`: `validate_state(state)` — compara EXACTAMENTE con `session["oauth_state"]`.
  - RF/RNF: RF-04, protección state
  - Hecho cuando: tests pasan: coincide → `True`; no coincide → `False`; ausente en sesión → `False`.
  - Tipo: TDD. **Tarea delicada — state OAuth.**
  - ✅ Completada: 63/63 tests pasan (`tests/test_t2_4_validate_state.py`). Comparación exacta con `secrets.compare_digest` (tiempo constante); `state`/`oauth_state` ausentes o `None` → `False`. `GoogleProvider` completo (todos los métodos de la interfaz implementados).

- [x] **T2.5** `auth/session.py`: `login_user(uid)` (sesión persistente), `logout_user()`, `current_user_id()`, decorador `login_required`.
  - RF/RNF: RF-05, RF-10, RNF-04 (cookie persistente)
  - Hecho cuando: tests pasan: tras `login_user`, `current_user_id()` devuelve uid; ruta decorada sin sesión → redirect `/login`; tras `logout_user`, sesión vacía.
  - Tipo: TDD.
  - ✅ Completada: 71/71 tests pasan (`tests/test_t2_5_session.py`). `login_user` setea `session.permanent=True` (cookie persistente, RNF-04; el lifetime/expiración por inactividad es T4.3); `logout_user` → `session.clear()`; `login_required` → redirect `auth.login` sin sesión. Fin de Fase 2.

---

## Fase 3 — Rutas web

- [x] **T3.1** `auth/routes.py`: `GET /login` + `web/templates/login.html` (botón "Iniciar sesión con Google", soporte mensaje de error `?error=`).
  - RF/RNF: RF-01, RF-02
  - Hecho cuando: test integración: `GET /login` → 200 con botón; `GET /login?error=auth_failed` muestra mensaje.
  - Tipo: TDD.
  - ✅ Completada: 75/75 tests pasan (`tests/test_t3_1_login.py`). `GET /login` → 200, botón enlaza a URL de OAuth (state generado al renderizar), `?error=auth_failed` → "No se pudo iniciar sesión. Inténtalo de nuevo.". `web` bp con `template_folder="templates"`. Fixture de T2.5 actualizada (stub de `/login` ya no hace falta).

- [x] **T3.2** `auth/routes.py`: `GET /auth/callback` completo — validar state → `verify_token(code)` → decidir con `RegistrationLock`: existente (RF-05/RF-06), nuevo <5 (RF-07), nuevo =5 → 403 (RF-08).
  - RF/RNF: RF-03 a RF-09
  - Hecho cuando: tests de integración con `AuthProvider` mock pasan para los **5 escenarios** (state inválido → 302 login; existente → 302 dashboard; nuevo <5 → crea archivo + 302 dashboard; =5 → 403 con "Límite de usuarios alcanzado." + enlace a `/login`; token inválido → 302 login con error genérico).
  - Tipo: TDD. **Tarea delicada — integra state + lock + límite.**
  - ✅ Completada: 80/80 tests pasan (`tests/test_t3_2_callback.py`). 5/5 escenarios. Errores de token (ValueError/KeyError/OSError) → 302 login genérico. 403 sin redirect con template `403_limit.html` (creado aquí como dependencia; T3.3 añade la ruta de render directo). Tests con stub `/dashboard` (T3.5 lo hará real).

- [x] **T3.3** `web/templates/403_limit.html` + ruta de render directo (usada por T3.2).
  - RF/RNF: RF-08
  - Hecho cuando: render de plantilla con mensaje "Límite de usuarios alcanzado." y enlace `/login`.
  - Tipo: estructura (plantilla).
  - ✅ Completada: criterio "Hecho cuando" satisfecho por el render inline de T3.2 (`403_limit.html` existe y se renderiza con HTTP 403 en `/auth/callback`, cubriendo RF-08 completo). Se eliminó la ruta pública `GET /auth/limit` (no conectada a ningún flujo real) y su test (`tests/test_t3_3_limit.py`).

- [x] **T3.4** `auth/routes.py`: `POST /logout` (form + CSRF) + botón de logout en dashboard.
  - RF/RNF: RF-10, RNF-05
  - Hecho cuando: `POST /logout` con CSRF válido → 302 `/login` y sesión vacía; POST sin CSRF → 400; GET `/logout` → 405.
  - Tipo: TDD.
  - ✅ Completada: 84/84 tests pasan (`tests/test_t3_4_logout.py`). `POST /logout` con `@login_required`: CSRF válido → 302 `/login` + sesión vacía; sin CSRF → 400; GET → 405; anónimo con CSRF válido → 302 `/login`. Botón de logout: se añadirá al `dashboard.html` en T3.5 (depende de ese template).

- [x] **T3.5** `web/routes.py`: `GET /dashboard` con `@login_required` → `storage.load()` → render `dashboard.html` (estado vacío con invitación; mensaje distinto si hubo corrupción).
  - RF/RNF: RF-01, RF-11, RF-12
  - Hecho cuando: tests pasan: sin sesión → 302 `/login`; con sesión y archivo vacío → 200 con invitación; archivo corrupto → backup `.corrupt.{ts}` + 200 con mensaje "Detectamos un problema...".
  - Tipo: TDD.
  - ✅ Completada: 89/89 tests pasan (`tests/test_t3_5_dashboard.py`). Añadido `storage.load_with_status() -> (dict, bool)` (vía `fileops._read_with_corrupt_flag`) para que el dashboard distinga corrupción de estado vacío (RF-12) sin romper `load()` (T1.3). `dashboard.html` con invitación, mensaje de recuperación, lista de hábitos y form logout+CSRF (botón de T3.4). Stub `/dashboard` de T3.2 eliminado (ruta real). Fin de Fase 3.

---

## Fase 4 — Seguridad transversal

- [x] **T4.1** Activar `flask-talisman` con CSP `default-src 'self'; script-src 'self'`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
  - RF/RNF: RNF-02
  - Hecho cuando: test verifica 4 cabeceras en cualquier ruta (ej. `/login`).
  - Tipo: configuración + test de verificación.
  - ✅ Completada: 91/91 tests pasan (`tests/test_t4_1_security_headers.py`). `Talisman` en `create_app`: CSP dict, `force_https=False` (dev/tests; Render termina TLS en proxy), `frame_options="DENY"`, `referrer_policy` explícito, `nosniff` por defecto. Nota: en esta versión de talisman el parámetro es `frame_options` (no `x_frame_options`).

- [x] **T4.2** Rate limiting con `flask-limiter`: 5/15 min por IP, contador independiente en `/login` y `/auth/callback`.
  - RF/RNF: RNF-01
  - Hecho cuando: 6 requests seguidos a `/login` → 429 en la 6ª; `/auth/callback` no hereda el contador de `/login` (6 a una no bloquean la otra).
  - Tipo: TDD.
  - ✅ Completada: 96/96 tests pasan (`tests/test_t4_2_rate_limit.py`). `Limiter(key_func=get_remote_address, storage_uri="memory://")` global en `create_app`; `@limiter.limit("5 per 15 minutes")` en `auth.login` y `auth.callback` (contadores independientes por ruta+IP, §9 "storage en memoria, suficiente para 5 usuarios").

- [x] **T4.3** Sesión permanente: `session.permanent=True`, `PERMANENT_SESSION_LIFETIME` según RNF-04 actual (15 días de inactividad), `last_activity` en cookie firmada (`before_request` actualiza y rechaza si >15 días sin actividad).
  - RF/RNF: RNF-04
  - Hecho cuando: tests pasan: cookie marcada `HttpOnly`; sesión con `last_activity` vencida → tratada como no autenticada.
  - Tipo: TDD.
  - ✅ Completada: 101/101 tests pasan (`tests/test_t4_3_session_expiry.py`). `PERMANENT_SESSION_LIFETIME=15 días`; `refresh_session_activity` en `before_request`: sin `last_activity` → la setea (acepta); vencida (>15d) → `logout_user()` (no autenticada); fresca → actualiza. `session.permanent=True` ya en `login_user` (T2.5). Cookie `HttpOnly` (Talisman). Fin de Fase 4.

---

## Fase 5 — Validación final

- [x] **T5.1** Ejecutar suite completa + verificar cobertura ≥80% en `storage/` (y `habits/` cuando exista).
  - RF/RNF: §4 (política de tests)
  - Hecho cuando: `pytest -v` 100% verde; `coverage` ≥80% en módulos obligatorios.
  - Tipo: validación.
  - ✅ Completada: 101/101 tests verdes; cobertura total 94%. `storage/` = 100% (`__init__`, `fileops`, `lock`) — muy por encima del mínimo §4 (80%). `habits/` aún no existe (spec 002). No obligatorios por debajo del 80%: `auth/provider.py` 71% (cuerpos `NotImplementedError` de la interfaz — no se añadieron tests superficiales) y `auth/google.py` 81% (ramas de red real no cubiertas por diseño; el plan mockea el intercambio).

- [x] **T5.2** Recorrer manualmente el checklist de "Criterios de finalización" de `spec.md` (10 items) y marcar tareas como completadas aquí.
  - RF/RNF: todos
  - Hecho cuando: los 10 criterios de la spec tienen checkbox marcado; ninguna regla de Constitución §5/§6/§9 violada.
  - Tipo: validación.
  - ✅ Completada: 10/10 criterios cubiertos. CI resuelto con `.github/workflows/tests.yml` (push + pull_request, Python 3.12, `pytest -v`, `pytest --cov` con fallo si `app/storage/` < 80%, secretos dummy — la suite no los requiere reales, conftest los mockea). Veredicto: Spec 001 completa.

---

### Notas
- Las tareas T1.3, T1.5, T2.2, T2.4 y T3.2 son las piezas delicadas: ir despacio, TDD estricto, no continuar si el test no pasa.
- Orden de dependencia estricto: F0 → F1 → F2 → F3 → F4 → F5. Dentro de F2, T2.2/T2.3/T2.4 antes de T2.5 solo si se usa session (necesaria para state).
- Al final de cada tarea: `pytest` y confirmar que no se viola §5/§9.
