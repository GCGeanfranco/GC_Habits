# Tasks — Spec 003: Interfaz Visual

Tareas de 20-30 min en orden de dependencia. TDD donde es verificable con pytest (backend, headers, render de plantillas); las tareas de CSS/JS puro son de implementación, verificadas manualmente según los Criterios de finalización de `spec_003.md`.

---

## Fase 0 — Configuración base (CSP, estáticos, layout compartido)

- [ ] **T0.1** `app/__init__.py`: ampliar el `content_security_policy` de `Talisman` con `style-src: ['self', https://fonts.googleapis.com]` y `font-src: ['self', https://fonts.gstatic.com]`, sin tocar `default-src` ni `script-src`.
  - RF/RNF: RF-02, Constitución §9 (diff ya acordado)
  - Hecho cuando: test de integración sobre cualquier respuesta (ej. `GET /login`) verifica que el header `Content-Security-Policy` contiene `style-src` con `fonts.googleapis.com` y `font-src` con `fonts.gstatic.com`, y que `script-src 'self'` sigue intacto (sin `unsafe-inline`).
  - Tipo: TDD.

- [ ] **T0.2** Copiar `logo_gc_habits_transparent.png` (actualmente en la raíz del repo) a `app/static/img/logo_gc_habits_transparent.png`.
  - RF/RNF: RF-02b
  - Hecho cuando: test de integración hace `GET /static/img/logo_gc_habits_transparent.png` y recibe `200` con `Content-Type: image/png`.
  - Tipo: TDD.

- [ ] **T0.3** Crear `app/static/css/style.css` y `app/static/js/habits.js` (ambos con un comentario placeholder, aún sin contenido real).
  - RF/RNF: RNF (sin build step, estáticos servidos por Flask)
  - Hecho cuando: tests verifican `GET /static/css/style.css` → 200 `text/css`, `GET /static/js/habits.js` → 200 `text/javascript` (o `application/javascript` según versión de Flask/Werkzeug).
  - Tipo: TDD.

- [ ] **T0.4** Crear `app/web/templates/base.html`: `<head>` con `<meta name="viewport">`, `<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">`, `preconnect` + `<link>` a Google Fonts (Poppins 600/700), `<script src="{{ url_for('static', filename='js/habits.js') }}" defer></script>`; `<header>` con el logo (`img` a `img/logo_gc_habits_transparent.png`) y wordmark; una única zona de mensajes flash (`get_flashed_messages(with_categories=true)`, categorías `success`/`error`/`info`); `{% block content %}{% endblock %}`.
  - RF/RNF: RF-01, RF-02, RF-02b, RF-12
  - Hecho cuando: un test con una plantilla hija mínima (`{% extends "base.html" %}{% block content %}OK{% endblock %}`) confirma, vía `test_client`, presencia del `<link rel="stylesheet">` con el `href` correcto, el `<img>` del logo, y el `<script src=...defer>`; ningún `<style>` ni `<script>` inline en el HTML resultante (grep sobre el body de la respuesta).
  - Tipo: TDD.

---

## Fase 1 — CSS (`app/static/css/style.css`)

- [ ] **T1.1** Variables CSS de paleta (`:root { --color-primary: #ff5722; --color-primary-dark: #b02f00; --color-secondary: #4b41e1; --color-tertiary: #00a572; --color-error: #ba1a1a; --color-bg: #ffffff; --color-text: #1a1a1a; }`), reset básico (`box-sizing`, márgenes), tipografía base (`font-family` de sistema para body, Poppins para `h1`/`h2`/clases de métrica).
  - RF/RNF: RF-01, RF-02
  - Hecho cuando: revisión visual manual — el color de fondo, texto y encabezados coincide con la paleta acordada en la spec.
  - Tipo: implementación.

- [ ] **T1.2** Estilos de layout y componentes: header con logo, `.habit-card` (tarjeta de hábito), los 4 estados visuales de salvavidas (bloqueado con progreso, activo, usado, re-bloqueado), `.btn-mark-done` (con estado `.is-done` para el JS de Fase 2), mensajes flash por categoría usando `--color-tertiary` (éxito), `--color-error` (error) y `--color-secondary` (información), `.badge-record` (insignia "¡Nuevo récord!").
  - RF/RNF: RF-03, RF-04, RF-05, RF-06, RF-08, RF-12
  - Hecho cuando: revisión visual manual de cada uno de los 4 estados de salvavidas (forzando datos de prueba) y de los 3 colores de mensaje flash.
  - Tipo: implementación.

