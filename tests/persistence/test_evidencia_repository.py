from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("sqlalchemy")

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.repositories import EvidenciaCreateData, EntidadCreateData, RelacionCreateData


def test_crea_evidencia_con_id_autogenerado(evidencia_repo, relacion_repo, entidad_repo) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor="Ana", valor_normalizado="ana")
    )
    destino = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.EMAIL, valor="ana@example.com", valor_normalizado="ana@example.com")
    )
    relacion = relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.POSEE)
    )

    evidencia = evidencia_repo.create(
        EvidenciaCreateData(
            relacion_id=relacion.id,
            fuente="https://ejemplo.test",
            descripcion="Fuente verificada",
            fecha=datetime(2026, 10, 10, 12, 30, 45),
        )
    )

    assert evidencia.id > 0
    assert evidencia.fuente == "https://ejemplo.test"
    assert evidencia.fecha == datetime(2026, 10, 10, 12, 30, 45)
    assert [item.id for item in evidencia_repo.list_by_relation(relacion.id)] == [evidencia.id]


def test_eliminar_relacion_elimina_evidencias_en_cascada(
    evidencia_repo,
    relacion_repo,
    entidad_repo,
) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.USUARIO, valor="user-a", valor_normalizado="user-a")
    )
    destino = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.SITIO_WEB, valor="site.test", valor_normalizado="site.test")
    )
    relacion = relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=TipoRelacion.UTILIZA)
    )

    evidencia_repo.create(EvidenciaCreateData(relacion_id=relacion.id, fuente="fuente-1"))
    evidencia_repo.create(EvidenciaCreateData(relacion_id=relacion.id, fuente="fuente-2"))

    deleted = relacion_repo.delete_by_id(relacion.id)
    assert deleted is True
    assert evidencia_repo.list_by_relation(relacion.id) == []
