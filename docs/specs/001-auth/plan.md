# Plan Técnico — Spec 001: Autenticación Google y Aislamiento de Datos

---

## 1. Estructura de Módulos

### `app/auth/`
| Archivo | Responsabilidad | API Pública |
|---------|----------------|-------------|
| `provider.py` | Interfaz `AuthProvider` (Constitución §7) | `class AuthProvider(ABC): get_login_url() -> str; verify_token(code: str) -> dict; get_user_info(credentials) -> dict; validate_state(state: str) -> bool` |
| `google.py` | Implementación Google OAuth | `class GoogleProvider(AuthProvider): __init__(client_id, client_secret, redirect_uri); get_login_url()` (genera `state` aleatorio, lo guarda en `session` y lo incluye en la URL de autorización); `verify_token(code)`; `get_user_info(credentials)`; `validate_state(state) -> bool` (compara contra el guardado en sesión) |
| `session.py` | Gestión de sesión Flask + decoradores | `login_user(user_id: str) -> None; logout_user() -> None; current_user_id() -> Optional[str]; login_required(f) -> f` |
| `routes.py` | Rutas `/login`, `/auth/callback`, `/logout` | `bp = Blueprint('auth', ...)` |

**Cubre**: RF-02, RF-03, RF-04, RF-05, RF-06, RF-08, RF-10, RF-13, RNF-03, RNF-05, protección state (login CSRF)

### `app/storage/`
| Archivo | Responsabilidad | API Pública |
|---------|----------------|-------------|
| `__init__.py` | Exporta funciones públicas | `load() -> dict; save(data: dict) -> None; user_exists(user_id: str) -> bool; count_users() -> int; create_user_file(user_id: str) -> None` |
| `fileops.py` | I/O atómico, locking, corrupt handling | `_atomic_write(path, data); _read_with_corrupt_handling(path) -> dict; _backup_corrupt(path) -> None` |
| `lock.py` | Lock de registro (RF-09) | `class RegistrationLock: __enter__(); __exit__()` |

**Cubre**: RF-07, RF-09, RF-11, RF-12, RF-13, Constitución §5, §9

### `app/web/`
| Archivo | Responsabilidad | API Pública |
|---------|----------------|-------------|
| `routes.py` | Rutas `/dashboard`, decorador `@login_required` en blueprint | `bp = Blueprint('web', ...)` |
| `templates/base.html` | Layout base con CSP nonce, CSRF token | — |
| `templates/login.html` | Página login + botón Google + mensajes error | — |
| `templates/dashboard.html` | Dashboard con lista hábitos (vacía en esta spec) | — |
| `templates/403_limit.html` | Página límite alcanzado (RF-08) | — |

**Cubre**: RF-01, RF-08, RF-11, RF-12, RNF-01, RNF-02, RNF-04, RNF-05

### `app/__init__.py`
- `create_app(auth_provider: AuthProvider = None) -> Flask`: Factory que inyecta proveedor (Constitución §7), configura Talisman, Limiter, CSRF, sesión, blueprints.

---

## 2. Modelo de Datos

**Ubicación**: `/data/users/{user_id}.json`

```json
{
  "habits": [],
  "metadata": {
    "created_at": "2026-09-01T12:00:00Z"
  }
}
```

- `created_at`: ISO 8601 UTC, se setea en `create_user_file()` (RF-07).
- `habits`: Array vacío en esta spec; se poblará en spec 002.
- `last_activity`: **NO vive en el JSON** — se gestiona exclusivamente en la cookie firmada (ver §7, decisión técnica).

---

## 3. Diseño de `storage.py` — Aislamiento Garantizado (RF-13)

**Principio**: `load()` y `save()` **no reciben `user_id` como parámetro**. Lo obtienen de la sesión verificada internamente.