- [ ] **T1.3** Responsive (breakpoint único `max-width: 640px`, `.habit-card` a columna, `.dashboard-grid` a una sola columna) y truncamiento de nombre de hábito largo (`.habit-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }` + atributo `title` en la plantilla).
  - RF/RNF: RF-14
  - Hecho cuando: revisión manual en DevTools con viewport móvil (< 640px) sin overflow horizontal ni elementos solapados; un nombre de hábito de 100 caracteres se trunca con elipsis y el `title` muestra el nombre completo al pasar el cursor.
  - Tipo: implementación.

- [ ] **T1.4** Acentos decorativos del login: `.login-page::before`/`::after` con `radial-gradient` de baja opacidad usando `--color-primary`, posicionados detrás de la tarjeta de login.
  - RF/RNF: RF-13
  - Hecho cuando: revisión visual manual — los acentos son sutiles (no comprometen la legibilidad del formulario) sobre fondo claro.
  - Tipo: implementación.

---

## Fase 2 — JS (`app/static/js/habits.js`)

- [ ] **T2.1** Feedback instantáneo del botón "Marcar como hecho": `addEventListener("click", ...)` sobre cada `.btn-mark-done` que cambia el texto a "Hecho ✓", añade la clase `.is-done` y deshabilita el botón — sin `preventDefault()`, el formulario sigue su envío normal.
  - RF/RNF: RF-08, RF-09, RF-10
  - Hecho cuando: prueba manual en navegador — clic cambia el botón visualmente antes de la recarga; clic repetido antes de la recarga no reenvía el formulario; con JS deshabilitado en el navegador, el botón sigue marcando el hábito con normalidad (recarga directa).
  - Tipo: implementación (JS de navegador, no testeable con pytest).

- [ ] **T2.2** Contador de palabras en vivo sobre el input `name` del formulario de alta (`input` event → cuenta palabras con `trim().split(/\s+/)`, actualiza `#word-counter`, clase `.counter-over` si supera 8).
  - RF/RNF: RF-11
  - Hecho cuando: prueba manual — escribir en el campo actualiza el contador en tiempo real; al superar 8 palabras el contador cambia de estilo pero el formulario sigue siendo enviable (la validación real sigue en el servidor).
  - Tipo: implementación.

---

## Fase 3 — `web/routes.py`: detección de "nuevo récord"

**Tarea delicada — único cambio de lógica de negocio de esta spec.**

- [ ] **T3.1** En `mark_habit_done`, capturar `old_record = habit["record_streak"]` antes de llamar a `mark_done()`; tras la llamada, si `not already_done and updated["current_streak"] > 0 and updated["current_streak"] >= old_record`, hacer `flash(updated["id"], "new_record")` antes del flash de éxito existente.
  - RF/RNF: RF-06
  - Hecho cuando: tests cubren los 4 casos: (1) primer marcado de un hábito nuevo (récord 0→1) flashea `new_record` con el `id` correcto; (2) racha que iguala el récord anterior tras un reinicio flashea; (3) racha que sube pero sin alcanzar el récord anterior NO flashea `new_record` (sí el flash de éxito normal); (4) hábito ya marcado hoy (`already_done=True`) NO flashea `new_record` aunque numéricamente calzara. Todos los tests existentes de `test_t4_2_mark_habit_done.py` (Spec 002) siguen en verde.
  - Tipo: TDD. **Tarea delicada.**

---

## Fase 4 — Plantillas: login, dashboard, 403

- [ ] **T4.1** `login.html`: `{% extends "base.html" %}`, tarjeta centrada con logo, mensaje de error si existe, botón "Iniciar sesión con Google", `<body>`/wrapper con clase `login-page` para los acentos CSS de T1.4.
  - RF/RNF: RF-02b, RF-13
  - Hecho cuando: test de integración sobre `GET /login` confirma que la respuesta hereda los elementos de `base.html` (link a `style.css`, logo) y conserva el enlace de login de Google y el mensaje de error cuando corresponde (mismo comportamiento que antes, solo cambia el envoltorio visual).
  - Tipo: TDD.

