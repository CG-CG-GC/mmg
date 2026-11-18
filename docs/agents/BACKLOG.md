# Backlog

Estado real según lo verificado hasta la fecha de la última entrega registrada
en [HANDOFF.md](HANDOFF.md). Una tarea solo figura como implementada si se
verificó.

## Implementado y verificado

| Área | Estado | Verificación |
|---|---|---|
| MVP: entidades, relaciones, grafo, BFS, DFS y camino | Implementado | Suite pytest; recorrido en navegador. |
| Edición de entidades y relaciones (backend y frontend) | Implementado | Pruebas de API y de navegador (404, 409, 422; evidencias e IDs conservados). |
| Cinco layouts y contadores por tipo | Implementado | Prueba en navegador con grafos pequeños y de 66 nodos; prueba de plantilla en pytest. |
| OSINT DNS backend y frontend | Implementado | Pruebas de API, aplicación y frontend; auditoría del Agente 06. |
| Auditoría independiente del Agente 06 sobre OSINT DNS | Aprobada con observaciones | QA-06-01 y QA-06-04 corregidos para D-20; QA-06-02 verificado para un proceso y una instancia; QA-06-03 es un riesgo documentado. Ver [auditoria-integral-dns.md](auditoria-integral-dns.md). |
| UX DNS: mensaje amigable ante JSON malformado | Implementado por el Agente 05 | Probado en navegador con respuesta simulada. |
| UX DNS: recuperación del foco tras la consulta | Implementado por el Agente 05 | Probado en navegador: éxito, error HTTP, red y timeout. |
| Documentación de usuario, guion oral y demostración (Agente 07) | Listo para revisión | Manual con 24 capturas reales de la interfaz (`docs/img/manual/`); comandos verificados; demo creada con `scripts/preparar_demo.py` y comprobada en la API; suite 368 aprobadas, 1 omitida. Ver [HANDOFF.md](HANDOFF.md). |
| Demostración personal aislada (Agente 07) | Lista para revisión | `scripts/preparar_demo_personal.py` lee configuración externa, rechaza sobrescritura y crea una base privada fuera del repositorio. Verificado en navegador, algoritmos, reinicio y simulación DNS offline; suite 369 aprobadas, 1 omitida. Datos locales excluidos de Git. Ver [HANDOFF.md](HANDOFF.md). |

Las dos mejoras de UX DNS no tienen una prueba automatizada específica; ver
[HANDOFF.md](HANDOFF.md).

## Incorporación DNS selectiva

**Estado:** aprobada con observaciones para la versión académica. Pueden comenzar el manual, las capturas y el guion de la presentación.

- QA-06-01 (IDNA 2003 consulta otro dominio): **corregido y ampliado.** Una única política (D-20) decide sobre el texto original, antes de cualquier minúscula. Rechaza `İstanbul.tr` (y su forma descompuesta), `ẞ`, `ß` y demás transformaciones no equivalentes con 422 en consulta e incorporación. No es soporte de IDNA 2008 (P-06).
- QA-06-02 (reconstrucciones concurrentes dejan el grafo atrasado): **corregido dentro de un proceso**, sin cambios en esta etapa (D-21). No cubre varios procesos.
- QA-06-03 (duplicados Unicode y punycode en CRUD): **evaluado, riesgo conocido.** La incorporación responde 409 sin escritura ante equivalentes. El CRUD sigue permitiéndolos (P-05), por decisión pendiente del usuario.
- QA-06-04 (A-labels `xn--` inválidas): **corregido.** Las A-label se validan por carga Punycode canónica y por el contenido decodificado. `xn--bogus.de` y `xn--invalid-zz.de` responden 422 antes de consultar o escribir. `xn--strae-oqa.de` y `xn--mnchen-3ya.de` se aceptan sin reinterpretarlas.
- Verificación independiente: **368 aprobadas, 1 omitida**; las 12 reproducciones de la reauditoría y las seis pruebas de concurrencia pasan. No se requiere otra intervención del Agente 04 sobre la canonicalización de este flujo.
- Ejecución: una instancia y un proceso. Varios procesos o modificaciones externas de SQLite no sincronizan los grafos.
- Interfaz (Agente 05): sin cambios. Los rechazos muestran el mensaje del servidor.
- No implementado: CNAME, MX y NS (solo se muestran, sin control de incorporación).
- Limitación conocida: tras incorporar, los registros nuevos aparecen como "Posible duplicado" en la vista previa. Es la heurística existente, no un error de datos.

## Pendientes menores

| Tema | Responsable sugerido | Nota |
|---|---|---|
| Prueba automatizada para el mensaje de JSON malformado y el foco en OSINT DNS | Agente 06 / 05 | No existe todavía. |
| Eliminar elementos desde la interfaz | Pendiente de decisión (P-04) | La API ya tiene DELETE. |
| Política de normalización | Pendiente de decisión (P-02) | Hoy es explícita. |
| Aclarar `protocolo-agentes.md` y la numeración histórica de `estado-proyecto.md` | Agente 07 | Ver PROJECT_CONTEXT.md. |
| Duplicados de DOMINIO en Unicode frente a punycode en la incorporación DNS | Agente 04 | Resuelto en persistencia (D-17). Los CRUD siguen sin esta regla: ver P-05. |
| Limitación de layouts: etiquetas ilegibles en grafos muy grandes sin acercar | Agente 05 | Conocida. |
| DFS recursivo falla en cadenas de más de ~1000 nodos (P-07) | Pendiente de decisión; Agente 03 y Agente 06 | Verificado: 900 nodos OK, 1200 con `RecursionError`. Documentado en el manual y la guía oral. |
| La interfaz no tiene buscador por texto | Pendiente de decisión | Documentado en el manual (sección 14). No está en el alcance del MVP confirmado. |
| La interfaz muestra solo el número de evidencias de una relación | Agente 05 | El contenido se consulta por API. Documentado en el manual (sección 24). |
| Mensaje de error del CRUD con texto genérico de posible pérdida | Agente 05 | Al fallar una escritura, la interfaz agrega "Si el servidor falló después de guardar..." incluso ante un 409 sin escritura. Revisar el texto. |
