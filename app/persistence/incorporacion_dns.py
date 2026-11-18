"""Incorporación transaccional de registros DNS A y AAAA al grafo persistido.

El lote llega ya validado y canonicalizado por la aplicación. La persistencia lo
vuelve a comprobar, busca coincidencias dentro de la transacción y escribe todo
en una sola transacción con BEGIN IMMEDIATE.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.nombres_dns import convertir_dominio
from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import transaccion_inmediata
from app.persistence.errors import CoincidenciaAmbiguaError, RepositoryError
from app.persistence.mappers import serialize_temporal
from app.persistence.repositories import (
    _resolve_entity_type_id,
    _resolve_relation_type_id,
    _translate_integrity_error,
)
from app.persistence.schema import EntidadModel, EvidenciaModel, RelacionModel

PREFIJO_PROCEDENCIA_DECLARADA = "declarada por el cliente: "
MAX_LONGITUD_DOMINIO = 253
_ETIQUETA_ASCII = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

EstadoIncorporacion = Literal["creada", "reutilizada"]


class LoteDnsInvalidoError(ValueError):
    """El lote no se puede canonicalizar o no cumple el contrato; no se escribe nada."""


@dataclass(slots=True)
class RegistroDnsIncorporacion:
    """Registro A o AAAA. `fuente` y `consultado_en` son declarados por el cliente."""

    tipo: Literal["A", "AAAA"]
    valor: str
    fuente: str
    consultado_en: datetime


@dataclass(slots=True)
class LoteDnsIncorporacion:
    """Dominio e IP en cualquier forma equivalente; se guardan en forma canónica."""

    dominio: str
    registros: tuple[RegistroDnsIncorporacion, ...]


@dataclass(slots=True)
class ObjetoIncorporado:
    id: int
    estado: EstadoIncorporacion


@dataclass(slots=True)
class ResultadoRegistroDns:
    tipo: str
    valor: str
    entidad: ObjetoIncorporado
    relacion: ObjetoIncorporado
    evidencia: ObjetoIncorporado


@dataclass(slots=True)
class ResultadoIncorporacionDns:
    dominio: ObjetoIncorporado
    resultados: tuple[ResultadoRegistroDns, ...]


class IncorporacionDnsRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def incorporar_lote(self, lote: LoteDnsIncorporacion) -> ResultadoIncorporacionDns:
        """Persiste el lote completo o nada. Ante error, se revierte todo el lote."""
        lote = _canonizar_lote(lote)
        try:
            with transaccion_inmediata(self._session_factory) as session:
                return _incorporar_en_sesion(session, lote)
        except IntegrityError as exc:
            raise _translate_integrity_error(
                exc,
                conflict="El lote duplicaría una relación o entidad existente.",
                generic="No se pudo incorporar el lote por una restricción de integridad.",
            ) from exc
        except SQLAlchemyError as exc:
            raise RepositoryError("No se pudo incorporar el lote DNS en persistencia.") from exc


def canonizar_dominio(valor: str) -> str:
    """Forma canónica DNS compatible con IDNA: minúsculas, sin punto final y en ASCII.

    Aplica la misma regla que `normalizar_dominio` de la aplicación, así una entidad
    guardada en Unicode o en punycode produce la misma clave. Lanza ValueError si el
    valor no es un nombre válido.
    """
    # La política compartida decide sobre el texto original. Lanza ValueError si no es válido.
    ascii_ = convertir_dominio(valor)
    if len(ascii_) > MAX_LONGITUD_DOMINIO or not all(
        _ETIQUETA_ASCII.match(etiqueta) for etiqueta in ascii_.split(".")
    ):
        raise ValueError("el nombre tiene etiquetas no válidas")
    return ascii_


def canonizar_ip(valor: str) -> str:
    """Forma canónica de IP. Rechaza zonas IPv6 (`%eth0`), que no son direcciones DNS."""
    ip = ipaddress.ip_address(valor.strip())
    if getattr(ip, "scope_id", None):
        raise ValueError("las zonas IPv6 no se admiten")
    return str(ip)


def _canonizar_lote(lote: LoteDnsIncorporacion) -> LoteDnsIncorporacion:
    if not lote.registros:
        raise LoteDnsInvalidoError("El lote no contiene registros.")
    try:
        dominio = canonizar_dominio(lote.dominio)
    except ValueError as exc:
        raise LoteDnsInvalidoError(f"Dominio no válido: {exc}.") from exc
    return LoteDnsIncorporacion(
        dominio=dominio,
        registros=tuple(_canonizar_registro(registro) for registro in lote.registros),
    )


def _canonizar_registro(registro: RegistroDnsIncorporacion) -> RegistroDnsIncorporacion:
    if registro.tipo not in ("A", "AAAA"):
        raise LoteDnsInvalidoError(f"Tipo de registro no admitido: {registro.tipo!r}.")
    try:
        valor = canonizar_ip(registro.valor)
    except ValueError as exc:
        raise LoteDnsInvalidoError(f"Dirección IP no válida: {registro.valor!r} ({exc}).") from exc
    if ipaddress.ip_address(valor).version != (4 if registro.tipo == "A" else 6):
        raise LoteDnsInvalidoError(f"La IP {valor} no corresponde al tipo {registro.tipo}.")
    fuente = registro.fuente.strip()
    if not fuente:
        raise LoteDnsInvalidoError("La fuente declarada no puede estar vacía.")
    if registro.consultado_en.utcoffset() is None:
        raise LoteDnsInvalidoError("La fecha de consulta debe incluir zona horaria.")
    return replace(registro, valor=valor, fuente=fuente)


def _incorporar_en_sesion(session: Session, lote: LoteDnsIncorporacion) -> ResultadoIncorporacionDns:
    tipo_dominio = _resolve_entity_type_id(session, TipoEntidad.DOMINIO)
    tipo_ip = _resolve_entity_type_id(session, TipoEntidad.IP)
    tipo_relacion = _resolve_relation_type_id(session, TipoRelacion.APUNTA_A)

    dominio = _obtener_o_crear_entidad(
        session, tipo_dominio, TipoEntidad.DOMINIO, lote.dominio, canonizar_dominio
    )
    resultados = []
    for registro in lote.registros:
        ip = _obtener_o_crear_entidad(session, tipo_ip, TipoEntidad.IP, registro.valor, canonizar_ip)
        relacion = _obtener_o_crear_relacion(session, dominio.id, ip.id, tipo_relacion)
        evidencia = _obtener_o_crear_evidencia(
            session,
            relacion.id,
            fuente=PREFIJO_PROCEDENCIA_DECLARADA + registro.fuente,
            fecha=serialize_temporal(registro.consultado_en.astimezone(timezone.utc)),
            descripcion=f"Consulta DNS {registro.tipo} de {lote.dominio}",
        )
        resultados.append(
            ResultadoRegistroDns(
                tipo=registro.tipo,
                valor=registro.valor,
                entidad=ip,
                relacion=relacion,
                evidencia=evidencia,
            )
        )
    return ResultadoIncorporacionDns(dominio=dominio, resultados=tuple(resultados))


def _obtener_o_crear_entidad(
    session: Session,
    tipo_id: int,
    tipo: TipoEntidad,
    canonico: str,
    canonizar: Callable[[str], str],
) -> ObjetoIncorporado:
    """Busca por `valor` y `valor_normalizado` canonicalizados; no modifica coincidencias."""
    filas = session.execute(
        select(EntidadModel.id, EntidadModel.valor, EntidadModel.valor_normalizado)
        .where(EntidadModel.tipo_entidad_id == tipo_id)
        .order_by(EntidadModel.id)
    ).all()
    coincidencias = [
        fila.id
        for fila in filas
        if _equivale(fila.valor, canonico, canonizar)
        or _equivale(fila.valor_normalizado, canonico, canonizar)
    ]
    if len(coincidencias) > 1:
        raise CoincidenciaAmbiguaError(
            f"Hay {len(coincidencias)} entidades {tipo.value} equivalentes a {canonico!r}: "
            f"ids {coincidencias}."
        )
    if coincidencias:
        return ObjetoIncorporado(id=coincidencias[0], estado="reutilizada")

    modelo = EntidadModel(tipo_entidad_id=tipo_id, valor=canonico, valor_normalizado=canonico)
    session.add(modelo)
    session.flush()
    return ObjetoIncorporado(id=modelo.id, estado="creada")


def _equivale(valor_existente: str, canonico: str, canonizar: Callable[[str], str]) -> bool:
    try:
        return canonizar(valor_existente) == canonico
    except ValueError:
        # Un valor no interpretable (p. ej. IP mal formada) nunca coincide.
        return False


def _obtener_o_crear_relacion(
    session: Session, origen_id: int, destino_id: int, tipo_relacion_id: int
) -> ObjetoIncorporado:
    existente = session.scalar(
        select(RelacionModel.id).where(
            RelacionModel.origen_id == origen_id,
            RelacionModel.destino_id == destino_id,
            RelacionModel.tipo_relacion_id == tipo_relacion_id,
        )
    )
    if existente is not None:
        return ObjetoIncorporado(id=existente, estado="reutilizada")

    modelo = RelacionModel(origen_id=origen_id, destino_id=destino_id, tipo_relacion_id=tipo_relacion_id)
    session.add(modelo)
    session.flush()
    return ObjetoIncorporado(id=modelo.id, estado="creada")


def _obtener_o_crear_evidencia(
    session: Session, relacion_id: int, *, fuente: str, fecha: str, descripcion: str
) -> ObjetoIncorporado:
    existente = session.scalar(
        select(EvidenciaModel.id)
        .where(
            EvidenciaModel.relacion_id == relacion_id,
            EvidenciaModel.fuente == fuente,
            EvidenciaModel.fecha == fecha,
            EvidenciaModel.descripcion == descripcion,
        )
        .order_by(EvidenciaModel.id)
        .limit(1)
    )
    if existente is not None:
        return ObjetoIncorporado(id=existente, estado="reutilizada")

    modelo = EvidenciaModel(relacion_id=relacion_id, fuente=fuente, fecha=fecha, descripcion=descripcion)
    session.add(modelo)
    session.flush()
    return ObjetoIncorporado(id=modelo.id, estado="creada")
