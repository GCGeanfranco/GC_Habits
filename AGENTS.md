# AGENTS.md — GC Habits

## Proyecto
App web multi-usuario (máx. 5, primeros en registrarse) para registrar
hábitos y ver la racha de días consecutivos. Login con Google OAuth,
backend Flask, persistencia en un archivo JSON por usuario. Desplegada en
Render (backend + disco persistente); frontend puede vivir en Vercel.

## Comandos
- Ejecutar: `flask --app app run` (o `gunicorn app:create_app` en producción)
- Tests: `pytest`
- Lint/formato: (a definir si hace falta, no bloqueante para el MVP)

## Estilo y convenciones
- Python 3.12+
- Dependencias permitidas: `flask`, `google-auth`, `python-dotenv`,
  `flask-wtf`, `flask-limiter`, `flask-talisman`. Ninguna otra sin
  actualizar antes docs/constitution.md.
- Identificadores y código en inglés, mensajes de usuario en español.
- Estructura de carpetas: `app/auth/`, `app/habits/`, `app/storage/`, `app/web/`.

## Reglas
- Lee SIEMPRE docs/constitution.md y la spec activa en docs/specs/ antes de
  tocar código.
- `app/habits/` no puede importar nada de `auth/`, `web/` ni de Flask
  (lógica pura, sin I/O).
- Ninguna ruta puede leer/escribir el JSON de un user_id distinto al de la
  sesión activa (ver Constitución §9).
- No añadir dependencias, base de datos externa, ni cambiar la lógica de
  autenticación sin actualizar primero docs/constitution.md.

## Al terminar cualquier tarea
- Ejecutar `pytest` y confirmar que todos los tests pasan.
- Confirmar que la tarea no viola ninguna regla de docs/constitution.md
  (especialmente aislamiento de datos y sanitización de inputs).
- Marcar la tarea como completada en el tasks.md correspondiente, indicando
  qué RF cubre.