```python
# app/storage/__init__.py
from flask import session
from .fileops import _read_with_corrupt_handling, _atomic_write

USER_DATA_DIR = Path("/data/users")

def _get_user_id() -> str:
    """Obtiene user_id de la sesión Flask verificada (firmada)."""
    uid = session.get("user_id")
    if not uid:
        raise RuntimeError("No hay usuario en sesión")
    return uid

def _user_path(user_id: str) -> Path:
    return USER_DATA_DIR / f"{user_id}.json"

def load() -> dict:
    """Carga datos del usuario autenticado. RF-11, RF-12, RF-13."""
    user_id = _get_user_id()
    path = _user_path(user_id)
    return _read_with_corrupt_handling(path, user_id)

def save(data: dict) -> None:
    """Guarda datos del usuario autenticado. RF-13, Constitución §5."""
    user_id = _get_user_id()
    path = _user_path(user_id)
    _atomic_write(path, data)

def user_exists(user_id: str) -> bool:
    """Verifica existencia SIN usar sesión (solo para callback auth). RF-05, RF-06, RF-07."""
    return _user_path(user_id).exists()

def count_users() -> int:
    """Cuenta archivos .json en /data/users (solo para callback auth). RF-07, RF-08."""
    return len(list(USER_DATA_DIR.glob("*.json")))

def create_user_file(user_id: str) -> None:
    """Crea archivo vacío para usuario nuevo. RF-07."""
    initial = {"habits": [], "metadata": {"created_at": now_iso()}}
    _atomic_write(_user_path(user_id), initial)
```

**Garantía**: Ninguna función pública expone `user_id` como parámetro de entrada salvo `user_exists()` y `create_user_file()`, que **solo se llaman desde `auth/routes.py` durante el callback OAuth** (antes de crear la sesión). Una vez creada la sesión, `load()/save()` usan exclusivamente `session["user_id"]`.

---

## 4. Diseño del Lock de Concurrencia (RF-09)

**Mecanismo elegido**: `threading.Lock` global en `app/storage/lock.py`

```python
# app/storage/lock.py
import threading
_lock = threading.Lock()

class RegistrationLock:
    def __enter__(self):
        _lock.acquire()
    def __exit__(self, *args):
        _lock.release()
```

**Uso en `auth/routes.py` (callback)**:
```python
with RegistrationLock():
    if storage.user_exists(user_id):
        # Usuario existente -> login normal (RF-05, RF-06)
    elif storage.count_users() < 5:
        storage.create_user_file(user_id)  # RF-07
    else:
        return render_403_limit()  # RF-08
```

**Por qué `threading.Lock` y no `filelock` o archivo `.lock`**:
- **Constitución §1**: Stack mínimo, sin dependencias extra. `filelock` no está en dependencias permitidas.
- **Nota de implementación (spec)**: Despliegue con **un solo worker gunicorn** → un solo proceso Python → `threading.Lock` serializa correctamente todos los hilos.
- **Simplicidad**: 10 líneas, sin I/O, sin riesgo de stale locks si el proceso muere (el lock muere con él).
- **Alternativa descartada**: `filelock` (dependencia externa) o `fcntl`/`flock` (no portable Windows, más complejo).

**Cubre**: RF-09, Constitución §1, §6, nota de implementación.

---

## 5. Flujo OAuth Paso a Paso

| Paso | Ruta | Módulo | Acción |
|------|------|--------|--------|
| 1 | `GET /login` | `web/routes.py` → `auth/routes.py` | Render `login.html` con botón "Iniciar sesión con Google" (RF-01, RF-02) |
| 2 | Click botón | Navegador | `GoogleProvider.get_login_url()` genera un `state` aleatorio, lo guarda en `session` ANTES de redirigir, y redirige a Google incluyendo el `state` en la URL de autorización |
| 3 | Google OAuth | Google | Usuario consiente, Google redirect a `/auth/callback?code=...&state=...` |
| 4 | `GET /auth/callback` | `auth/routes.py` + `auth/google.py` | **VALIDACIÓN STATE (login CSRF, RFC 6749)**: el sistema compara el `state` recibido en el query string con el guardado en sesión; debe coincidir EXACTAMENTE antes de continuar. Si no coincide → mismo flujo que RF-04: redirect a `/login?error=auth_failed` (sin intercambiar código) |
| 5 | `GET /auth/callback` | `auth/routes.py` + `auth/google.py` | `GoogleProvider.verify_token(code)` → intercambia código por tokens, valida ID token (`aud`, `iss`, `exp`) (RF-03, Constitución §9) |
| 6a | Token inválido | `auth/routes.py` | Redirect `/login?error=auth_failed` (RF-04) |
| 6b | Token válido + user_exists | `auth/routes.py` + `storage` | `login_user(user_id)`, redirect `/dashboard` (RF-05, RF-06) |
| 6c | Token válido + !user_exists + count < 5 | `auth/routes.py` + `storage` + `lock` | `RegistrationLock()` → `create_user_file()` → `login_user()` → redirect `/dashboard` (RF-07, RF-09) |
| 6d | Token válido + !user_exists + count == 5 | `auth/routes.py` | Render `403_limit.html` con HTTP 403 (RF-08) |
| 7 | `GET /dashboard` | `web/routes.py` | `@login_required` → `storage.load()` → render `dashboard.html` (RF-11, RF-12) |
| 8 | `POST /logout` | `auth/routes.py` | `logout_user()` (borra sesión), redirect `/login` (RF-10, RNF-05) |

