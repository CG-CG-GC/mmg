from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from app.domain.tipos import TipoEntidad
from app.persistence.errors import DataMappingError, IntegrityConstraintError
from app.persistence.repositories import EntidadCreateData


def test_crea_entidad_con_id_autogenerado_y_metadata(entidad_repo) -> None:
    created = entidad_repo.create(
        EntidadCreateData(
            tipo=TipoEntidad.EMAIL,
            valor="ana@example.com",
            valor_normalizado="ana@example.com",
            descripcion="Correo principal",
            metadata={"fuente": "manual"},
        )
    )

    assert created.id > 0
    assert created.tipo == TipoEntidad.EMAIL
    assert created.metadata == {"fuente": "manual"}

    fetched = entidad_repo.get_by_id(created.id)
    assert fetched == created


def test_rechaza_duplicados_por_tipo_y_valor_normalizado(entidad_repo) -> None:
    entidad_repo.create(
        EntidadCreateData(
            tipo=TipoEntidad.USUARIO,
            valor="Ana",
            valor_normalizado="ana",
        )
    )

    with pytest.raises(IntegrityConstraintError):
        entidad_repo.create(
            EntidadCreateData(
                tipo=TipoEntidad.USUARIO,
                valor="ANA",
                valor_normalizado="ana",
            )
        )


def test_falla_si_metadata_no_es_json_serializable(entidad_repo) -> None:
    with pytest.raises(DataMappingError):
        entidad_repo.create(
            EntidadCreateData(
                tipo=TipoEntidad.PERSONA,
                valor="Ana Pérez",
                valor_normalizado="ana perez",
                metadata={"invalid": {1, 2, 3}},
            )
        )
