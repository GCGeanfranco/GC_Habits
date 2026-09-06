# Spec 003 — Interfaz Visual

## Contexto y objetivo
Con las Specs 001 y 002 completas, GC Habits funciona de punta a punta pero con una interfaz HTML plana sin estilos. Esta spec da una interfaz visual completa a las pantallas existentes (login y dashboard), inspirada en un mockup de referencia (Stitch/Google), adaptando su lenguaje visual sin adoptar Tailwind (se mantiene CSS vanilla, según la Constitución) y sin incorporar funcionalidad que no existe en el backend (XP, niveles, analytics, comunidad, etc.).

## Usuarios / actores
Los mismos usuarios autenticados de las Specs 001/002.

## Alcance visual
- Página de login (`/login`).
- Dashboard (`/dashboard`): formulario de alta de hábito, listado de hábitos con racha/récord/salvavidas, botón de marcar como hecho, invitación cuando no hay hábitos, mensajes flash.
- Páginas ya existentes de la Spec 001 pueden heredar el estilo base (CSS compartido) pero no cambian de contenido en esta spec (403 límite de usuarios, aviso de datos recuperados).

## Historias de usuario
- H1: Como usuario, quiero una interfaz visualmente atractiva y clara para sentirme motivado a usar la app.
- H2: Como usuario, quiero ver de un vistazo el estado de mis salvavidas (disponibles, bloqueados, cuánto falta para desbloquear) sin tener que interpretar números sueltos.
- H3: Como usuario, quiero una respuesta visual inmediata al marcar un hábito como hecho, sin esperar la recarga de la página.
- H4: Como usuario, quiero sentirme reconocido cuando supero mi récord anterior.

## Requisitos funcionales (criterios de aceptación en EARS)

### Identidad visual
- RF-01: EL SISTEMA usa la paleta de colores del mockup de referencia (primario naranja/rojo `#b02f00`/`#ff5722`, secundario morado `#4b41e1`, terciario verde `#006c49`/`#00a572`, error `#ba1a1a`), implementada como variables CSS (`:root { --color-primary: ...; }`), sin depender de Tailwind ni de ningún framework CSS.
- RF-02: EL SISTEMA usa una tipografía sans-serif para texto general y una más geométrica/bold para títulos y métricas (racha, récord), similar a la del mockup — la fuente exacta (Google Fonts vs. fuente de sistema) queda como decisión técnica del plan.
- RF-02b: EL SISTEMA muestra el logo de GC Habits (ícono llama+corazón+escudo con degradado naranja-morado-dorado + wordmark "GC Habits") en el encabezado del dashboard y en la pantalla de login, usando una versión del asset con fondo transparente.

### Dashboard — listado de hábitos
- RF-03: CUANDO se renderiza un hábito en el listado, EL SISTEMA muestra su nombre, racha actual (con icono de fuego/racha) y récord histórico.
- RF-04: SI la racha actual del hábito es menor a 15 días, ENTONCES EL SISTEMA muestra los 2 salvavidas en estado "bloqueado" junto con el progreso hacia el desbloqueo (ej. "8/15 días para desbloquear").
- RF-05: SI el hábito tiene salvavidas desbloqueados, ENTONCES EL SISTEMA muestra cada uno de los 2 slots en estado "activo" (disponible) o "usado" (gastado), según `lifelines_available`.
- RF-06: SI la racha actual del hábito iguala o supera su récord histórico (y es mayor a 0), ENTONCES EL SISTEMA muestra una insignia "¡Nuevo récord!" junto a la racha.
- RF-07: MIENTRAS el usuario no tenga hábitos creados, EL SISTEMA muestra un estado vacío con una invitación visual a crear el primero (hereda RF-16 de la Spec 002, ahora con diseño).

### Marcado como hecho
- RF-08: CUANDO el usuario hace clic en "Marcar como hecho", EL SISTEMA (vía JavaScript vanilla) cambia el aspecto del botón de forma inmediata (ej. a un estado "Hecho ✓", visualmente distinto) ANTES de que el formulario complete su envío y la página recargue.
- RF-09: EL SISTEMA envía el formulario normalmente tras el cambio visual (no reemplaza el POST real por una llamada AJAX) — el cambio es solo feedback percibido; la fuente de verdad sigue siendo la respuesta del servidor tras la recarga.
- RF-10: SI el usuario hace clic repetido sobre el botón ya en estado "Hecho" (antes de que la página recargue), ENTONCES EL SISTEMA no reenvía el formulario una segunda vez (deshabilita el botón tras el primer clic).

