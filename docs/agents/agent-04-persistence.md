# Agente 04 · Persistencia

## Identidad y especialidad

Persistencia: repositorios, mapeos, SQLAlchemy y SQLite.

## Responsabilidades

- Repositorios y mapeos entre dominio y tablas.
- Integridad: claves foráneas, restricciones únicas y errores de persistencia.
- Consistencia entre la base y el grafo en memoria.
- Pruebas de persistencia con bases temporales.

## Áreas habituales

`app/persistence` y `tests/persistence`.

## Límites

- No modifica el esquema SQLite sin autorización expresa del usuario.
- No borra ni altera la base local ni sus datos; las pruebas usan bases temporales.
- No cambia contratos de API ni el dominio (coordinar con el Agente 03).
- No agrega dependencias sin justificarlas y obtener aprobación.
- No hace commit ni push sin autorización.

## Leer antes de trabajar

[README.md](README.md), esta ficha, [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md),
[DECISIONS.md](DECISIONS.md) y, según la tarea, [HANDOFF.md](HANDOFF.md) y
[BACKLOG.md](BACKLOG.md). El esquema vigente está descrito en
[mvp-academico.md](../mvp-academico.md).

## Entregar al finalizar

Una entrada en [HANDOFF.md](HANDOFF.md) con archivos, restricciones o esquema
afectados, pruebas con resultados reales y pendientes. Todo cambio de esquema
se registra primero como pendiente en [DECISIONS.md](DECISIONS.md).

## Comunicar resultados a

- Agente 03 si cambia el comportamiento que ven los servicios.
- Agente 06 para revisión.
- Agente 07 si cambia el modelo de datos documentado.
- Siempre al usuario.

## Continuidad técnica

Estado contrastado con el código el 2026-11-16 (rama `feature/project-expansion`,
cambios sin commit). `python -m pytest tests/persistence -q`: 37 aprobadas.

### Responsabilidades y límites

Los de la ficha: `app/persistence` y `tests/persistence`. Los servicios
(`app/application`), las rutas y los manejadores de error de `app/api` y el
dominio son del Agente 03; la interfaz es del Agente 05. Si una tarea exige
tocarlos, se coordina por [HANDOFF.md](HANDOFF.md).

### Arquitectura

- `schema.py`: modelos ORM (`TipoEntidadModel`, `EntidadModel`,
  `TipoRelacionModel`, `RelacionModel`, `EvidenciaModel`), `create_schema`,
  `seed_catalogs` e `initialize_database` (crea tablas y siembra catálogos; no hay
  migraciones).
- `database.py`: `create_sqlite_engine`, `create_session_factory`,
  `session_scope`, `assert_foreign_keys_enabled`.
- `repositories.py`: repositorios y DTOs; `mappers.py`: modelo ↔ dominio y
  serialización (metadata JSON en TEXT, fechas ISO); `graph_loader.py`:
  `load_graph_from_database`; `errors.py`: jerarquía de errores.
- Los repositorios devuelven objetos de dominio con ID asignado por SQLite.
  `mappers.entidad_from_model` carga también `valor_normalizado` en `Entidad`
  (campo opcional agregado al dominio por otro agente, sin commit).

### Repositorios y operaciones

| Repositorio | Operaciones |
|---|---|
| `EntidadRepository` | `create(EntidadCreateData)`, `update(id, EntidadUpdateData)`, `get_by_id`, `list_all`, `delete_by_id -> bool` |
| `RelacionRepository` | `create(RelacionCreateData)`, `update(id, RelacionUpdateData)`, `get_by_id`, `list_all`, `list_by_origen`, `delete_by_id -> bool` |
| `EvidenciaRepository` | `create(EvidenciaCreateData)`, `list_by_relation`, `delete_by_id -> bool` |

- `update` es un reemplazo total de los campos editables sobre el registro
  existente: conserva el ID y las filas dependientes. Las evidencias no se editan.
- `valor_normalizado` se guarda tal como llega; la persistencia no lo calcula.
- Un ID inexistente en `update` lanza `RecordNotFoundError`; en `delete_by_id`
  devuelve `False`; en `get_by_id`, `None`.
- `GraphApplicationService` (`app/application/service.py`) invoca los
  repositorios y reconstruye el grafo completo tras cada escritura.

### Sesiones, commits y rollback

- Cada método de repositorio abre su propia sesión con `session_scope`: verifica
  `PRAGMA foreign_keys`, ejecuta, hace `commit` al salir y `rollback` ante
  cualquier excepción, y cierra la sesión.
- Sesiones con `autoflush=False` y `expire_on_commit=False`.
- No existe API para compartir una sesión o transacción entre varias
  operaciones: encadenar `create` de distintos repositorios produce commits
  independientes.
