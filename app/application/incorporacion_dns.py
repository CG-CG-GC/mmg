"""Caso de uso: incorporar al grafo registros DNS A y AAAA elegidos por el usuario.

La fuente y la fecha llegan declaradas por el cliente. El servidor no las verifica
ni afirma que el proveedor respondió.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.dns_lookup import DominioInvalidoError, normalizar_dominio
from app.application.errors import ApplicationError
from app.persistence.errors import (
    CoincidenciaAmbiguaError,
    DatabaseBusyError,
    ForeignKeyConstraintError,
    UniqueConstraintError,
)
from app.persistence.incorporacion_dns import (
    IncorporacionDnsRepository,
    LoteDnsIncorporacion,
    LoteDnsInvalidoError,
    ObjetoIncorporado,
    RegistroDnsIncorporacion,
)

TIPOS_INCORPORABLES = ("A", "AAAA")
MAX_REGISTROS_INCORPORACION = 100
MAX_LONGITUD_FUENTE = 100


class IncorporacionDnsInvalidaError(ApplicationError, ValueError):
    """El lote no cumple el contrato; no se escribió nada."""


class IncorporacionDnsConflictoError(ApplicationError):
    """Hay coincidencias ambiguas o un conflicto de unicidad; no se escribió nada."""


class IncorporacionDnsOcupadaError(ApplicationError):
    """SQLite está ocupado por otra escritura; no se escribió nada."""


class IncorporacionDnsFallaInternaError(ApplicationError):
    """Persistencia encontró una referencia inconsistente; no se escribió nada."""


class IncorporacionPersistidaSinGrafoError(ApplicationError):
    """Los datos se guardaron, pero el grafo en memoria no pudo reconstruirse."""


@dataclass(frozen=True, slots=True)
class RegistroSolicitadoDns:
    tipo: str
    valor: str
    fuente: str
    consultado_en: datetime


@dataclass(frozen=True, slots=True)
class SolicitudIncorporacionDns:
    dominio: str
    registros: Sequence[RegistroSolicitadoDns]


@dataclass(frozen=True, slots=True)
class RegistroIncorporadoDns:
    tipo: str
    valor: str
    fuente: str  # declarada por el cliente
    consultado_en: datetime  # en UTC, declarada por el cliente
    entidad: ObjetoIncorporado
    relacion: ObjetoIncorporado
    evidencia: ObjetoIncorporado


@dataclass(frozen=True, slots=True)
class IncorporacionDnsResultado:
    dominio: ObjetoIncorporado
    registros: tuple[RegistroIncorporadoDns, ...]


def preparar_lote(solicitud: SolicitudIncorporacionDns) -> LoteDnsIncorporacion:
    """Valida y canonicaliza la solicitud. No accede a la base de datos."""
    if not solicitud.registros:
        raise IncorporacionDnsInvalidaError("La lista de registros no puede estar vacía.")
    if len(solicitud.registros) > MAX_REGISTROS_INCORPORACION:
        raise IncorporacionDnsInvalidaError(
            f"Un lote admite como máximo {MAX_REGISTROS_INCORPORACION} registros."
        )
    try:
        dominio = normalizar_dominio(solicitud.dominio)
    except DominioInvalidoError as exc:
        raise IncorporacionDnsInvalidaError(f"Dominio no válido: {exc}.") from exc

    registros: list[RegistroDnsIncorporacion] = []
    vistos: set[tuple[str, str, str, datetime]] = set()
    for indice, registro in enumerate(solicitud.registros):
        preparado = _preparar_registro(indice, registro)
        clave = (preparado.tipo, preparado.valor, preparado.fuente, preparado.consultado_en)
        if clave in vistos:
            continue  # Selección repetida: se incorpora una sola vez.
        vistos.add(clave)
        registros.append(preparado)
    return LoteDnsIncorporacion(dominio=dominio, registros=tuple(registros))


def _preparar_registro(indice: int, registro: RegistroSolicitadoDns) -> RegistroDnsIncorporacion:
    def rechazar(motivo: str) -> IncorporacionDnsInvalidaError:
        return IncorporacionDnsInvalidaError(f"registros[{indice}]: {motivo}")

    if registro.tipo not in TIPOS_INCORPORABLES:
        raise rechazar(f"tipo {registro.tipo!r} no admitido; solo se incorporan A y AAAA.")

    try:
        ip = ipaddress.ip_address(registro.valor.strip())
    except ValueError as exc:
        raise rechazar(f"{registro.valor!r} no es una dirección IP válida.") from exc
    version_esperada = 4 if registro.tipo == "A" else 6
    if ip.version != version_esperada:
        raise rechazar(f"un registro {registro.tipo} requiere una dirección IPv{version_esperada}.")
    if getattr(ip, "scope_id", None):
        raise rechazar("no se admiten direcciones IPv6 con identificador de zona.")

    fuente = registro.fuente.strip()
    if not fuente or len(fuente) > MAX_LONGITUD_FUENTE or not fuente.isprintable():
        raise rechazar(
            f"la fuente declarada debe tener entre 1 y {MAX_LONGITUD_FUENTE} caracteres imprimibles."
        )

    if registro.consultado_en.utcoffset() is None:
        raise rechazar("la fecha de consulta debe incluir zona horaria.")

    return RegistroDnsIncorporacion(
        tipo=registro.tipo,
        valor=str(ip),
        fuente=fuente,
        consultado_en=registro.consultado_en,
    )


class IncorporacionDnsService:
    """Valida, persiste en una sola transacción y reconstruye el grafo una vez."""

    def __init__(
        self,
        repositorio: IncorporacionDnsRepository,
        refrescar_grafo: Callable[[], None],
    ) -> None:
        self._repositorio = repositorio
        self._refrescar_grafo = refrescar_grafo

    def incorporar(self, solicitud: SolicitudIncorporacionDns) -> IncorporacionDnsResultado:
        lote = preparar_lote(solicitud)
        try:
            resultado = self._repositorio.incorporar_lote(lote)
        except LoteDnsInvalidoError as exc:
            raise IncorporacionDnsInvalidaError(str(exc)) from exc
        except (CoincidenciaAmbiguaError, UniqueConstraintError) as exc:
            raise IncorporacionDnsConflictoError(str(exc)) from exc
        except DatabaseBusyError as exc:
            raise IncorporacionDnsOcupadaError(str(exc)) from exc
        except ForeignKeyConstraintError as exc:
            raise IncorporacionDnsFallaInternaError(
                "No se pudo incorporar el lote por una referencia interna inconsistente."
            ) from exc

        try:
            self._refrescar_grafo()
        except Exception as exc:
            raise IncorporacionPersistidaSinGrafoError(
                "Los datos de la incorporación sí se guardaron, pero el grafo no pudo "
                "reconstruirse. Reintente la misma incorporación para recuperarlo."
            ) from exc

        registros = tuple(
            RegistroIncorporadoDns(
                tipo=preparado.tipo,
                valor=preparado.valor,
                fuente=preparado.fuente,
                consultado_en=preparado.consultado_en.astimezone(UTC),
                entidad=persistido.entidad,
                relacion=persistido.relacion,
                evidencia=persistido.evidencia,
            )
            for preparado, persistido in zip(lote.registros, resultado.resultados, strict=True)
        )
        return IncorporacionDnsResultado(dominio=resultado.dominio, registros=registros)
