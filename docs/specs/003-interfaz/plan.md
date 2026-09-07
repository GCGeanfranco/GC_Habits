# Plan Técnico — Spec 003: Interfaz Visual

---

## 1. Estructura de Archivos

### `app/static/` (nuevo — **no** `app/web/static/`)
`Flask(__name__)` se instancia dentro de `app/__init__.py`, así que `app.root_path` es el paquete `app/` y la carpeta estática por defecto ya es `app/static/`, servida en `/static/...` sin ninguna configuración adicional de Blueprint. Poner los estáticos dentro de `app/web/static/` no los serviría sin registrar un `static_folder` propio en el Blueprint — innecesario cuando el mecanismo por defecto de Flask ya resuelve esto.

| Archivo | Responsabilidad |
|---------|------------------|
| `css/style.css` | Variables CSS (paleta, tipografía), layout base, componentes (tarjeta de hábito, salvavidas, botón, mensajes flash, formulario), media query responsive. Cubre RF-01, RF-11 (contador), RF-12, RF-14. |
| `js/habits.js` | Feedback instantáneo del botón "Marcar como hecho" (RF-08, RF-09, RF-10) y contador de palabras en vivo (RF-11). Un único archivo, cargado con `<script src="..." defer>` en `base.html` — sin bundler, sin build step (RNF). |
| `img/logo_gc_habits_transparent.png` | El logo vive actualmente en la **raíz del repo**, fuera del paquete `app/` — Flask no puede servirlo desde ahí. Se copia a esta ruta para que `url_for('static', filename='img/logo_gc_habits_transparent.png')` funcione. |

### `app/web/templates/` (nuevo + modificados)
| Archivo | Cambio | Cubre |
|---------|--------|-------|
| `base.html` | **Nuevo.** Layout compartido: `<head>` con `<link>` a `style.css` y a Google Fonts, header con logo (RF-02b), `block content`, bloque de mensajes flash renderizado una sola vez para toda la app. | RF-01, RF-02, RF-02b, RF-12 |
| `login.html` | Se modifica para `{% extends "base.html" %}` + tarjeta centrada con logo, botón de Google, acentos decorativos. | RF-02b, RF-13 |
| `dashboard.html` | Se modifica para `{% extends "base.html" %}` + tarjetas de hábito con salvavidas, badge de récord, formulario de alta con contador, botón con `data-*` para JS. | RF-03 a RF-11 |
| `403_limit.html` | Se modifica para `{% extends "base.html" %}`, sin cambio de contenido (solo hereda header/logo/paleta). | Alcance visual §"Páginas Spec 001" |

**Nota de arquitectura**: crear `base.html` en vez de duplicar `<head>`/header/CSS/JS en cada plantilla es la única forma de que el punto de la clarificación ("las páginas de Spec 001 heredan el CSS obligatoriamente") se cumpla sin copiar y pegar HTML tres veces.

### `app/web/routes.py` (modificado, sin rutas nuevas)
Cambio puntual en `mark_habit_done` para detectar un nuevo récord y comunicarlo a la plantilla (ver §3.1). Ninguna otra ruta cambia de firma.

### `app/habits/` — **sin cambios**
Esta spec es puramente de presentación. No se toca `validation.py`, `streak.py` ni `management.py`. `mark_done()` ya devuelve el hábito actualizado con `record_streak`; la detección de "nuevo récord" se hace comparando el `record_streak` *antes* y *después* de la llamada, en la capa web — no requiere que la función pura de racha sepa nada sobre insignias visuales (Constitución §3: `habits/` no conoce a Flask ni a la interfaz).

---

## 2. Modelo de Datos

**Sin cambios al modelo persistido** (`data["habits"]` sigue igual que en la Spec 002). Esta spec no añade ni modifica ningún campo en el JSON por usuario.

Lo único "nuevo" es efímero y vive en la sesión de Flask (no se persiste en disco): una categoría de flash adicional, `"new_record"`, que transporta el `id` del hábito que acaba de batir su récord. Ver §3.1.

---

## 3. Diseño Técnico

### 3.1 Insignia "Nuevo récord" — resuelve la Duda abierta de RF-06

