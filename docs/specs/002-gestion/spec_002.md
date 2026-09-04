# Spec 002 — Gestión de hábitos

## Contexto y objetivo
Con la Spec 001 (autenticación Google y aislamiento de datos) completa y validada, cada uno de los hasta 5 usuarios de GC Habits tiene ya un archivo JSON propio, aislado y accesible solo tras login. Esta spec añade la funcionalidad central de la aplicación: crear hábitos, marcarlos como hechos cada día y listarlos junto con su racha de días consecutivos. Se incorpora además una mecánica de "salvavidas" que permite tolerar fallos puntuales en rachas largas sin perder todo el progreso, para reducir el efecto desmotivador de romper una racha por un despiste aislado.

## Usuarios / actores
Los mismos usuarios autenticados de la Spec 001 (máximo 5, "primeros en llegar, primeros en registrarse"). Cada usuario ve y modifica exclusivamente sus propios hábitos, respetando el aislamiento de datos ya implementado en `storage/`.

## Historias de usuario
- H1: Como usuario autenticado, quiero crear un hábito con un nombre único para empezar a hacerle seguimiento.
- H2: Como usuario, quiero marcar un hábito como hecho hoy para registrar mi progreso diario.
- H3: Como usuario, quiero ver el listado de mis hábitos con su racha actual y su récord histórico para mantenerme motivado.
- H4: Como usuario con una racha larga, quiero disponer de salvavidas que me protejan de perder toda la racha si algún día se me olvida completar el hábito.

## Requisitos funcionales (criterios de aceptación en EARS)

### Creación de hábitos
- RF-01: CUANDO el usuario crea un hábito con un nombre que no existe previamente entre sus hábitos, EL SISTEMA lo registra con racha actual 0, récord 0 y 0 salvavidas disponibles.
- RF-02: SI el usuario intenta crear un hábito cuyo nombre normalizado (minúsculas, sin tildes, espacios colapsados en guión bajo) coincide con el de un hábito ya existente, ENTONCES EL SISTEMA rechaza la creación e informa del nombre duplicado.
- RF-03: SI el nombre del hábito está vacío, compuesto solo de espacios, o supera las 8 palabras, ENTONCES EL SISTEMA rechaza la creación e informa del error concreto.

### Marcado como hecho
- RF-04: CUANDO el usuario marca un hábito como hecho en el día actual (UTC) y no lo tenía ya marcado hoy, EL SISTEMA registra el día como completado y recalcula racha y salvavidas.
- RF-05: SI el usuario intenta marcar como hecho un hábito que ya está marcado como hecho hoy (UTC), ENTONCES EL SISTEMA no duplica el registro y lo comunica como ya completado.
- RF-06: SI el usuario intenta marcar un hábito que no existe, ENTONCES EL SISTEMA informa del error sin modificar datos.

### Cálculo de racha
- RF-07: EL SISTEMA evalúa la racha de cada hábito en UTC, procesando cronológicamente cada día transcurrido desde el último marcado hasta hoy, detectando fallos aunque el usuario no haya realizado ninguna acción de marcado en días intermedios.
- RF-08: CUANDO el sistema detecta que un día no fue completado y el hábito dispone de al menos 1 salvavida, EL SISTEMA consume 1 salvavida para ese día, lo marca como "salvado" (no como "hecho") y mantiene la racha actual.
- RF-09: CUANDO el sistema detecta que un día no fue completado y el hábito no dispone de salvavidas, EL SISTEMA reinicia la racha actual a 0 para ese día.
- RF-10: CUANDO el usuario marca un hábito como hecho y el día inmediatamente anterior estaba completado o salvado (o es el primer día del hábito), EL SISTEMA incrementa la racha actual en 1.
- RF-11: EL SISTEMA actualiza el récord (racha máxima histórica) de un hábito cada vez que la racha actual supera al récord almacenado. Los días marcados como "salvado" no contribuyen al récord.

