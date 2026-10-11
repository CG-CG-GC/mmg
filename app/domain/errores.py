class ErrorDominio(Exception):
    """Error base del dominio y motor de grafo."""


class ErrorValidacion(ErrorDominio):
    """Error de validación de datos de entrada."""


class EntidadInvalidaError(ErrorValidacion):
    """Entidad con datos inválidos."""


class RelacionInvalidaError(ErrorValidacion):
    """Relación con datos inválidos."""


class EvidenciaInvalidaError(ErrorValidacion):
    """Evidencia con datos inválidos."""


class EntidadDuplicadaError(ErrorDominio):
    """Entidad duplicada por identidad de ID."""


class RelacionDuplicadaError(ErrorDominio):
    """Relación duplicada por ID o por origen-destino-tipo."""


class EntidadNoEncontradaError(ErrorDominio):
    """Entidad inexistente en el grafo."""


class RelacionNoEncontradaError(ErrorDominio):
    """Relación inexistente en el grafo."""


class InvarianteGrafoError(ErrorDominio):
    """Violación de invariantes estructurales del grafo."""
