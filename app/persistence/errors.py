class PersistenceError(Exception):
    """Error base de la capa de persistencia."""


class SchemaInitializationError(PersistenceError):
    """Error al crear o inicializar el esquema."""


class ForeignKeysDisabledError(PersistenceError):
    """Las claves foráneas no están habilitadas para la conexión activa."""


class RepositoryError(PersistenceError):
    """Error base para operaciones de repositorio."""


class IntegrityConstraintError(RepositoryError):
    """Violación de restricción de integridad o unicidad."""


class UniqueConstraintError(IntegrityConstraintError):
    """Conflicto de unicidad: el registro duplicaría uno existente.

    Subclase de IntegrityConstraintError para no alterar a quienes ya capturan
    la clase base; otras violaciones (p. ej. claves foráneas) siguen siendo la base.
    """


class ForeignKeyConstraintError(IntegrityConstraintError):
    """Violación de clave foránea al guardar una referencia inexistente."""


class RecordNotFoundError(RepositoryError):
    """El identificador indicado no corresponde a ningún registro persistido."""


class DataMappingError(RepositoryError):
    """Error al mapear entre filas de BD y objetos de dominio."""


class GraphReconstructionError(PersistenceError):
    """No se pudo reconstruir un grafo consistente desde la base de datos."""


class DatabaseBusyError(RepositoryError):
    """Otra escritura mantiene la base bloqueada; la operación no se aplicó."""


class CoincidenciaAmbiguaError(RepositoryError):
    """Varias entidades existentes equivalen al mismo valor canónico."""
