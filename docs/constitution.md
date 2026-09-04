# GC Habits — Constitución del Proyecto

## 1. Simplicidad del Stack
- **Backend**: Flask + Python stdlib. Sin BD externa, sin ORM.
- **Persistencia**: Un archivo JSON por usuario en disco persistente (Render).
- **Frontend**: Plantillas Jinja2 + CSS/JS vanilla (sin frameworks JS pesados).
- **Dependencias**: Mínimas, solo `flask`, `google-auth`, `python-dotenv`, `flask-wtf`, `flask-limiter`, `flask-talisman`.

## 2. Spec vs Código
- **La especificación (este documento + specs en `docs/specs/`) manda**.
- Si el código contradice la spec, el código es incorrecto y debe corregirse.
- Cambios a la spec requieren PR con aprobación explícita.

## 3. Separación de Responsabilidades
| Capa | Responsabilidad | Ubicación |
|------|-----------------|-----------|
| `auth/` | Google OAuth, sesión, decoradores `@login_required` | `app/auth/` |
| `habits/` | Lógica pura de hábitos/rachas (sin I/O, sin Flask) | `app/habits/` |
| `storage/` | Lectura/escritura JSON, manejo de errores de archivo | `app/storage/` |
| `web/` | Rutas Flask, plantillas, serialización HTTP | `app/web/` |

**Regla**: `habits/` no importa nada de `auth/`, `web/`, ni `flask`.

## 4. Política de Tests
- **Unitarios obligatorios** para `habits/` (lógica pura) y `storage/` (edge cases: archivo corrupto, faltante, permisos).
- **Integración ligeros** para `auth/` (mock Google) y rutas críticas de `web/`.
- **Cobertura mínima**: 80% en `habits/` y `storage/`.
- Ejecución: `pytest` en CI y local antes de push.

## 5. Persistencia de Datos
- **Ubicación**: `/data/users/{user_id}.json` (disco persistente Render).
- **Estructura**: `{ "habits": [...], "metadata": {...} }`
- **Manejo de errores**:
  - Archivo no existe → crear estructura vacía.
  - JSON corrupto → log error, backup `.corrupt`, devolver estructura vacía.
  - Error de escritura → reintento 3x con backoff, luego excepción.
- **Atomicidad**: Escribir a `.tmp` + `os.rename()`.

## 6. Límite de Usuarios (Máx. 5)
- No hay whitelist de emails ni rol de "administrador" en este MVP.
- Cualquier cuenta de Google puede intentar login.
- Si el usuario ya tiene un archivo JSON existente (ya registrado), entra normalmente sin contar contra el límite.
- Si es un usuario nuevo (primer login) y ya existen 5 archivos de usuario en `/data/users/`, se rechaza el registro con **HTTP 403** y el mensaje: `"Límite de usuarios alcanzado."`.
- Es decir: el límite aplica a **"primeros 5 en registrarse"**, por orden de llegada, sin preferencia ni whitelist.

## 7. Autenticación Desacoplada
- **Interfaz `AuthProvider`** en `app/auth/provider.py` con métodos: `get_login_url()`, `verify_token()`, `get_user_info()`.
- **Implementación Google** en `app/auth/google.py`.
- **Inyección de dependencias**: `create_app(auth_provider=GoogleProvider())`.
- **Sesión**: Flask `session` con `user_id` (opaco, no token de Google).
- Futuro cambio de proveedor = nueva clase que implemente `AuthProvider`.

## 8. Despliegue
- **Backend (Render)**: Web Service + Persistent Disk montado en `/data`.
  - `buildCommand`: `pip install -r requirements.txt`
  - `startCommand`: `gunicorn app:create_app`
- **Frontend (si separado en Vercel)**:
  - Comunicación: REST API (JSON) + CORS configurado para dominio Vercel.
  - Auth: Cookies `HttpOnly; Secure; SameSite=Lax` (backend setea, frontend no toca tokens).
  - **No** compartir dominio → `SESSION_COOKIE_DOMAIN` configurable.

## 9. Seguridad

| Principio | Detalle Verificable |
|-----------|---------------------|
| **Secretos** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FLASK_SECRET_KEY` viven en `.env` (nunca commiteado). `.gitignore` incluye `.env*`. En Render: variables de entorno del servicio. |
| **Validación token Google** | Verificar obligatoriamente: `aud` == `GOOGLE_CLIENT_ID`, `iss` ∈ `{"accounts.google.com", "https://accounts.google.com"}`, `exp` > `now()`. Rechazar si falta alguno. |
| **Aislamiento de datos** | **Regla estricta**: ninguna ruta (`web/`) puede leer/escribir `users/{user_id}.json` donde `user_id ≠ session["user_id"]`. Validar en `storage.load(user_id)` y `storage.save(user_id, data)` que coincida con la sesión activa. |
| **Sanitización de inputs** | Nombre de hábito: máx. 100 chars, solo Unicode letras/números/espacios/`_-.` (regex `^[\p{L}\p{N} _\-.]{1,100}$`). Rechazar si no cumple. Escape HTML al renderizar en plantillas (Jinja2 `autoescape=true` por defecto). |
| **CSRF** | Flask-WTF (`CSRFProtect`) habilitado globalmente. Todos los formularios POST (crear/marcar/borrar hábito) requieren token CSRF válido. |
| **Rate limiting login** | Límite: 5 intentos/15 min por IP en `/auth/login` y `/auth/callback`. Implementar con `flask-limiter` (storage en memoria, suficiente para 5 usuarios). |
| **Cabeceras HTTP** | Middleware `Talisman` o `after_request` que añada: `Content-Security-Policy: default-src 'self'; script-src 'self'`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. |