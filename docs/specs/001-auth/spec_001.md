# Spec 001 — Autenticación Google y Aislamiento de Datos

## Contexto y objetivo
Permitir que un usuario acceda a GC Habits mediante Google OAuth, creando automáticamente su archivo JSON personal si es su primera vez (respetando el límite de 5 usuarios totales), y garantizando que cada usuario solo vea y modifique sus propios datos.

## Usuarios/actores
- **Usuario no autenticado**: Persona que llega a la app sin sesión activa.
- **Usuario autenticado**: Persona con sesión válida (cookie persistente) que tiene archivo JSON en `/data/users/{user_id}.json`.
- **Sistema**: Backend Flask que gestiona OAuth, sesiones, almacenamiento y límites.

## Historias de usuario
1. **HU-01**: Como usuario no autenticado, quiero entrar a la app y ver un botón "Iniciar sesión con Google" para acceder a mi espacio personal.
2. **HU-02**: Como usuario nuevo (primer login), quiero que se cree mi archivo JSON automáticamente si hay cupo (< 5 usuarios) y llegar al dashboard vacío con invitación a crear mi primer hábito.
3. **HU-03**: Como usuario recurrente, quiero entrar directamente a mi dashboard con mis hábitos y rachas tras hacer login.
4. **HU-04**: Como usuario autenticado, quiero cerrar sesión desde el dashboard y volver a la página de login.
5. **HU-05**: Como usuario que intenta registrarse cuando ya hay 5 usuarios, quiero ver un mensaje claro en el login indicando que se alcanzó el límite y poder reintentar más tarde.
6. **HU-06**: Como usuario cuyos datos JSON se corrompieron, quiero ver mi dashboard vacío con un mensaje informativo de que se reiniciaron mis datos, sin perder la sesión.

## Requisitos funcionales (EARS)

**RF-01** CUANDO un usuario no autenticado accede a una ruta protegida ENTONCES el sistema REDIRIGE a `/login` (sin parámetro `next`). Rutas protegidas: `/dashboard`, `/logout`. Rutas públicas: `/login`, `/auth/callback`, `/static/*`.

**RF-02** CUANDO un usuario pulsa "Iniciar sesión con Google" EN `/login` ENTONCES el sistema INICIA el flujo OAuth redirigiendo a Google.

**RF-03** CUANDO Google redirige a `/auth/callback` con un código de autorización, EL SISTEMA INTERCAMBIA el código por tokens con Google, OBTIENE el ID token, y LO VERIFICA validando `aud`, `iss` y `exp` (Constitución §9).

**RF-04** SI la validación del token FALLA ENTONCES el sistema REDIRIGE a `/login` con mensaje de error genérico.

**RF-05** CUANDO el token es válido Y el `sub` (user_id) YA TIENE archivo en `/data/users/{user_id}.json` ENTONCES el sistema CREA sesión persistente (cookie `HttpOnly; Secure; SameSite=Lax`) y REDIRIGE a `/dashboard`.

**RF-06** CUANDO el token es válido Y el `sub` YA TIENE archivo, ENTONCES el sistema CREA sesión y redirige a `/dashboard`, SIN IMPORTAR el total de usuarios registrados (el límite nunca aplica a usuarios existentes).

**RF-07** CUANDO el token es válido Y el `sub` NO TIENE archivo Y el total de archivos en `/data/users/` ES MENOR QUE 5 ENTONCES el sistema CREA archivo JSON vacío (`{ "habits": [], "metadata": {} }`), CREA sesión persistente y REDIRIGE a `/dashboard`. Los reintentos de escritura en caso de fallo siguen la política de Constitución §5 (3 reintentos con backoff) sin excepción.

**RF-08** SI el token es válido Y el `sub` NO TIENE archivo Y el total de archivos ES IGUAL A 5, ENTONCES el sistema RESPONDE directamente con HTTP 403 en `/auth/callback` (sin redirect), mostrando una página con el mensaje "Límite de usuarios alcanzado." y un enlace de vuelta a `/login`.

**RF-09** El sistema APLICA un bloqueo (lock) durante la verificación de cupo y la creación del archivo de usuario nuevo, garantizando que el conteo de usuarios registrados nunca exceda 5 incluso con registros concurrentes.

**RF-10** CUANDO un usuario autenticado accede a `/logout` ENTONCES el sistema DESTRUYE la sesión y REDIRIGE a `/login`. El logout se ejecuta mediante un formulario POST con token CSRF válido (RNF-05), no mediante enlace GET.

**RF-11** CUANDO un usuario autenticado accede a `/dashboard` ENTONCES el sistema CARGA su archivo JSON (`storage.load()`) y RENDERIZA la plantilla con sus hábitos/rachas (o estado vacío si no tiene ninguno).