---

## 6. Contrato de Rutas

| Método | Path | Protegida | Códigos Respuesta | Descripción |
|--------|------|-----------|-------------------|-------------|
| GET | `/login` | No | 200, 429 (rate limit) | Página login + mensajes error (RF-01, RNF-01) |
| GET | `/auth/callback` | No | 302 (login ok → `/dashboard`; error/state inválido → `/login`), 403 (límite), 429 (rate limit) | Callback OAuth (RF-02 a RF-08, RNF-01). Ningún paso del flujo devuelve 200: todos los desenlaces son redirect (302) o 403 (límite alcanzado) |
| POST | `/logout` | Sí | 302 → `/login`, 400 (CSRF inválido), 401 (no autenticado) | Logout con CSRF (RF-10, RNF-05) |
| GET | `/dashboard` | Sí | 200, 302 → `/login` (RF-01), 500 (error storage) | Dashboard usuario (RF-11, RF-12) |
| GET | `/static/*` | No | 200, 404 | Assets estáticos (RF-01) |

**Protección**: `@login_required` en `/dashboard` y `/logout` (via `auth/session.py`). `/auth/callback` es pública pero valida `state` (login CSRF) y token Google.

---

## 7. Decisiones Técnicas

| Decisión | Alternativa Descartada | Justificación |
|----------|------------------------|---------------|
| **OAuth `state` (login CSRF)** | Confiar solo en el `code` de Google | Previene login CSRF (RFC 6749 / OAuth 2.0 Security Best Practices): un atacante no puede forzar el login de la víctima en la cuenta del atacante manipulando el callback |
| **Lock: `threading.Lock`** | `filelock`, `fcntl`, archivo `.lock` manual | Stack mínimo (Constitución §1); 1 worker gunicorn → un proceso → lock en memoria suficiente y simple. |
| **`last_activity` en cookie firmada** | En JSON de usuario (`metadata.last_activity`) | Nota de implementación: evita I/O en cada request; cookie firmada es tamper-proof (secret `FLASK_SECRET_KEY`). |
| **Backup corrupto: `.corrupt.{timestamp}`** | Sobreescribir `.corrupt` fijo | Timestamp evita perder backups previos; permite auditoría. |
| **Rate limit: contador independiente por ruta** | Contador global por IP | Especificación RNF-01 y nota de implementación; evita que intentos en `/login` bloqueen `/auth/callback` y viceversa. |
| **1 worker gunicorn** | Múltiples workers | Nota de implementación: simplifica rate-limit (memoria compartida) y lock (threading.Lock). 5 usuarios → 1 worker sobra. |
| **AuthProvider inyectado en `create_app()`** | Singleton global / import directo | Constitución §7: desacoplamiento para tests (mock) y futuro cambio de proveedor. |
| **`storage.load/save` sin `user_id` param** | `load(user_id)`, `save(user_id, data)` | RF-13 / Constitución §9: elimina toda vía para operar sobre user_id ajeno. |
| **Logout via POST + CSRF** | GET `/logout` | RNF-05 + RF-10: logout es acción de estado → POST. |
| **HTTP 403 directo en callback (no redirect)** | 302 → `/login?error=limit` con 403 allí | Constitución §6: "se rechaza el registro con HTTP 403". 403 en callback es semánticamente correcto. |

---

## 8. Estrategia de Tests

### Módulos a testear y cobertura objetivo (≥80%)

| Módulo | Tests Unitarios | Tests Integración | Mocks |
|--------|----------------|-------------------|-------|
| `auth/google.py` | `verify_token()`: token válido, inválido (aud, iss, exp), error red; `validate_state()`: coincide, no coincide, `state` ausente | — | `google.oauth2.id_token.verify_oauth2_token`, `google.auth.transport.requests.Request`, `flask.session` |
| `auth/session.py` | `login_user`, `logout_user`, `current_user_id`, `login_required` decorator | — | `flask.session` |
| `auth/routes.py` | — | Callback: usuario existente, nuevo <5, nuevo =5, token inválido, error red, `state` inválido/ausente | `AuthProvider` (mock), `storage` (mock) |
| `storage/fileops.py` | `_read_with_corrupt_handling`: existe, no existe, corrupto; `_atomic_write`: ok, fallo permiso, retry | — | `open`, `os.rename`, `json.load`, `json.dump` |
| `storage/lock.py` | `RegistrationLock` serializa hilos (test con `threading.Thread`) | — | — |
| `storage/__init__.py` | `load`, `save`, `user_exists`, `count_users`, `create_user_file` | — | `session` (mock), `fileops` (mock) |
| `web/routes.py` | — | Dashboard: con datos, vacío, corrupto; acceso sin sesión | `storage.load` (mock), `session` (mock) |

