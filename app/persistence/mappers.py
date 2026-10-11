from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from app.domain.entidad import Entidad
from app.domain.evidencia import Evidencia
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.errors import DataMappingError
from app.persistence.schema import EntidadModel, EvidenciaModel, RelacionModel


def serialize_metadata(metadata: dict[str, Any] | None) -> str | None:
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        raise DataMappingError("La metadata debe ser dict o None para persistirse.")
    try:
        return json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise DataMappingError("No se pudo serializar metadata a JSON.") from exc


def deserialize_metadata(metadata_json: str | None) -> dict[str, Any] | None:
    if metadata_json is None:
        return None
    try:
        parsed = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise DataMappingError("La metadata persistida no contiene JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise DataMappingError("La metadata persistida debe deserializar a un diccionario.")
    return parsed


def serialize_temporal(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raise DataMappingError("El valor temporal debe ser date, datetime o None.")


def deserialize_temporal(raw_value: str | None) -> date | datetime | None:
    if raw_value is None:
        return None
    try:
        if "T" in raw_value:
            return datetime.fromisoformat(raw_value)
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise DataMappingError(f"Fecha persistida inválida: {raw_value}.") from exc


def entidad_from_model(model: EntidadModel) -> Entidad:
    if model.tipo_entidad is None:
        raise DataMappingError("La entidad no tiene tipo asociado en la base de datos.")
    try:
        tipo = TipoEntidad(model.tipo_entidad.codigo)
    except ValueError as exc:
        raise DataMappingError(
            f"Código de tipo de entidad inválido en BD: {model.tipo_entidad.codigo}."
        ) from exc

    return Entidad(
        id=model.id,
        tipo=tipo,
        valor=model.valor,
        descripcion=model.descripcion,
        metadata=deserialize_metadata(model.metadata_json),
    )


def evidencia_from_model(model: EvidenciaModel) -> Evidencia:
    return Evidencia(
        id=model.id,
        fuente=model.fuente,
        descripcion=model.descripcion,
        fecha=deserialize_temporal(model.fecha),
    )


def relacion_from_model(model: RelacionModel) -> Relacion:
    if model.tipo_relacion is None:
        raise DataMappingError("La relación no tiene tipo asociado en la base de datos.")
    try:
        tipo = TipoRelacion(model.tipo_relacion.codigo)
    except ValueError as exc:
        raise DataMappingError(
            f"Código de tipo de relación inválido en BD: {model.tipo_relacion.codigo}."
        ) from exc

    ordered_evidence = sorted(model.evidencias, key=lambda item: item.id)
    evidencias = [evidencia_from_model(evidence_model) for evidence_model in ordered_evidence]
    return Relacion(
        id=model.id,
        origen_id=model.origen_id,
        destino_id=model.destino_id,
        tipo=tipo,
        descripcion=model.descripcion,
        fecha=deserialize_temporal(model.fecha),
        evidencias=evidencias,
    )