- [ ] **T4.2** `403_limit.html`: `{% extends "base.html" %}`, sin cambiar el contenido (mensaje de límite + enlace de vuelta al login).
  - RF/RNF: Alcance visual §"Páginas Spec 001"
  - Hecho cuando: test de integración fuerza la condición de 5 usuarios y confirma que la respuesta 403 hereda `base.html` (logo, CSS) y conserva el texto "Límite de usuarios alcanzado." y el enlace a `/login`.
  - Tipo: TDD.

- [ ] **T4.3** `dashboard.html` — salvavidas y badge de récord: `{% extends "base.html" %}`; por cada hábito, renderizar los 2 slots de salvavidas según `lifelines_unlocked`/`lifelines_available` (RF-04, RF-05); mostrar `<span class="badge badge-record">¡Nuevo récord!</span>` cuando `habit.id` esté en `get_flashed_messages(category_filter=["new_record"])`.
  - RF/RNF: RF-04, RF-05, RF-06
  - Hecho cuando: tests de integración cubren: hábito con `lifelines_unlocked=False` muestra progreso "X/15"; hábito con `lifelines_unlocked=True` muestra los 2 slots (activo/usado según `lifelines_available`); tras un `POST /habits/<id>/done` que rompe récord, el `GET /dashboard` de la redirección incluye el badge; un `GET /dashboard` posterior (nueva petición, sin el flash) NO lo incluye.
  - Tipo: TDD. **Tarea delicada** (depende de T3.1).

- [ ] **T4.4** `dashboard.html` — formulario y botón: añadir `<span id="word-counter">` junto al input `name` (ya tiene `maxlength="100"`, no se toca); añadir clase `btn-mark-done` a cada botón "Marcar como hecho"; aplicar `.habit-name` con `title="{{ habit.name }}"` al nombre renderizado.
  - RF/RNF: RF-11 (contador), RF-08 (gancho de clase para JS), RF-14 (truncamiento)
  - Hecho cuando: test de integración confirma la presencia de `id="word-counter"`, la clase `btn-mark-done` en cada botón, y el atributo `title` con el nombre completo del hábito en `.habit-name`.
  - Tipo: TDD.

---

## Fase 5 — Validación final

- [ ] **T5.1** Ejecutar la suite completa y confirmar que no hay regresiones: todos los tests de las Specs 001 y 002 siguen en verde, cobertura de `app/web/routes.py` se mantiene ≥80%.
  - RF/RNF: Criterios de finalización de la spec
  - Hecho cuando: `pytest -v` en verde (salvo los 4 fallos preexistentes ya documentados de `test_t0_3_secrets.py`); `coverage` confirma ≥80% en `app/web/routes.py`.
  - Tipo: validación.

- [ ] **T5.2** Recorrido manual del checklist de "Criterios de finalización" de `spec_003.md`: login y dashboard en escritorio y en vista móvil simulada (DevTools, < 640px); los 4 estados de salvavidas reproducidos con datos de prueba; el botón "Marcar como hecho" cambia de aspecto antes de la recarga real; la insignia de récord aparece una vez y no persiste en una recarga posterior.
  - RF/RNF: todos (RF-01 a RF-14)
  - Hecho cuando: cada criterio de finalización de la spec está confirmado con evidencia (test o nota de verificación manual); ninguna regla de Constitución §3/§9 violada (CSP, sanitización, CSRF intactos).
  - Tipo: validación.

---

### Notas
- Orden de dependencia: F0 → F1/F2 (pueden ir en paralelo entre sí, ambas dependen solo de F0) → F3 → F4 (T4.3 depende de T3.1) → F5.
- T3.1 es la única tarea que toca lógica de negocio/backend real de esta spec — el resto es CSS/JS/plantillas. Tratarla con el mismo rigor TDD que las tareas delicadas de la Spec 002.
- Las tareas de CSS/JS puro (T1.1–T1.4, T2.1–T2.2) no tienen test de pytest asociado por diseño — se verifican en T5.2. No forzar un test artificial sobre ellas.