from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.domain.entidad import Entidad
from app.domain.evidencia import Evidencia
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import session_scope
from app.persistence.errors import DataMappingError, IntegrityConstraintError, RepositoryError
from app.persistence.mappers import (
    entidad_from_model,
    evidencia_from_model,
    relacion_from_model,
    serialize_metadata,
    serialize_temporal,
)
from app.persistence.schema import (
    EntidadModel,
    EvidenciaModel,
    RelacionModel,
    TipoEntidadModel,
    TipoRelacionModel,
)


@dataclass(slots=True)
class EntidadCreateData:
    tipo: TipoEntidad
    valor: str
    valor_normalizado: str
    descripcion: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class RelacionCreateData:
    origen_id: int
    destino_id: int
    tipo: TipoRelacion
    descripcion: str | None = None
    fecha: date | datetime | None = None


@dataclass(slots=True)
class EvidenciaCreateData:
    relacion_id: int
    fuente: str
    descripcion: str | None = None
    fecha: date | datetime | None = None


class EntidadRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, data: EntidadCreateData) -> Entidad:
        try:
            with session_scope(self._session_factory) as session:
                tipo_entidad_id = _resolve_entity_type_id(session, data.tipo)
                model = EntidadModel(
                    tipo_entidad_id=tipo_entidad_id,
                    valor=data.valor,
                    valor_normalizado=data.valor_normalizado,
                    descripcion=data.descripcion,
                    metadata_json=serialize_metadata(data.metadata),
                )
                session.add(model)
                session.flush()
                session.refresh(model, attribute_names=["tipo_entidad"])
                return entidad_from_model(model)
        except DataMappingError:
            raise
        except IntegrityError as exc:
            raise IntegrityConstraintError(
                "No se pudo crear la entidad por una restricción de integridad."
            ) from exc
        except SQLAlchemyError as exc:
            raise RepositoryError("No se pudo crear la entidad en persistencia.") from exc

    def get_by_id(self, entity_id: int) -> Entidad | None:
        try:
            with session_scope(self._session_factory) as session:
                stmt = (
                    select(EntidadModel)
                    .options(joinedload(EntidadModel.tipo_entidad))
                    .where(EntidadModel.id == entity_id)
                )
                model = session.scalar(stmt)
                if model is None:
                    return None
                return entidad_from_model(model)
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError(f"No se pudo obtener la entidad con id {entity_id}.") from exc

    def list_all(self) -> list[Entidad]:
        try:
            with session_scope(self._session_factory) as session:
                stmt = select(EntidadModel).options(joinedload(EntidadModel.tipo_entidad)).order_by(
                    EntidadModel.id
                )
                return [entidad_from_model(model) for model in session.scalars(stmt).all()]
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError("No se pudieron listar las entidades.") from exc

    def delete_by_id(self, entity_id: int) -> bool:
        try:
            with session_scope(self._session_factory) as session:
                model = session.get(EntidadModel, entity_id)
                if model is None:
                    return False
                session.delete(model)
                session.flush()
                return True
        except SQLAlchemyError as exc:
            raise RepositoryError(f"No se pudo eliminar la entidad con id {entity_id}.") from exc


class RelacionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, data: RelacionCreateData) -> Relacion:
        try:
            with session_scope(self._session_factory) as session:
                tipo_relacion_id = _resolve_relation_type_id(session, data.tipo)
                model = RelacionModel(
                    origen_id=data.origen_id,
                    destino_id=data.destino_id,
                    tipo_relacion_id=tipo_relacion_id,
                    descripcion=data.descripcion,
                    fecha=serialize_temporal(data.fecha),
                )
                session.add(model)
                session.flush()
                session.refresh(model, attribute_names=["tipo_relacion", "evidencias"])
                return relacion_from_model(model)
        except DataMappingError:
            raise
        except IntegrityError as exc:
            raise IntegrityConstraintError(
                "No se pudo crear la relación por una restricción de integridad."
            ) from exc
        except SQLAlchemyError as exc:
            raise RepositoryError("No se pudo crear la relación en persistencia.") from exc

    def get_by_id(self, relation_id: int) -> Relacion | None:
        try:
            with session_scope(self._session_factory) as session:
                stmt = (
                    select(RelacionModel)
                    .options(
                        joinedload(RelacionModel.tipo_relacion),
                        selectinload(RelacionModel.evidencias),
                    )
                    .where(RelacionModel.id == relation_id)
                )
                model = session.scalar(stmt)
                if model is None:
                    return None
                return relacion_from_model(model)
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError(f"No se pudo obtener la relación con id {relation_id}.") from exc

    def list_all(self) -> list[Relacion]:
        try:
            with session_scope(self._session_factory) as session:
                stmt = (
                    select(RelacionModel)
                    .options(
                        joinedload(RelacionModel.tipo_relacion),
                        selectinload(RelacionModel.evidencias),
                    )
                    .order_by(RelacionModel.id)
                )
                return [relacion_from_model(model) for model in session.scalars(stmt).all()]
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError("No se pudieron listar las relaciones.") from exc

    def list_by_origen(self, origin_entity_id: int) -> list[Relacion]:
        try:
            with session_scope(self._session_factory) as session:
                stmt = (
                    select(RelacionModel)
                    .options(
                        joinedload(RelacionModel.tipo_relacion),
                        selectinload(RelacionModel.evidencias),
                    )
                    .where(RelacionModel.origen_id == origin_entity_id)
                    .order_by(RelacionModel.id)
                )
                return [relacion_from_model(model) for model in session.scalars(stmt).all()]
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError(
                f"No se pudieron listar las relaciones del origen {origin_entity_id}."
            ) from exc

    def delete_by_id(self, relation_id: int) -> bool:
        try:
            with session_scope(self._session_factory) as session:
                model = session.get(RelacionModel, relation_id)
                if model is None:
                    return False
                session.delete(model)
                session.flush()
                return True
        except SQLAlchemyError as exc:
            raise RepositoryError(f"No se pudo eliminar la relación con id {relation_id}.") from exc


class EvidenciaRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, data: EvidenciaCreateData) -> Evidencia:
        try:
            with session_scope(self._session_factory) as session:
                model = EvidenciaModel(
                    relacion_id=data.relacion_id,
                    fuente=data.fuente,
                    descripcion=data.descripcion,
                    fecha=serialize_temporal(data.fecha),
                )
                session.add(model)
                session.flush()
                return evidencia_from_model(model)
        except DataMappingError:
            raise
        except IntegrityError as exc:
            raise IntegrityConstraintError(
                "No se pudo crear la evidencia por una restricción de integridad."
            ) from exc
        except SQLAlchemyError as exc:
            raise RepositoryError("No se pudo crear la evidencia en persistencia.") from exc

    def list_by_relation(self, relation_id: int) -> list[Evidencia]:
        try:
            with session_scope(self._session_factory) as session:
                stmt = (
                    select(EvidenciaModel)
                    .where(EvidenciaModel.relacion_id == relation_id)
                    .order_by(EvidenciaModel.id)
                )
                return [evidencia_from_model(model) for model in session.scalars(stmt).all()]
        except (SQLAlchemyError, DataMappingError) as exc:
            raise RepositoryError(
                f"No se pudieron listar las evidencias de la relación {relation_id}."
            ) from exc

    def delete_by_id(self, evidence_id: int) -> bool:
        try:
            with session_scope(self._session_factory) as session:
                model = session.get(EvidenciaModel, evidence_id)
                if model is None:
                    return False
                session.delete(model)
                session.flush()
                return True
        except SQLAlchemyError as exc:
            raise RepositoryError(f"No se pudo eliminar la evidencia con id {evidence_id}.") from exc


def _resolve_entity_type_id(session: Session, entity_type: TipoEntidad) -> int:
    stmt = select(TipoEntidadModel.id).where(TipoEntidadModel.codigo == entity_type.value)
    type_id = session.scalar(stmt)
    if type_id is None:
        raise RepositoryError(
            f"No existe el tipo de entidad {entity_type.value} en los catálogos persistidos."
        )
    return type_id


def _resolve_relation_type_id(session: Session, relation_type: TipoRelacion) -> int:
    stmt = select(TipoRelacionModel.id).where(TipoRelacionModel.codigo == relation_type.value)
    type_id = session.scalar(stmt)
    if type_id is None:
        raise RepositoryError(
            f"No existe el tipo de relación {relation_type.value} en los catálogos persistidos."
        )
    return type_id
