from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import inspect, select

from app.persistence.database import session_scope
from app.persistence.schema import TipoEntidadModel, TipoRelacionModel


def test_crea_tablas_y_catalogos_iniciales(session_factory) -> None:
    engine = session_factory.kw["bind"]
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert table_names == {"tipo_entidad", "entidad", "tipo_relacion", "relacion", "evidencia"}

    with session_scope(session_factory) as session:
        entity_type_codes = session.scalars(select(TipoEntidadModel.codigo)).all()
        relation_type_codes = session.scalars(select(TipoRelacionModel.codigo)).all()

    assert sorted(entity_type_codes) == sorted(
        ["PERSONA", "ORGANIZACION", "EMAIL", "USUARIO", "DOMINIO", "SITIO_WEB", "IP"]
    )
    assert sorted(relation_type_codes) == sorted(
        ["POSEE", "UTILIZA", "TRABAJA_EN", "ADMINISTRA", "PERTENECE_A", "APUNTA_A"]
    )
