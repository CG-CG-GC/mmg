"""Servicio de aplicacion para consultar registros DNS publicos.

No escribe en la base de datos ni toca el grafo: devuelve resultados para que el
usuario elija cuales incorporar. Los datos del proveedor se tratan como no confiables.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.application.errors import ApplicationError
from app.domain.nombres_dns import NombreDnsNoEquivalenteError, convertir_dominio
from app.integrations.dns_google import (
    CODIGOS_TIPO_DNS,
    ProveedorDnsHttpError,
    ProveedorDnsRedError,
    ProveedorDnsRespuestaError,
    ProveedorDnsTimeoutError,
    RespuestaCrudaDns,
)

TIPOS_REGISTRO_INICIALES = ("A", "AAAA", "CNAME", "MX", "NS")

ESTADO_REGISTRO_ENCONTRADO = "encontrado"

ESTADO_CONSULTA_OK = "ok"
ESTADO_CONSULTA_SIN_REGISTROS = "sin_registros"
ESTADO_CONSULTA_DOMINIO_INEXISTENTE = "dominio_inexistente"
ESTADO_CONSULTA_ERROR_TIMEOUT = "error_timeout"
ESTADO_CONSULTA_ERROR_RED = "error_red"
ESTADO_CONSULTA_ERROR_HTTP = "error_http"
ESTADO_CONSULTA_ERROR_RESPUESTA = "error_respuesta"
ESTADO_CONSULTA_ERROR_DNS = "error_dns"

MAX_REGISTROS_POR_TIPO = 50
MAX_LONGITUD_DOMINIO = 253
_ETIQUETA = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SEPARADORES_NO_PERMITIDOS = re.compile(r"[\s/\\:@?#%&=+*,;'\"<>\[\]{}()|^~`!$]")


class DominioInvalidoError(ApplicationError, ValueError):
    """El dominio de entrada no es un nombre DNS valido."""


class TipoRegistroInvalidoError(ApplicationError, ValueError):
    """Se pidio un tipo de registro que el servicio no soporta."""


class ProveedorDns(Protocol):
    fuente: str

    def consultar(self, dominio: str, tipo: str) -> RespuestaCrudaDns: ...


@dataclass(frozen=True, slots=True)
class RegistroDns:
    tipo: str
    valor: str
    estado: str
    fuente: str
    consultado_en: datetime
    prioridad: int | None = None  # solo MX


@dataclass(frozen=True, slots=True)
class EstadoConsultaTipo:
    tipo: str
    estado: str
    descartados: int = 0  # valores del proveedor que no pasaron la validacion


@dataclass(frozen=True, slots=True)
class ResultadoConsultaDns:
    dominio: str
    fuente: str
    consultado_en: datetime
    registros: tuple[RegistroDns, ...]
    estados: tuple[EstadoConsultaTipo, ...]


def normalizar_dominio(entrada: str) -> str:
    """Devuelve el dominio en minusculas y ASCII (punycode) o lanza DominioInvalidoError."""
    if not isinstance(entrada, str):
        raise DominioInvalidoError("el dominio debe ser texto")
    # La política compartida decide sobre el texto original, antes de cualquier minúscula.
    try:
        dominio = convertir_dominio(entrada)
    except NombreDnsNoEquivalenteError as exc:
        raise DominioInvalidoError(f"el dominio no puede convertirse con seguridad: {exc}") from exc
    if "://" in dominio or _SEPARADORES_NO_PERMITIDOS.search(dominio):
        raise DominioInvalidoError("el dominio contiene caracteres no permitidos")
    try:
        ipaddress.ip_address(dominio)
    except ValueError:
        pass
    else:
        raise DominioInvalidoError("se esperaba un nombre de dominio, no una direccion IP")
    if not _es_nombre_valido(dominio) or "." not in dominio:
        raise DominioInvalidoError("el dominio no tiene un formato valido")
    if dominio.rsplit(".", 1)[1].isdigit():
        raise DominioInvalidoError("el TLD no puede ser numerico")
    return dominio


def _es_nombre_valido(nombre: str) -> bool:
    if len(nombre) > MAX_LONGITUD_DOMINIO:
        return False
    return all(_ETIQUETA.match(etiqueta) for etiqueta in nombre.split("."))


def _nombre_de_respuesta(dato: str) -> str | None:
    nombre = dato.strip().lower()
    if nombre.endswith("."):
        nombre = nombre[:-1]
    return nombre if _es_nombre_valido(nombre) else None


def _validar_valor(tipo: str, dato: str) -> tuple[str, int | None] | None:
    """Devuelve (valor, prioridad) normalizado o None si el dato no es aceptable."""
    if len(dato) > 300:
        return None
    if tipo == "A":
        try:
            return str(ipaddress.IPv4Address(dato.strip())), None
        except ValueError:
            return None
    if tipo == "AAAA":
        try:
            return str(ipaddress.IPv6Address(dato.strip())), None
        except ValueError:
            return None
    if tipo in ("CNAME", "NS"):
        nombre = _nombre_de_respuesta(dato)
        return (nombre, None) if nombre else None
    if tipo == "MX":
        partes = dato.split()
        if len(partes) != 2 or not partes[0].isascii() or not partes[0].isdigit():
            return None
        prioridad = int(partes[0])
        nombre = _nombre_de_respuesta(partes[1])
        if prioridad > 65535 or nombre is None:  # "0 ." (MX nulo) tambien se descarta
            return None
        return nombre, prioridad
    return None


class DnsLookupService:
    def __init__(
        self,
        proveedor: ProveedorDns,
        *,
        reloj: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._proveedor = proveedor
        self._reloj = reloj

    def consultar(
        self, dominio: str, tipos: Sequence[str] = TIPOS_REGISTRO_INICIALES
    ) -> ResultadoConsultaDns:
        nombre = normalizar_dominio(dominio)
        tipos_normalizados = self._normalizar_tipos(tipos)
        consultado_en = self._reloj()
        registros: list[RegistroDns] = []
        estados: list[EstadoConsultaTipo] = []
        for tipo in tipos_normalizados:
            nuevos, estado = self._consultar_tipo(nombre, tipo, consultado_en)
            registros.extend(nuevos)
            estados.append(estado)
        return ResultadoConsultaDns(
            dominio=nombre,
            fuente=self._proveedor.fuente,
            consultado_en=consultado_en,
            registros=tuple(registros),
            estados=tuple(estados),
        )

    @staticmethod
    def _normalizar_tipos(tipos: Sequence[str]) -> tuple[str, ...]:
        if isinstance(tipos, str) or not tipos:
            raise TipoRegistroInvalidoError("tipos debe ser una lista no vacia")
        vistos: dict[str, None] = {}
        for tipo in tipos:
            if not isinstance(tipo, str) or tipo.strip().upper() not in TIPOS_REGISTRO_INICIALES:
                raise TipoRegistroInvalidoError(f"tipo de registro no soportado: {tipo!r}")
            vistos[tipo.strip().upper()] = None
        return tuple(vistos)

    def _consultar_tipo(
        self, dominio: str, tipo: str, consultado_en: datetime
    ) -> tuple[list[RegistroDns], EstadoConsultaTipo]:
        try:
            respuesta = self._proveedor.consultar(dominio, tipo)
        except ProveedorDnsTimeoutError:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_ERROR_TIMEOUT)
        except ProveedorDnsRedError:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_ERROR_RED)
        except ProveedorDnsHttpError:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_ERROR_HTTP)
        except ProveedorDnsRespuestaError:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_ERROR_RESPUESTA)

        if respuesta.codigo_dns == 3:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_DOMINIO_INEXISTENTE)
        if respuesta.codigo_dns != 0:
            return [], EstadoConsultaTipo(tipo, ESTADO_CONSULTA_ERROR_DNS)

        codigo_tipo = CODIGOS_TIPO_DNS[tipo]
        vistos: set[tuple[str, int | None]] = set()
        registros: list[RegistroDns] = []
        descartados = 0
        for codigo, dato in respuesta.respuestas:
            if codigo != codigo_tipo:
                continue  # p. ej. el CNAME intermedio que acompana a una consulta A
            validado = _validar_valor(tipo, dato)
            if validado is None or len(registros) >= MAX_REGISTROS_POR_TIPO:
                descartados += 1
                continue
            if validado in vistos:
                continue
            vistos.add(validado)
            registros.append(
                RegistroDns(
                    tipo=tipo,
                    valor=validado[0],
                    prioridad=validado[1],
                    estado=ESTADO_REGISTRO_ENCONTRADO,
                    fuente=self._proveedor.fuente,
                    consultado_en=consultado_en,
                )
            )
        estado = ESTADO_CONSULTA_OK if registros else ESTADO_CONSULTA_SIN_REGISTROS
        return registros, EstadoConsultaTipo(tipo, estado, descartados)
