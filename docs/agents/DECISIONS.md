# Decisiones vigentes

Solo se registran decisiones respaldadas por el código o por documentos del
repositorio. Lo no confirmado figura como **pendiente de decisión**.

## Vigentes

| # | Decisión | Respaldo |
|---|---|---|
| D-01 | El motor de grafos (`app/domain`) es independiente de infraestructura: no depende de persistencia, API ni interfaz. Los algoritmos BFS, DFS y camino son propios. | [estado-proyecto.md](../estado-proyecto.md) §3, §6; [mvp-academico.md](../mvp-academico.md) |
| D-02 | Las relaciones son dirigidas. Se permiten ciclos y autoenlaces (bucles). El esquema SQLite impide repetir la misma terna origen, destino y tipo. | [mvp-academico.md](../mvp-academico.md); `tests/domain` |
| D-03 | Los identificadores son enteros positivos (`gt=0` en rutas y esquemas de la API). | `app/api/routes.py`, `app/api/schemas.py` |
| D-04 | La persistencia es SQLite con SQLAlchemy. | [mvp-academico.md](../mvp-academico.md) |
| D-05 | `valor_normalizado` se envía de forma explícita: no hay política de normalización automática. La respuesta de entidad lo incluye para poder editar otros campos sin sustituirlo. | `app/api/schemas.py`; [mvp-academico.md](../mvp-academico.md) |
| D-06 | Edición de entidades: `PUT /api/v1/entidades/{id}` reemplaza `tipo`, `valor`, `valor_normalizado`, `descripcion` y `metadata`. El ID se conserva. | `app/api/schemas.py` (`EntityUpdateRequest`) |
| D-07 | Edición de relaciones: `PUT /api/v1/relaciones/{id}` reemplaza `origen_id`, `destino_id`, `tipo`, `descripcion` y `fecha`. No recibe evidencias: las existentes se conservan. El ID se conserva. | `app/api/schemas.py` (`RelationUpdateRequest`) |
| D-08 | Los PUT responden 404 (no existe), 409 (conflicto), 422 (validación) y 500 según corresponda. La interfaz traduce esos errores a mensajes comprensibles. | Entrega de edición; `tests/api/test_update_api.py` |
| D-09 | La interfaz edita en línea dentro del inspector, sin modales, y mantiene la selección tras guardar. | [frontend.md](../frontend.md) |
| D-10 | Los layouts de Cytoscape (fuerzas, jerárquica, concéntrica, círculo y cuadrícula) solo cambian la posición de los nodos: no alteran datos ni relaciones. La última opción se guarda en `localStorage` (`mmg.layout`). | [frontend.md](../frontend.md); `app/frontend/app.js` |
| D-11 | Los contadores por tipo se calculan en el cliente con las listas que ya consulta la interfaz. | [frontend.md](../frontend.md) |
| D-12 | La consulta DNS usa `POST /api/v1/osint/dns` con `dominio` y `tipos` opcionales (por defecto A, AAAA, CNAME, MX y NS). Devuelve `dominio`, `fuente`, `consultado_en`, `registros` y `estados`. | `app/api/dns_routes.py`, `app/api/dns_schemas.py` |
| D-13 | La consulta DNS no persiste nada automáticamente: no crea entidades, relaciones ni evidencias. La interfaz la presenta como vista previa. | `app/frontend/osint.js` (aviso "No se guardó nada") |
| D-14 | No se modifica el esquema de SQLite sin autorización expresa del usuario. | Reglas de trabajo en [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) |
| D-15 | No hay commits ni push sin autorización, ni trailers `Co-authored-by`. | Instrucciones del usuario |
| D-16 | La incorporación DNS A/AAAA queda autorizada (P-01). Solo incorpora registros A y AAAA ya revisados por la aplicación. Crea o reutiliza DOMINIO, IP, `APUNTA_A` y evidencia en una única transacción `BEGIN IMMEDIATE`, con rollback completo ante error. No cambia el esquema SQLite ni los contratos CRUD. | Autorización del usuario (2026-11-17); `app/persistence/incorporacion_dns.py`; `app/application/incorporacion_dns.py`; `tests/persistence/test_incorporacion_dns.py` |
| D-17 | En este flujo, la identidad de un DOMINIO es su forma canónica IDNA: minúsculas, sin punto final y en ASCII, la misma regla que `normalizar_dominio`. Reutiliza una entidad guardada en Unicode o en punycode; varias equivalentes son ambiguas (409). No modifica entidades existentes. No es una regla global: los CRUD y `valor_normalizado` no cambian. | `canonizar_dominio` en `app/persistence/incorporacion_dns.py`; pruebas de equivalencia con `normalizar_dominio` en `tests/persistence/test_incorporacion_dns.py` |
| D-18 | La procedencia de la incorporación DNS es declarada por el cliente. Se guarda en `evidencia.fuente` con el prefijo `declarada por el cliente: ` y nunca se presenta como verificada por el servidor. | `PREFIJO_PROCEDENCIA_DECLARADA`; respuesta con `procedencia.declarada_por: "cliente"` (API del Agente 03) |
| D-19 | En la interfaz, "Incorporar al grafo" es una selección separada de "Revisado" y solo existe para A y AAAA; requiere revisión previa. La confirmación es un panel en línea dentro de la sección OSINT (sin modal, como D-09). Tras un fallo incierto (red, timeout, respuesta malformada o 503 con `persistencia: confirmada`) no se envía otro lote hasta actualizar el grafo. | `app/frontend/osint.js`, `app/frontend/osint-incorporacion.js`; `tests/api/test_osint_incorporacion_frontend.py` |
| D-20 | Una única política DNS (`app/domain/nombres_dns.py`) decide sobre el texto original, antes de cualquier minúscula, y la usan la consulta, la incorporación y la persistencia. Se rechazan con 422 las etiquetas Unicode que IDNA 2003 cambiaría (`ß`, `ẞ`, `ς`, `İ` y su forma descompuesta, separadores ideográficos, ligaduras, formas de compatibilidad, guion blando), las etiquetas vacías y las A-label `xn--` inválidas. Una A-label se acepta si su carga Punycode es canónica y el contenido decodificado está en minúsculas, NFC y NFKC, sin control, formato, espacio ni separadores. No es soporte de IDNA 2008: `xn--strae-oqa.de` y `xn--mnchen-3ya.de` se aceptan por esas reglas, sin reinterpretarlas. Ver P-06. | `app/domain/nombres_dns.py`; `tests/domain/test_nombres_dns.py`; `tests/persistence/test_politica_idna_coherente.py`; `tests/api/test_dns_idna_api.py` |
| D-21 | El grafo en memoria se carga y publica bajo un cerrojo del proceso (`_PUBLICACION_GRAFO`) que cubre todas las escrituras CRUD e incorporaciones: el último snapshot publicado es el último leído. Solo garantiza un proceso. Con varios procesos, cada uno tiene su copia y no hay sincronización. | `app/application/service.py`; `tests/application/test_concurrencia_grafo.py` |
| D-22 | Las demostraciones usan una base nueva creada por `scripts/preparar_demo.py` con datos ficticios (dominios `example.com` e IP de documentación). El script nunca sobrescribe un archivo existente ni usa `data/mmg.sqlite3`. La respuesta DNS de las capturas es simulada en el navegador y se identifica con la fuente `simulacion-demo-sin-red`; no se presenta como dato en vivo. | `scripts/preparar_demo.py`; `docs/demo/respuesta-dns-simulada.json`; `docs/demo-presentacion.md` |

