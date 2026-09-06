# Spec 003 — Interfaz Visual

## Contexto y objetivo
Con las Specs 001 y 002 completas, GC Habits funciona de punta a punta pero con una interfaz HTML plana sin estilos. Esta spec da una interfaz visual completa a las pantallas existentes (login y dashboard), inspirada en un mockup de referencia (Stitch/Google), adaptando su lenguaje visual sin adoptar Tailwind (se mantiene CSS vanilla, según la Constitución) y sin incorporar funcionalidad que no existe en el backend (XP, niveles, analytics, comunidad, etc.).

## Usuarios / actores
Los mismos usuarios autenticados de las Specs 001/002.

## Alcance visual
- Página de login (`/login`).
- Dashboard (`/dashboard`): formulario de alta de hábito, listado de hábitos con racha/récord/salvavidas, botón de marcar como hecho, invitación cuando no hay hábitos, mensajes flash.
- Páginas ya existentes de la Spec 001 (incluida la página de error 403 por límite de usuarios) heredan **obligatoriamente** el estilo base (CSS compartido: paleta, tipografía, logo) pero no cambian de contenido en esta spec (403 límite de usuarios, aviso de datos recuperados).

## Historias de usuario
- H1: Como usuario, quiero una interfaz visualmente atractiva y clara para sentirme motivado a usar la app.
- H2: Como usuario, quiero ver de un vistazo el estado de mis salvavidas (disponibles, bloqueados, cuánto falta para desbloquear) sin tener que interpretar números sueltos.
- H3: Como usuario, quiero una respuesta visual inmediata al marcar un hábito como hecho, sin esperar la recarga de la página.
- H4: Como usuario, quiero sentirme reconocido cuando supero mi récord anterior.

## Requisitos funcionales (criterios de aceptación en EARS)

### Identidad visual
- RF-01: EL SISTEMA usa la paleta de colores del mockup de referencia (primario naranja/rojo `#b02f00`/`#ff5722`, secundario morado `#4b41e1`, terciario verde `#006c49`/`#00a572`, error `#ba1a1a`), implementada como variables CSS (`:root { --color-primary: ...; }`) **en una hoja de estilos externa** (archivo `.css` estático), sin `<style>` inline en las plantillas y sin depender de Tailwind ni de ningún framework CSS.
- RF-02: EL SISTEMA usa una tipografía sans-serif para texto general y una más geométrica/bold para títulos y métricas (racha, récord), similar a la del mockup. Se permite usar Google Fonts (cargada vía `<link>` desde `fonts.googleapis.com`/`fonts.gstatic.com`); esto requiere ampliar la CSP de la Constitución (ver `docs/constitution.md`, sección 9). La fuente exacta (Google Fonts vs. fuente de sistema) queda como decisión técnica del plan.
- RF-02b: EL SISTEMA muestra el logo de GC Habits (ícono llama+corazón+escudo con degradado naranja-morado-dorado + wordmark "GC Habits") en el encabezado del dashboard y en la pantalla de login, usando una versión del asset con fondo transparente.

### Dashboard — listado de hábitos
- RF-03: CUANDO se renderiza un hábito en el listado, EL SISTEMA muestra su nombre, racha actual (con icono de fuego/racha) y récord histórico.
- RF-04: SI `lifelines_unlocked` es `false` para el hábito, ENTONCES EL SISTEMA muestra los 2 salvavidas en estado "bloqueado" junto con el progreso hacia el desbloqueo, calculado sobre la racha actual (ej. "8/15 días para desbloquear").
- RF-05: SI `lifelines_unlocked` es `true` para el hábito, ENTONCES EL SISTEMA muestra cada uno de los 2 slots en estado "activo" (disponible) o "usado" (gastado), según `lifelines_available`.
- RF-06: CUANDO el usuario marca un hábito como hecho y esa acción hace que la racha actual iguale o supere el récord histórico previo (siendo la racha resultante mayor a 0), EL SISTEMA muestra la insignia "¡Nuevo récord!" en la respuesta inmediata a esa acción. La insignia NO se muestra en renderizados posteriores del listado (`GET /dashboard`) aunque la racha se mantenga en su máximo histórico. [NECESITA ACLARACIÓN EN PLAN] mecanismo técnico exacto para distinguir "la acción que acaba de ocurrir" de una recarga posterior (flash message, parámetro de redirect, u otro).
- RF-07: MIENTRAS el usuario no tenga hábitos creados, EL SISTEMA muestra un estado vacío con una invitación visual a crear el primero (hereda RF-16 de la Spec 002, ahora con diseño).

### Marcado como hecho
- RF-08: CUANDO el usuario hace clic en "Marcar como hecho", EL SISTEMA (vía JavaScript vanilla) cambia el aspecto del botón de forma inmediata (ej. a un estado "Hecho ✓", visualmente distinto) ANTES de que el formulario complete su envío y la página recargue.
- RF-09: EL SISTEMA envía el formulario normalmente tras el cambio visual (no reemplaza el POST real por una llamada AJAX) — el cambio es solo feedback percibido; la fuente de verdad sigue siendo la respuesta del servidor tras la recarga.
- RF-10: SI el usuario hace clic repetido sobre el botón ya en estado "Hecho" (antes de que la página recargue), ENTONCES EL SISTEMA no reenvía el formulario una segunda vez (deshabilita el botón tras el primer clic).