### Salvavidas
- RF-12: CUANDO la racha actual de un hábito alcanza 15 días, EL SISTEMA desbloquea 2 salvavidas disponibles para ese hábito.
- RF-13: SI la racha actual de un hábito se reinicia a 0 (RF-09), ENTONCES EL SISTEMA bloquea de nuevo sus salvavidas a 0 hasta que la nueva racha vuelva a alcanzar 15 días (RF-12).
- RF-14: CUANDO hayan transcurrido 30 días desde el desbloqueo de los salvavidas de un hábito (o desde la última recuperación) sin haber agotado los 2 disponibles, EL SISTEMA recupera 1 salvavida adicional hasta un máximo de 2. Este contador solo aplica mientras los salvavidas estén desbloqueados.

### Listado
- RF-15: CUANDO el usuario solicita el listado de sus hábitos, EL SISTEMA muestra, para cada uno, su nombre, racha actual y récord histórico, con la racha recalculada al momento de la consulta (RF-07).
- RF-16: MIENTRAS el usuario no tenga ningún hábito creado, EL SISTEMA le invita a crear el primero.

### Límite de hábitos
- RF-17: SI el usuario ya tiene 10 hábitos creados y solicita crear uno nuevo, ENTONCES EL SISTEMA rechaza la creación e informa de que ha alcanzado el límite máximo de 10 hábitos.

### Persistencia
- RF-18: EL SISTEMA almacena los hábitos de cada usuario dentro de su archivo JSON existente (creado en la Spec 001), añadiendo una estructura de datos para hábitos sin romper el formato ya validado.

## Requisitos no funcionales
- Debe respetar el aislamiento por usuario ya implementado (`load()`/`save()` sin parámetro `user_id` explícito, obtenido solo de la sesión verificada — Constitución, Spec 001 T1.3).
- El corte de "día" para marcar hábitos como hechos y para detectar fallos se calcula siempre en UTC (hora del servidor Render), independientemente de la zona horaria del usuario.
- Cobertura de tests: 100% en el módulo de cálculo de racha y salvavidas (lógica de negocio pura); ≥80% en el resto del código nuevo de esta spec (vistas, rutas Flask).
- Cualquier corrupción del archivo JSON de un usuario debe manejarse igual que en la Spec 001 (no debe romper la app; ya cubierto por `load_with_status()`).

## Casos límite
- Dos o más días fallados consecutivos o separados: cada uno consume un salvavida independiente (RF-08). Al agotar los 2, el siguiente día fallado reinicia la racha a 0 (RF-09) y bloquea los salvavidas (RF-13).
- El usuario no entra varios días seguidos: el sistema detecta los días fallados al recalcular en la siguiente consulta o marcado (RF-07), consumiendo salvavidas o reiniciando racha según corresponda.
- Racha que llega a 15 el mismo día en que hay días anteriores sin cubrir: RF-07 evalúa cronológicamente, así que los fallos previos se procesan antes del desbloqueo, evitando ambigüedad.
- Uso de salvavida en el día exacto 15 (justo cuando se desbloquean): es posible si ese día se detecta un fallo anterior al procesar RF-07.
- Nombre con mayúsculas, tildes o espacios múltiples que tras normalización coincide con uno existente: rechazado por RF-02.
- Marcado simultáneo del mismo hábito por dos peticiones concurrentes: no aplica en producción (único worker Gunicorn, sin condición de carrera real); no requiere lock adicional en esta spec.

## Fuera de alcance
- Borrar un hábito.
- Marcar días pasados de forma retroactiva.
- Ver historial completo día a día (solo se exponen racha actual y récord, no el detalle histórico).
- Recordatorios.
- Colores o personalización visual de los hábitos.

## Criterios de finalización
- Todos los RF-01 a RF-18 cuentan con al menos un test automatizado en verde.
- La lógica de racha y salvavidas alcanza el 100% de cobertura; el resto del código nuevo de esta spec alcanza ≥80%.
- Demo manual: crear un hábito, marcarlo como hecho varios días seguidos, forzar un fallo con y sin salvavidas disponibles, y verificar que el listado muestra racha y récord correctos.
- No se han modificado el formato de aislamiento por usuario ni los archivos JSON de la Spec 001 de forma incompatible (migración limpia, aditiva).

## Dudas abiertas
- [PENDIENTE TÉCNICO] La normalización de nombres (minúsculas, sin tildes, espacios colapsados en guión bajo) se implementará en el módulo de lógica de negocio, no en la capa de persistencia. El nombre original del usuario se almacena tal cual para mostrarlo en el listado; la clave normalizada se usa solo para comparación. Confirmar o ajustar en el plan técnico.