### Test de Aislamiento de Datos (RF-13)
```python
def test_storage_rejects_external_user_id():
    with app.test_request_context():
        session["user_id"] = "user_A"
        storage.save({"habits": []})  # OK
        # No existe forma de llamar storage.save(user_id="user_B", ...)
        # La API no lo permite por diseño (sin parámetro user_id)
```

### Test de Condición de Carrera (RF-09) — Sin Concurrencia Real
```python
def test_registration_lock_serializes(monkeypatch):
    # Simular 2 hilos intentando registrar al 6º usuario cuando hay 5
    # Mock: count_users() retorna 5 en primera llamada, pero create_user_file()
    # verifica otra vez bajo lock
    lock = RegistrationLock()
    calls = []
    def mock_count():
        calls.append("count")
        return 5
    def mock_create(uid):
        calls.append(f"create_{uid}")
    with lock:
        # Hilo 1: ve 5, no crea
    with lock:
        # Hilo 2: ve 5, no crea
    assert "create_" not in "".join(calls)  # Nadie creó
```
**Truco**: El lock se testea unitariamente verificando que `RegistrationLock` es reentrante y mutuamente exclusivo. La lógica de "verificar + crear" atómica se testea mockeando `count_users` y `create_user_file` y verificando el orden de llamadas bajo `with lock:`.

### Test de `state` (login CSRF)
```python
def test_callback_rejects_mismatched_state(client):
    # GET /auth/callback?code=...&state=incorrecto (session tiene state distinto)
    # → redirect /login?error=auth_failed, sin llamar a verify_token()
def test_callback_accepts_matching_state(client):
    # state en query == state en session → continúa el flujo
def test_callback_rejects_missing_state(client):
    # sin parámetro state → redirect /login?error=auth_failed
```

### Test de Rate Limiting (RNF-01)
- Mock `flask_limiter` o test real con `test_client` haciendo 6 requests seguidos → 429 en la 6ª.

### Test de Cabeceras Seguridad (RNF-02)
- Verificar `response.headers` en cualquier ruta.

---

## Resumen de Cobertura RF

| RF | Sección Plan |
|----|--------------|
| RF-01 | 1 (web/routes), 5 (paso 1), 6 (tabla) |
| RF-02 | 1 (auth/routes, google), 5 (paso 1-2) |
| RF-03 | 1 (auth/google), 5 (paso 5) |
| RF-04 | 1 (auth/routes), 5 (pasos 4, 6a) |
| RF-05 | 1 (auth/routes, storage), 5 (paso 6b) |
| RF-06 | 1 (auth/routes), 5 (paso 6b) |
| RF-07 | 1 (storage, auth/routes), 5 (paso 6c) |
| RF-08 | 1 (auth/routes, templates), 5 (paso 6d), 6 |
| RF-09 | 1 (storage/lock), 4, 5 (paso 6c) |
| RF-10 | 1 (auth/routes, session), 5 (paso 8), 6 |
| RF-11 | 1 (web/routes, storage), 5 (paso 7) |
| RF-12 | 1 (storage/fileops, web/routes), 5 (paso 7) |
| RF-13 | 1 (storage/__init__), 3, 8 |
| RNF-01 | 1 (app/__init__, auth/routes), 6, 8 |
| RNF-02 | 1 (app/__init__, templates), 7 |
| RNF-03 | 1 (app/__init__, auth/google), 7 |
| RNF-04 | 1 (session, web/routes), 5 (pasos 7-8), 7 |
| RNF-05 | 1 (app/__init__, templates), 6, 7 |
| Login CSRF (state) | 1 (auth/google), 5 (pasos 2, 4), 7, 8 |

---

**Listo para implementación**. Todas las dudas resueltas (spec Dudas abiertas). Próximo paso: escribir código siguiendo este plan y ejecutar `pytest` al finalizar.
