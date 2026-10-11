from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import text

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import session_scope
from app.persistence.repositories import EvidenciaCreateData, EntidadCreateData, RelacionCreateData


def test_foreign_keys_habilitadas_en_conexion_sqlite(session_factory) -> None:
    with session_scope(session_factory) as session:
        value = session.execute(text("PRAGMA foreign_keys")).scalar_one()
    assert int(value) == 1


def test_eliminar_entidad_elimina_relaciones_entrantes_y_salientes_y_evidencias(
    entidad_repo,
    relacion_repo,
    evidencia_repo,
) -> None:
    centro = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor="Centro", valor_normalizado="centro")
    )
    source = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.USUARIO, valor="Source", valor_normalizado="source")
    )
    target = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="Target", valor_normalizado="target")
    )

    outgoing = relacion_repo.create(
        RelacionCreateData(origen_id=centro.id, destino_id=target.id, tipo=TipoRelacion.UTILIZA)
    )
    incoming = relacion_repo.create(
        RelacionCreateData(origen_id=source.id, destino_id=centro.id, tipo=TipoRelacion.PERTENECE_A)
    )

    evidencia_repo.create(EvidenciaCreateData(relacion_id=outgoing.id, fuente="outgoing-e1"))
    evidencia_repo.create(EvidenciaCreateData(relacion_id=incoming.id, fuente="incoming-e1"))

    deleted = entidad_repo.delete_by_id(centro.id)
    assert deleted is True

    assert relacion_repo.get_by_id(outgoing.id) is None
    assert relacion_repo.get_by_id(incoming.id) is None
    assert evidencia_repo.list_by_relation(outgoing.id) == []
    assert evidencia_repo.list_by_relation(incoming.id) == []