## Pendientes de decisión

| # | Tema | Estado |
|---|---|---|
| P-01 | Incorporar al grafo resultados DNS revisados: mapeo A/AAAA, evidencia, deduplicación, atomicidad, procedencia y contrato de incorporación. | Autorizada. Persistencia (D-16, D-17, D-18), API (Agente 03) e interfaz (D-19) implementadas. Pendiente la auditoría del Agente 06. |
| P-02 | Política de normalización de `valor_normalizado` por tipo de entidad. | Sin definir; hoy lo ingresa el usuario. |
| P-03 | Qué rol tienen `protocolo-agentes.md` (los agentes proponen) y la práctica actual (los agentes editan con autorización). | Pendiente de decisión del usuario. |
| P-04 | Eliminar entidades y relaciones desde la interfaz: la API tiene DELETE, la interfaz aún no lo ofrece. | No decidido si entra en el alcance. |
| P-05 | Los CRUD manuales comparan texto exacto: pueden crear un DOMINIO en Unicode junto a uno equivalente en punycode. Cerrarlo exige una regla global (validación en CRUD o migración de datos). | Sin cambios en CRUD. QA-06-03 evaluado: la incorporación responde 409 sin escritura ante equivalentes, probado. Riesgo aceptado para la versión académica, pendiente de decisión del usuario. |
| P-06 | Python implementa IDNA 2003. D-20 evita que la conversión cambie un nombre y valida las A-label con criterios propios, sin usar `decode("idna")` como criterio de validez. El soporte completo de IDNA 2008 requiere una biblioteca no aprobada como dependencia. | Mitigación ampliada y probada. Sigue abierto: el usuario debe decidir si se implementa IDNA 2008. El Agente 06 debe verificar la mitigación. |
| P-07 | DFS (`app/domain/grafo.py`) es recursivo. Con la verificación del 18/11/2026, una cadena de 900 nodos se recorre y una de 1200 produce `RecursionError` (límite de Python de 1000). BFS no falla en esas cadenas. El manual y la guía oral lo documentan como limitación. | Pendiente de decisión: convertir DFS a una versión iterativa (cambio de dominio, Agente 03 con pruebas del Agente 06) o aceptar la limitación en la versión académica. |

## Cómo agregar una decisión

Agregá una fila con número correlativo, la decisión en una frase y su respaldo
(archivo o documento). Si falta respaldo, va en Pendientes. Si una decisión
reemplaza a otra, marcá la anterior como reemplazada en lugar de borrarla.
