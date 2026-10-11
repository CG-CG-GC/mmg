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


class DataMappingError(RepositoryError):
    """Error al mapear entre filas de BD y objetos de dominio."""


class GraphReconstructionError(PersistenceError):
    """No se pudo reconstruir un grafo consistente desde la base de datos."""