### Alta de hábito
- RF-11: EL SISTEMA muestra el campo de nombre de hábito con un atributo `maxlength="100"` (refuerzo visual del límite de la Constitución) y un contador visual de palabras (ej. "3 / 8 palabras"), actualizado en vivo mientras el usuario escribe, sin bloquear el envío del formulario (la validación real de duplicados, vacío y máximo de 8 palabras sigue ocurriendo en el servidor, Spec 002 RF-03).

### Mensajes y estados
- RF-12: EL SISTEMA muestra los mensajes flash (éxito, error, información) con un estilo visual diferenciado por categoría: verde (`--color-tertiary`) para éxito, rojo (`--color-error`) para error, morado (`--color-secondary`) para información.
- RF-13: EL SISTEMA muestra la pantalla de login con el mismo lenguaje visual (paleta, tipografía, fondo claro) que el resto de la app, con un diseño propio: tarjeta centrada con el logo, el botón de "Iniciar sesión con Google", y opcionalmente acentos de color difuminados de fondo (mismo recurso decorativo que el banner superior del dashboard, pero sobre fondo claro, no oscuro) — la inclusión final de estos acentos es una decisión técnica del plan, no bloqueante para el criterio de finalización.

### Responsive
- RF-14: EL SISTEMA adapta el layout del dashboard y login a pantallas móviles (apilado vertical de tarjetas/formulario), priorizando el diseño de escritorio como referencia principal. El breakpoint concreto y el ancho mínimo soportado quedan como decisión técnica del plan.

## Requisitos no funcionales
- No se introduce ningún framework CSS/JS nuevo (Tailwind, Bootstrap, React, etc.) — CSS vanilla + JS vanilla, según Constitución.
- El JS de "Marcar como hecho" (RF-08 a RF-10) se implementa en un archivo `.js` estático mediante `addEventListener`, sin atributos inline (`onclick`) ni bloques `<script>` inline en las plantillas, para respetar la CSP `script-src 'self'` de la Constitución sin necesidad de modificarla.
- El JS de "Marcar como hecho" debe degradar con gracia: si JavaScript está deshabilitado en el navegador, el formulario debe seguir funcionando de forma normal (RF-09 ya lo garantiza, ya que el POST real no depende del JS).
- Sin dependencias de build (sin bundlers, sin paso de compilación) — los archivos CSS/JS se sirven como estáticos, consistente con el resto del proyecto.

## Casos límite
- Hábito recién creado (racha 0, récord 0): no debe mostrar la insignia de "Nuevo récord" (RF-06 exige récord > 0).
- Hábito con racha reiniciada a 0 tras agotar salvavidas: vuelve al estado "bloqueado" (`lifelines_unlocked = false`) con progreso "0/15 días para desbloquear".
- Nombre de hábito con exactamente 8 palabras: el contador visual (RF-11) debe mostrarlo en su color normal, no como error (el límite real se valida en servidor, Spec 002 RF-03).
- La página de error 403 (límite de 5 usuarios, Spec 001) hereda el CSS compartido, la paleta y el logo, sin contenido adicional más allá del ya existente.

## Fuera de alcance (explícito — no existen en el backend real, aunque aparecían en el mockup de referencia)
- Sistema de XP, niveles, o cualquier "puntaje" de gamificación no definido en la Spec 002.
- Navegación a "Analytics", "Badges & Rewards", "Community" — no existen esas páginas ni rutas.
- Categorías, horarios o descripciones por hábito (el modelo de datos de la Spec 002 solo tiene nombre).
- Segundo salvavida desbloqueado a los 25 días — en la Spec 002 ambos salvavidas se desbloquean juntos a los 15 días.
- "Refresh rate" de salvavidas a 14 días — la Spec 002 define 30 días.
- Cualquier lógica de "cron a medianoche" — el recálculo es perezoso (al listar o marcar), no programado.
- Heatmap semanal, retos semanales, avatar/nombre/email de Google visibles en el header.
- Cualquier persistencia nueva o cambio al modelo de datos de `habits` — esta spec es puramente visual, no toca `app/habits/` ni la lógica de las rutas ya existentes más allá de lo necesario para pasar datos a la plantilla.
- Protección contra doble envío del formulario por **recarga manual del navegador** (F5) mientras el POST anterior sigue en vuelo — RF-10 solo cubre el doble clic sobre el mismo botón antes de la recarga, no una recarga manual iniciada por el usuario.

## Criterios de finalización
- Login y dashboard renderizan con el nuevo estilo visual en escritorio y en una vista móvil simulada (DevTools), sin regresiones en los tests de integración existentes de `web/routes.py`.
- Los 4 estados de salvavidas (bloqueado con progreso, activo, usado, re-bloqueado) se pueden reproducir manualmente ajustando datos de prueba y se ven visualmente distintos entre sí.
- El botón "Marcar como hecho" cambia de aspecto antes de la recarga real de la página (verificado manualmente, es una interacción de JS en el navegador).
- Ningún test de las Fases 2 a 5 de la Spec 002 se rompe por los cambios de plantilla.

## Dudas abiertas
- [PENDIENTE TÉCNICO — RF-06] Mecanismo exacto para mostrar la insignia "Nuevo récord" solo en la respuesta inmediata a la acción de marcar como hecho, y no en un `GET /dashboard` posterior dentro del mismo día.
- [PENDIENTE TÉCNICO — RF-13] Si finalmente se incluyen los acentos de color difuminados de fondo en el login, o se omiten.
- [PENDIENTE TÉCNICO — RF-14] Breakpoint concreto (ancho en px) para el cambio a layout móvil.
- [PENDIENTE TÉCNICO] Tratamiento visual (truncamiento con ellipsis, wrap a varias líneas, etc.) de nombres de hábito largos dentro de la tarjeta del listado.