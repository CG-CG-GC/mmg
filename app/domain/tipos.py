from enum import Enum

EntityId = int
RelationId = int
EvidenceId = int


class TipoEntidad(str, Enum):
    PERSONA = "PERSONA"
    ORGANIZACION = "ORGANIZACION"
    EMAIL = "EMAIL"
    USUARIO = "USUARIO"
    DOMINIO = "DOMINIO"
    SITIO_WEB = "SITIO_WEB"
    IP = "IP"


class TipoRelacion(str, Enum):
    POSEE = "POSEE"
    UTILIZA = "UTILIZA"
    TRABAJA_EN = "TRABAJA_EN"
    ADMINISTRA = "ADMINISTRA"
    PERTENECE_A = "PERTENECE_A"
    APUNTA_A = "APUNTA_A"