**Decisión**: reutilizar el mecanismo de `flash()` que ya existe en `routes.py` (categorías `"success"`, `"error"`, `"info"`), añadiendo una categoría `"new_record"` cuyo mensaje es el `id` del hábito.

```python
# app/web/routes.py — dentro de mark_habit_done(), después de calcular `updated`
old_record = habit["record_streak"]
if not already_done and updated["current_streak"] > 0 and updated["current_streak"] >= old_record:
    flash(updated["id"], "new_record")
```

```jinja2
{# dashboard.html #}
{% set record_ids = get_flashed_messages(category_filter=["new_record"]) %}
{% for habit in habits %}
  ...
  {% if habit.id in record_ids %}
    <span class="badge badge-record">¡Nuevo récord!</span>
  {% endif %}
{% endfor %}
```

**Por qué esto resuelve exactamente lo pedido**: los mensajes flash de Flask se guardan en `session["_flashes"]` y se **consumen** (se vacían) la primera vez que `get_flashed_messages()` se llama dentro de una request. Como el flujo es `POST /habits/<id>/done` → `redirect` → `GET /dashboard`, la insignia aparece en ese `GET` inmediato y desaparece sola en cualquier `GET /dashboard` posterior (recarga manual, volver a entrar más tarde el mismo día), sin necesitar ningún campo nuevo en el modelo de datos ni lógica adicional de "expiración por fecha".

### 3.2 JS de "Marcar como hecho" (RF-08, RF-09, RF-10)

```javascript
// app/web/static/js/habits.js
document.querySelectorAll(".btn-mark-done").forEach((btn) => {
  btn.addEventListener("click", () => {
    btn.textContent = "Hecho ✓";
    btn.classList.add("is-done");
    btn.disabled = true; // el clic ya inició el envío del formulario; deshabilitar aquí no lo cancela
  });
});
```

- Se ata el listener al **botón**, no al evento `submit` del formulario: el clic ya disparó el envío nativo del navegador antes de que el manejador termine de ejecutarse, así que `disabled = true` solo bloquea clics repetidos (RF-10) sin interferir con el POST en curso (RF-09).
- Sin `preventDefault()` en ningún punto — el formulario sigue su curso normal hacia el servidor.
- Si JS está deshabilitado, el `<button type="submit">` sigue funcionando exactamente igual (RNF de degradación).

### 3.3 Contador de palabras en vivo (RF-11)

```javascript
const nameInput = document.querySelector("#habit-name");
const counter = document.querySelector("#word-counter");
nameInput?.addEventListener("input", () => {
  const words = nameInput.value.trim().split(/\s+/).filter(Boolean).length;
  counter.textContent = `${words} / 8 palabras`;
  counter.classList.toggle("counter-over", words > 8);
});
```

El input lleva además `maxlength="100"` directamente en el HTML (RF-11), como refuerzo visual; la validación real de duplicado/vacío/8 palabras sigue en el servidor (`habits/validation.py`, sin cambios).

### 3.4 Tipografía (resuelve la decisión abierta de RF-02)

**Decisión**: una única familia de Google Fonts, **Poppins** (pesos 600/700), solo para títulos, métricas de racha/récord y el wordmark del logo. El texto general usa la pila de fuentes de sistema (`-apple-system, "Segoe UI", Roboto, sans-serif`) — cero peticiones de red adicionales para el cuerpo del texto.

```html
<!-- base.html <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap" rel="stylesheet">
```

Esto es exactamente lo que justifica el diff de `docs/constitution.md` ya acordado (`style-src fonts.googleapis.com`, `font-src fonts.gstatic.com`) — **pero el diff del documento no basta por sí solo**. La CSP real la aplica en runtime `Talisman(...)` en `app/__init__.py`:

```diff
 Talisman(
     app,
-    content_security_policy={"default-src": "'self'", "script-src": "'self'"},
+    content_security_policy={
+        "default-src": "'self'",
+        "script-src": "'self'",
+        "style-src": ["'self'", "https://fonts.googleapis.com"],
+        "font-src": ["'self'", "https://fonts.gstatic.com"],
+    },
     force_https=is_production,
     ...
 )
```

Este cambio de código es el que efectivamente le permite al navegador cargar la hoja de estilos y las fuentes de Google; el diff de la Constitución documenta la política, este es el que la hace cumplir.