### Alta de hábito
- RF-11: EL SISTEMA muestra el campo de nombre de hábito con un contador visual de palabras (ej. "3 / 8 palabras"), actualizado en vivo mientras el usuario escribe, sin bloquear el envío del formulario (la validación real sigue ocurriendo en el servidor, Spec 002 RF-03).

### Mensajes y estados
- RF-12: EL SISTEMA muestra los mensajes flash (éxito, error, información) con un estilo visual diferenciado por categoría (ej. verde para éxito, rojo para error).
- RF-13: EL SISTEMA muestra la pantalla de login con el mismo lenguaje visual (paleta, tipografía, fondo claro) que el resto de la app, con un diseño propio: tarjeta centrada con el logo, el botón de "Iniciar sesión con Google", y opcionalmente acentos de color difuminados de fondo (mismo recurso decorativo que el banner superior del dashboard, pero sobre fondo claro, no oscuro).
- RF-13b: EL SISTEMA muestra el logo de GC Habits (ícono + "GC Habits") en el header del dashboard y en la tarjeta de login, usando el archivo con fondo transparente.

### Responsive
- RF-14: EL SISTEMA adapta el layout del dashboard y login a pantallas móviles (apilado vertical de tarjetas/formulario), priorizando el diseño de escritorio como referencia principal pero sin romperse en móvil.

## Fuera de alcance (explícito — no existen en el backend real, aunque aparecían en el mockup de referencia)
- Sistema de XP, niveles, o cualquier "puntaje" de gamificación no definido en la Spec 002.
- Navegación a "Analytics", "Badges & Rewards", "Community" — no existen esas páginas ni rutas.
- Categorías, horarios o descripciones por hábito (el modelo de datos de la Spec 002 solo tiene nombre).
- Segundo salvavida desbloqueado a los 25 días — en la Spec 002 ambos salvavidas se desbloquean juntos a los 15 días.
- "Refresh rate" de salvavidas a 14 días — la Spec 002 define 30 días.
- Cualquier lógica de "cron a medianoche" — el recálculo es perezoso (al listar o marcar), no programado.
- Heatmap semanal, retos semanales, avatar/nombre/email de Google visibles en el header.
- Cualquier persistencia nueva o cambio al modelo de datos de `habits` — esta spec es puramente visual, no toca `app/habits/` ni la lógica de las rutas ya existentes más allá de lo necesario para pasar datos a la plantilla.

## Requisitos no funcionales
- No se introduce ningún framework CSS/JS nuevo (Tailwind, Bootstrap, React, etc.) — CSS vanilla + JS vanilla, según Constitución.
- El JS de "Marcar como hecho" (RF-08 a RF-10) debe degradar con gracia: si JavaScript está deshabilitado en el navegador, el formulario debe seguir funcionando de forma normal (RF-09 ya lo garantiza, ya que el POST real no depende del JS).
- Sin dependencias de build (sin bundlers, sin paso de compilación) — los archivos CSS/JS se sirven como estáticos, consistente con el resto del proyecto.

## Casos límite
- Hábito recién creado (racha 0, récord 0): no debe mostrar la insignia de "Nuevo récord" (RF-06 exige récord > 0).
- Hábito con racha reiniciada a 0 tras agotar salvavidas: vuelve al estado "bloqueado" con progreso "0/15 días para desbloquear".
- Nombre de hábito con exactamente 8 palabras: el contador visual (RF-11) debe mostrarlo en su color normal, no como error (el límite real se valida en servidor, Spec 002 RF-03).

## Criterios de finalización
- Login y dashboard renderizan con el nuevo estilo visual en escritorio y en una vista móvil simulada (DevTools), sin regresiones en los tests de integración existentes de `web/routes.py`.
- Los 4 estados de salvavidas (bloqueado con progreso, activo, usado, re-bloqueado) se pueden reproducir manualmente ajustando datos de prueba y se ven visualmente distintos entre sí.
- El botón "Marcar como hecho" cambia de aspecto antes de la recarga real de la página (verificado manualmente, es una interacción de JS en el navegador).
- Ningún test de las Fases 2 a 5 de la Spec 002 se rompe por los cambios de plantilla.

## Dudas abiertas
Ninguna — todas las decisiones de esta ronda se cerraron en la entrevista (paleta, progreso de desbloqueo, insignia de récord, feedback JS instantáneo, estilo de login).