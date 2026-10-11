from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("sqlalchemy")

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.errors import IntegrityConstraintError
from app.persistence.repositories import EntidadCreateData, RelacionCreateData


def test_crea_relacion_con_id_autogenerado(relacion_repo, entidad_repo) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor="Ana", valor_normalizado="ana")
    )
    destino = entidad_repo.create(
        EntidadCreateData(
            tipo=TipoEntidad.ORGANIZACION,
            valor="Empresa X",
            valor_normalizado="empresa x",
        )
    )

    relacion = relacion_repo.create(
        RelacionCreateData(
            origen_id=origen.id,
            destino_id=destino.id,
            tipo=TipoRelacion.TRABAJA_EN,
            descripcion="Relación laboral",
            fecha=date(2026, 10, 10),
        )
    )

    assert relacion.id > 0
    assert relacion.origen_id == origen.id
    assert relacion.destino_id == destino.id
    assert relacion.tipo == TipoRelacion.TRABAJA_EN
    assert relacion.fecha == date(2026, 10, 10)


def test_rechaza_relacion_duplicada_por_origen_destino_tipo(relacion_repo, entidad_repo) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor="Ana", valor_normalizado="ana")
    )
    destino = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.EMAIL, valor="ana@example.com", valor_normalizado="ana@example.com")
    )

    relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.POSEE)
    )

    with pytest.raises(IntegrityConstraintError):
        relacion_repo.create(
            RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.POSEE)
        )


def test_permite_relaciones_paralelas_de_distinto_tipo(relacion_repo, entidad_repo) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.USUARIO, valor="ana_usr", valor_normalizado="ana_usr")
    )
    destino = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="example.com", valor_normalizado="example.com")
    )

    first = relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.UTILIZA)
    )
    second = relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.ADMINISTRA)
    )

    assert first.id != second.id
    assert {first.tipo, second.tipo} == {TipoRelacion.UTILIZA, TipoRelacion.ADMINISTRA}


def test_rechaza_fk_inexistente(relacion_repo, entidad_repo) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="10.0.0.10", valor_normalizado="10.0.0.10")
    )
    with pytest.raises(IntegrityConstraintError):
        relacion_repo.create(
            RelacionCreateData(origen_id=origen.id, destino_id=999999, tipo=TipoRelacion.APUNTA_A)
        )