### 3.5 Paleta y variables CSS (RF-01, RF-12)

```css
/* app/web/static/css/style.css */
:root {
  --color-primary: #ff5722;
  --color-primary-dark: #b02f00;
  --color-secondary: #4b41e1;   /* también usado como color de mensajes "información» */
  --color-tertiary: #00a572;    /* éxito */
  --color-error: #ba1a1a;
  --color-bg: #ffffff;
  --color-text: #1a1a1a;
}
```

### 3.6 Breakpoint responsive — resuelve la Duda abierta de RF-14

**Decisión**: un único breakpoint en `640px` (ancho de referencia para móviles pequeños/medianos). Por debajo, las tarjetas de hábito y el formulario pasan de una fila horizontal a apilado vertical de una sola columna.

```css
@media (max-width: 640px) {
  .habit-card { flex-direction: column; }
  .dashboard-grid { grid-template-columns: 1fr; }
}
```

Un único breakpoint (en vez de varios para tablet/móvil) es consistente con el principio de simplicidad de la Constitución y con que esta es una app interna de 5 usuarios como máximo, no un producto público que deba pulirse para todos los tamaños de pantalla.

### 3.7 Nombres de hábito largos en la tarjeta — resuelve la Duda abierta pendiente

**Decisión**: truncar a una sola línea con elipsis CSS, mostrando el nombre completo como tooltip nativo.

```css
.habit-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
```
```jinja2
<span class="habit-name" title="{{ habit.name }}">{{ habit.name }}</span>
```

### 3.8 Acentos de color en el login — resuelve la Duda abierta de RF-13

**Decisión**: sí se incluyen, implementados con CSS puro (`radial-gradient` de baja opacidad sobre pseudo-elementos `::before`/`::after`), sin ningún asset de imagen adicional ni JS.

```css
.login-page::before {
  content: "";
  position: absolute;
  background: radial-gradient(circle, var(--color-primary) 0%, transparent 70%);
  opacity: 0.15;
  /* ... posicionamiento decorativo ... */
}
```

---

## 4. Cambios en `routes.py`

Único cambio funcional (el resto de rutas no se tocan):

```diff
 @bp.route("/habits/<habit_id>/done", methods=["POST"])
 @login_required
 def mark_habit_done(habit_id):
     data = storage.load()
     idx = next(
         (i for i, h in enumerate(data["habits"]) if h["id"] == habit_id),
         None,
     )
     if idx is None:
         abort(404)
     habit = data["habits"][idx]
+    old_record = habit["record_streak"]
     updated, already_done = mark_done(habit, _today_utc())
     data["habits"][idx] = updated
     storage.save(data)
     if already_done:
         flash(f"'{updated['name']}' ya estaba marcado como hecho hoy.", "info")
     else:
+        if updated["current_streak"] > 0 and updated["current_streak"] >= old_record:
+            flash(updated["id"], "new_record")
         flash(
             f"'{updated['name']}' marcado como hecho. Racha: {updated['current_streak']} días.",
             "success",
         )
     return redirect(url_for("web.dashboard"))
```

`dashboard()` no cambia su firma ni su lógica — solo la plantilla que renderiza (`dashboard.html`) empieza a leer `get_flashed_messages(category_filter=["new_record"])` además de las categorías existentes.

---

## 5. Decisiones Técnicas