**RF-12** SI `storage.load()` detecta JSON corrupto ENTONCES el sistema LOGGEA el error, RENOMBRA el archivo a `.corrupt.{timestamp}`, DEVUELVE estructura vacía, y el dashboard MUESTRA mensaje: "Detectamos un problema con tus datos guardados y los reiniciamos." Los reintentos de escritura en caso de fallo siguen la política de Constitución §5 (3 reintentos con backoff) sin excepción.

**RF-13** Las funciones de storage (load/save) NO reciben user_id como parámetro proveniente de una fuente externa a la sesión; obtienen el user_id únicamente de la sesión verificada del servidor. No existe ninguna vía en el sistema para operar sobre el archivo de un user_id distinto al autenticado.

## Requisitos no funcionales
- **RNF-01**: Rate limiting en `/login` y `/auth/callback`: máx. 5 intentos / 15 min por IP (Constitución §9).
- **RNF-02**: Cabeceras de seguridad en todas las respuestas: CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` (Constitución §9).
- **RNF-03**: Secretos (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FLASK_SECRET_KEY`) solo en variables de entorno / `.env` (nunca en código ni repo).
- **RNF-04**: La sesión persiste entre cierres de navegador y expira automáticamente tras 15 días de inactividad (sin actividad del usuario), además de poder cerrarse manualmente vía logout (RF-10).
- **RNF-05**: CSRF protection habilitado globalmente (Flask-WTF) aunque login sea vía OAuth (formularios POST posteriores lo requieren).

## Casos límite
| Caso | Comportamiento esperado |
|------|------------------------|
| Usuario nuevo, cupo disponible | Crear JSON, sesión, redirect dashboard vacío + invitación |
| Usuario nuevo, cupo lleno (5) | HTTP 403 en callback, mensaje en página de callback con enlace a `/login`, sin sesión |
| Usuario recurrente | Sesión, redirect dashboard con datos |
| JSON corrupto en login recurrente | Backup `.corrupt.{timestamp}`, dashboard vacío + mensaje informativo |
| Intento de acceso a `/dashboard` sin sesión | Redirect a `/login` simple |
| Logout | Destruir sesión via POST + CSRF, redirect `/login` |
| Token Google con `aud`/`iss`/`exp` inválidos | Rechazar, redirect `/login` con error genérico |
| Manipulación de `user_id` en request | Imposible: storage no acepta user_id externo, solo sesión verificada |
| Registros concurrentes al límite | Lock serializa verificación+creación, máximo 5 usuarios garantizado |

## Fuera de alcance (MVP)
- Whitelist de emails o roles de administrador.
- Recuperación de contraseña / 2FA / métodos auth alternativos.
- Eliminación de cuenta / GDPR / exportación de datos.
- Renovación automática de token de acceso Google (solo ID token para sesión).
- Frontend separado en Vercel (MVP: Jinja2 servido por Flask).
- Tests de carga / stress / seguridad avanzada.
- Internacionalización (solo español).
- Validación del campo hd (hosted domain) del token de Google — se acepta cualquier cuenta Google sin restricción de dominio corporativo.
- Recuperación ante fallo de intercambio de token con Google más allá de mostrar error genérico y permitir reintentar login.

## Criterios de finalización
- [ ] Flujo completo: `/login` → Google OAuth → callback → sesión → `/dashboard` funciona para usuario nuevo y recurrente.
- [ ] Límite de 5 usuarios se respeta: 6º usuario recibe 403 en callback con mensaje y enlace a `/login`.
- [ ] Logout desde dashboard via form POST + CSRF destruye sesión y vuelve a `/login`.
- [ ] Acceso directo a `/dashboard` sin sesión redirige a `/login`.
- [ ] JSON corrupto se detecta, backupea con timestamp y muestra mensaje informativo (no estado vacío silencioso).
- [ ] Rate limiting activo en `/login` y `/auth/callback` con contador independiente por ruta.
- [ ] Cabeceras de seguridad presentes en todas las respuestas.
- [ ] Aislamiento verificado: tests confirman que storage no acepta user_id externo, solo sesión verificada.
- [ ] Tests unitarios `auth/` (mock Google) y `storage/` (corrupto, faltante, aislamiento, lock concurrencia) pasan con ≥80% cobertura.
- [x] `pytest` pasa en local y CI (pipeline: `.github/workflows/tests.yml`, push y pull_request en cualquier rama, con verificación de cobertura ≥80% en `app/storage/`).

## Notas de implementación para el plan técnico
- Expiración de sesión vía `last_activity` en la cookie firmada (no en el JSON de usuario).
- Backup de corrupción con sufijo de timestamp (`.corrupt.{timestamp}`).
- Rate limiting con contador independiente por ruta.
- Despliegue con un solo worker gunicorn para evitar inconsistencias de rate-limit y para simplificar el lock de concurrencia (RF-09).

## Dudas abiertas
- Ninguna pendiente (resueltas en la entrevista inicial y en la revisión QA de seguridad).