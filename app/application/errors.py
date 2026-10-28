class ApplicationError(Exception):
    """Error base de la capa de aplicación."""


class GraphUnavailableError(ApplicationError):
    """El grafo no está disponible hasta reconstruirlo desde persistencia."""
