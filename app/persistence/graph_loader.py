from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.domain.errores import ErrorDominio
from app.domain.grafo import Graph
from app.persistence.database import session_scope
from app.persistence.errors import DataMappingError, GraphReconstructionError
from app.persistence.mappers import entidad_from_model, relacion_from_model
from app.persistence.schema import EntidadModel, RelacionModel


def load_graph_from_database(session_factory: sessionmaker[Session]) -> Graph:
    graph = Graph()
    try:
        with session_scope(session_factory) as session:
            _load_entities(session, graph)
            _load_relations(session, graph)
    except (SQLAlchemyError, DataMappingError, ErrorDominio) as exc:
        raise GraphReconstructionError(
            "No se pudo reconstruir un grafo consistente desde persistencia."
        ) from exc
    return graph


def _load_entities(session: Session, graph: Graph) -> None:
    stmt = select(EntidadModel).options(joinedload(EntidadModel.tipo_entidad)).order_by(EntidadModel.id)
    for model in session.scalars(stmt).all():
        graph.agregar_entidad(entidad_from_model(model))


def _load_relations(session: Session, graph: Graph) -> None:
    stmt = (
        select(RelacionModel)
        .options(
            joinedload(RelacionModel.tipo_relacion),
            selectinload(RelacionModel.evidencias),
        )
        .order_by(RelacionModel.id)
    )
    for model in session.scalars(stmt).all():
        graph.agregar_relacion(relacion_from_model(model))