- `PRAGMA foreign_keys=ON` se aplica en los eventos `connect` y `checkout` del
  engine.
- No hay configuración explícita de `BEGIN IMMEDIATE`, `busy_timeout` ni modo
  WAL, ni bloqueo en el servicio. La concurrencia de escritura no está tratada.

### Restricciones del esquema

- `entidad`: `UNIQUE uq_entidad_tipo_valor_normalizado (tipo_entidad_id, valor_normalizado)`;
  `valor_normalizado` NOT NULL; la comparación es textual exacta (sin colación
  especial).
- `relacion`: `UNIQUE uq_relacion_origen_destino_tipo (origen_id, destino_id, tipo_relacion_id)`;
  `fecha` se guarda como texto ISO.
- `evidencia`: sin restricción de unicidad.
- FK con `ON DELETE CASCADE`: relación → entidad (origen y destino) y evidencia →
  relación. FK con `RESTRICT` hacia los catálogos de tipos.
- Autoenlaces permitidos (D-02). Cambiar el esquema requiere autorización
  expresa (D-14).

### Clasificación de errores

| Error | Cuándo |
|---|---|
| `UniqueConstraintError` (hereda de `IntegrityConstraintError`) | Violación `UNIQUE` en `create` o `update` de entidad y relación. |
| `ForeignKeyConstraintError` (hereda de `IntegrityConstraintError`) | Violación de FK, p. ej. origen o destino inexistente. |
| `IntegrityConstraintError` | Otra violación de integridad (NOT NULL, etc.). |
| `RecordNotFoundError` (hereda de `RepositoryError`) | `update` de un ID inexistente. |
| `DataMappingError` (hereda de `RepositoryError`) | Metadata no serializable o dato persistido inválido; se propaga sin envolver. |
| `RepositoryError` | Resto de errores de SQLAlchemy. |
| `GraphReconstructionError` | La reconstrucción del grafo encontró datos inconsistentes (falla explícita, sin grafo parcial). |

La clasificación usa `sqlite_errorname` y, si no existe, el texto del mensaje de
SQLite (`_is_unique_violation`, `_is_foreign_key_violation`). Traducción HTTP
actual en `app/api/main.py`: `RecordNotFoundError` y `ForeignKeyConstraintError`
→ 404; `UniqueConstraintError` → 409; el resto de `PersistenceError`, incluido
`IntegrityConstraintError` genérico, → 500.

### Pruebas de persistencia (`tests/persistence`)

`test_schema_init`, `test_entidad_repository`, `test_relacion_repository`,
`test_evidencia_repository`, `test_integridad_referencial`, `test_graph_loader`,
`test_entidad_update` y `test_relacion_update`. Usan SQLite temporal (`tmp_path`)
mediante las fixtures de `conftest.py` (`session_factory`, `entidad_repo`,
`relacion_repo`, `evidencia_repo`). Los errores de actualización también se
ejercitan en `tests/application/test_service_update.py`.

### Riesgos técnicos conocidos

- Sin transacción compartida no hay atomicidad entre operaciones: base para la
  incorporación DNS (ver [HANDOFF.md](HANDOFF.md)).
- Escrituras concurrentes sin serialización: el patrón comprobar y luego
  escribir puede competir, y SQLite puede fallar por bloqueo; hoy ese caso cae en
  `RepositoryError` genérico (500).
- La unicidad compara texto persistido: formas equivalentes (mayúsculas, punto
  final, IPv6 abreviado) no se detectan en SQL; la normalización es de quien llama
  (P-02).
- Las evidencias pueden duplicarse: el esquema no lo impide.
- `GraphApplicationService` valida origen y destino de una relación contra el
  grafo en memoria, que puede quedar desactualizado respecto de la base.
- Tras un commit exitoso, si falla la reconstrucción el grafo queda invalidado
  aunque la persistencia ya esté confirmada.
- La reconstrucción del grafo recorre toda la base en cada escritura.
- Ninguna prueba de persistencia afirma `ForeignKeyConstraintError` de forma
  específica: solo se verifica `IntegrityConstraintError` y que no sea unicidad
  (`test_relacion_update.py`), y la subclase en la capa de aplicación.

### Pendiente (no implementado)

- Contrato transaccional de incorporación DNS A/AAAA: ver la entrega del
  2026-11-16 en [HANDOFF.md](HANDOFF.md). Sin código escrito.
- Operaciones con sesión compartida o unidad de trabajo.
- Búsqueda por valor canónico con detección de coincidencias múltiples.
- Serialización de escrituras concurrentes y clasificación de errores de bloqueo.
- Política de normalización de `valor_normalizado` (P-02, decisión del usuario).
