"""Adaptador de Google Public DNS over HTTPS.

Solo transporta y decodifica la respuesta del proveedor. No valida el contenido
de los registros: eso corresponde al servicio de aplicacion.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

FUENTE_GOOGLE_DOH = "google-public-dns-doh"
URL_GOOGLE_DOH = "https://dns.google/resolve"
TIMEOUT_POR_DEFECTO = 5.0
MAX_BYTES_RESPUESTA = 64 * 1024

CODIGOS_TIPO_DNS = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "AAAA": 28}

# (url, timeout) -> (codigo HTTP, cuerpo leido hasta MAX_BYTES_RESPUESTA + 1 bytes)
Transporte = Callable[[str, float], tuple[int, bytes]]


class ProveedorDnsError(Exception):
    """Error base del proveedor DNS."""


class ProveedorDnsTimeoutError(ProveedorDnsError):
    """La consulta supero el timeout."""


class ProveedorDnsRedError(ProveedorDnsError):
    """Fallo de red o TLS antes de recibir respuesta HTTP."""


class ProveedorDnsHttpError(ProveedorDnsError):
    """El proveedor respondio con un estado HTTP distinto de 200."""


class ProveedorDnsRespuestaError(ProveedorDnsError):
    """La respuesta no es JSON valido, es demasiado grande o tiene forma inesperada."""


@dataclass(frozen=True, slots=True)
class RespuestaCrudaDns:
    codigo_dns: int
    # Pares (codigo de tipo DNS, dato) tal como los devolvio el proveedor.
    respuestas: tuple[tuple[int, str], ...]


def _transporte_urllib(url: str, timeout: float) -> tuple[int, bytes]:
    peticion = urllib.request.Request(url, headers={"Accept": "application/dns-json"})  # nosec B310
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:  # nosec B310
            return respuesta.status, respuesta.read(MAX_BYTES_RESPUESTA + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except TimeoutError as exc:
        raise ProveedorDnsTimeoutError("timeout al consultar el proveedor DNS") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            raise ProveedorDnsTimeoutError("timeout al consultar el proveedor DNS") from exc
        raise ProveedorDnsRedError("error de red al consultar el proveedor DNS") from exc
    except OSError as exc:
        raise ProveedorDnsRedError("error de red al consultar el proveedor DNS") from exc


class GoogleDohProvider:
    fuente = FUENTE_GOOGLE_DOH

    def __init__(
        self,
        *,
        timeout: float = TIMEOUT_POR_DEFECTO,
        transporte: Transporte = _transporte_urllib,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout debe ser positivo")
        self._timeout = timeout
        self._transporte = transporte

    def consultar(self, dominio: str, tipo: str) -> RespuestaCrudaDns:
        if tipo not in CODIGOS_TIPO_DNS:
            raise ValueError(f"tipo de registro no soportado: {tipo}")
        url = URL_GOOGLE_DOH + "?" + urllib.parse.urlencode({"name": dominio, "type": tipo})
        estado_http, cuerpo = self._transporte(url, self._timeout)
        if estado_http != 200:
            raise ProveedorDnsHttpError(f"el proveedor respondio HTTP {estado_http}")
        if len(cuerpo) > MAX_BYTES_RESPUESTA:
            raise ProveedorDnsRespuestaError("respuesta del proveedor demasiado grande")
        return _decodificar(cuerpo)


def _decodificar(cuerpo: bytes) -> RespuestaCrudaDns:
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProveedorDnsRespuestaError("la respuesta no es JSON valido") from exc
    if not isinstance(datos, dict):
        raise ProveedorDnsRespuestaError("el JSON de respuesta no es un objeto")
    codigo = datos.get("Status")
    if isinstance(codigo, bool) or not isinstance(codigo, int):
        raise ProveedorDnsRespuestaError("falta el campo Status o no es entero")
    crudas = datos.get("Answer")
    if crudas is None:
        crudas = []
    if not isinstance(crudas, list):
        raise ProveedorDnsRespuestaError("el campo Answer no es una lista")
    pares: list[tuple[int, str]] = []
    for item in crudas:
        # Un item malformado se ignora; el resto de la respuesta sigue siendo util.
        if not isinstance(item, dict):
            continue
        tipo, dato = item.get("type"), item.get("data")
        if isinstance(tipo, bool) or not isinstance(tipo, int) or not isinstance(dato, str):
            continue
        pares.append((tipo, dato))
    return RespuestaCrudaDns(codigo_dns=codigo, respuestas=tuple(pares))