| Decisión | Alternativa descartada | Justificación |
|----------|------------------------|----------------|
| Insignia de récord vía `flash(habit_id, "new_record")` | Query param en el redirect (`?new_record=<id>`), o un campo nuevo en el modelo (`record_just_broken: bool`) | Reutiliza un mecanismo ya existente y probado (Spec 002), se autolimpia solo en el siguiente `GET` sin lógica de expiración por fecha, y no persiste nada en disco para algo puramente efímero de UI |
| `base.html` compartido con `{% extends %}` | Duplicar `<head>`/header/enlaces CSS-JS en cada plantilla | Es la única forma de garantizar que las 3 páginas (login, dashboard, 403) hereden el mismo CSS/logo sin copiar y pegar, y facilita cambios futuros de identidad visual en un solo lugar |
| JS atado al `click` del botón, sin `preventDefault` | Interceptar el `submit` del formulario con `fetch`/AJAX | RF-09 prohíbe explícitamente reemplazar el POST real por una llamada AJAX; el formulario debe seguir siendo la fuente de verdad |
| Una sola familia de Google Fonts (Poppins, solo títulos/métricas) | Dos familias (una para títulos, otra para cuerpo) | Menos peticiones de red externas, más simple, y ya el cuerpo del texto no necesita personalidad tipográfica extra |
| Un único breakpoint responsive (640px) | Breakpoints múltiples (tablet + móvil) | Simplicidad (Constitución) — app interna de máx. 5 usuarios, no un producto público |
| Truncamiento de nombre largo con elipsis + `title` | Ajuste de línea (`wrap`) a varias líneas dentro de la tarjeta | El wrap multilinea rompe la altura uniforme de las tarjetas en el listado; el elipsis + tooltip nativo no requiere JS ni CSS adicional para mantener alineación |
| Acentos decorativos del login con CSS puro (`radial-gradient`) | Imagen de fondo como asset | Cero peticiones de red adicionales, cero archivos nuevos que gestionar, coherente con "sin frameworks / sin build step" |
| Detección de "nuevo récord" en `routes.py` (capa web), no en `habits/streak.py` | Añadir un campo `is_new_record` calculado dentro de `mark_done()` | Constitución §3: `habits/` es lógica pura sin conocimiento de presentación; si mañana cambia cómo se muestra la insignia (o se elimina), no debe tocarse el motor de racha |

---

## 6. Estrategia de Tests

Esta spec es mayormente visual (CSS/JS de navegador), por lo que **no** se testea con pytest en ese aspecto — se verifica manualmente según los Criterios de finalización de la spec. Lo que sí es testeable y se cubre con pytest:

| Área | Tests clave |
|------|-------------|
| `web/routes.py::mark_habit_done` | Nuevo récord tras primer marcado (`record 0→1`) flashea `"new_record"`; racha que iguala el récord anterior tras un reinicio también flashea; racha que sube pero no alcanza el récord anterior NO flashea; hábito ya marcado hoy (`already_done`) NO flashea aunque numéricamente calzara |
| `web/routes.py::dashboard` (vía plantilla) | La respuesta HTML contiene el badge `"¡Nuevo récord!"` solo inmediatamente después del POST correspondiente, y NO aparece en un `GET /dashboard` posterior dentro de la misma sesión de test |
| Plantillas (`test_client`) | `login.html`, `dashboard.html` y `403_limit.html` heredan de `base.html` (smoke test: presencia del `<link>` a `style.css` y del logo `<img>` en las tres respuestas) |
| `dashboard.html` — formulario de alta | El HTML renderizado contiene `maxlength="100"` en el input de nombre |
| Regresión | Todos los tests de integración de la Spec 002 sobre `web/routes.py` (creación, marcado, límites, 404, CSRF) siguen en verde sin modificarse |

**Cobertura objetivo**: se mantiene el umbral existente de la Constitución/Spec 002, ≥80% en `app/web/routes.py`. No se fija umbral de cobertura para CSS/JS (no aplica a `coverage.py`).

---

## Resumen de Cobertura RF

| RF | Sección del Plan |
|----|--------------------|
| RF-01 | 1 (`style.css`), 3.5 |
| RF-02 | 3.4 |
| RF-02b | 1 (`base.html`) |
| RF-03 | 1 (`dashboard.html`) |
| RF-04 | 1 (`dashboard.html`) — usa `lifelines_unlocked` tal como se decidió en clarificación |
| RF-05 | 1 (`dashboard.html`) — usa `lifelines_unlocked`/`lifelines_available` |
| RF-06 | 3.1, 4 |
| RF-07 | 1 (`dashboard.html`) |
| RF-08 | 3.2 |
| RF-09 | 3.2 |
| RF-10 | 3.2 |
| RF-11 | 3.3, 3.7 (input `maxlength`) |
| RF-12 | 3.5 (paleta de mensajes) |
| RF-13 | 3.8 |
| RF-14 | 3.6 |

---

**Listo para tareas**. Las 4 dudas abiertas de la spec quedaron resueltas en este plan (§3.1, §3.6, §3.7, §3.8). Próximo paso: descomponer este plan en `tasks.md`.