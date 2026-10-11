from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import text

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import session_scope
from app.persistence.errors import GraphReconstructionError
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.repositories import EvidenciaCreateData, EntidadCreateData, RelacionCreateData


def test_reconstruye_grafo_preservando_datos(
    session_factory,
    entidad_repo,
    relacion_repo,
    evidencia_repo,
) -> None:
    persona = entidad_repo.create(
        EntidadCreateData(
            tipo=TipoEntidad.PERSONA,
            valor="Ana Pérez",
            valor_normalizado="ana perez",
            descripcion="Analista",
            metadata={"origen": "manual"},
        )
    )
    email = entidad_repo.create(
        EntidadCreateData(
            tipo=TipoEntidad.EMAIL,
            valor="ana@example.com",
            valor_normalizado="ana@example.com",
            descripcion="Email principal",
        )
    )
    relacion = relacion_repo.create(
        RelacionCreateData(
            origen_id=persona.id,
            destino_id=email.id,
            tipo=TipoRelacion.POSEE,
            descripcion="Posee correo",
            fecha=date(2026, 10, 10),
        )
    )
    evidencia = evidencia_repo.create(
        EvidenciaCreateData(
            relacion_id=relacion.id,
            fuente="https://fuente.test",
            descripcion="Captura",
            fecha=date(2026, 10, 10),
        )
    )

    graph = load_graph_from_database(session_factory)

    loaded_persona = graph.buscar_entidad(persona.id)
    assert loaded_persona is not None
    assert loaded_persona.id == persona.id
    assert loaded_persona.tipo == TipoEntidad.PERSONA
    assert loaded_persona.descripcion == "Analista"
    assert loaded_persona.metadata == {"origen": "manual"}

    loaded_relacion = graph.buscar_relacion(relacion.id)
    assert loaded_relacion is not None
    assert loaded_relacion.id == relacion.id
    assert loaded_relacion.origen_id == persona.id
    assert loaded_relacion.destino_id == email.id
    assert loaded_relacion.tipo == TipoRelacion.POSEE
    assert loaded_relacion.descripcion == "Posee correo"
    assert loaded_relacion.fecha == date(2026, 10, 10)
    assert len(loaded_relacion.evidencias) == 1
    assert loaded_relacion.evidencias[0].id == evidencia.id
    assert loaded_relacion.evidencias[0].fuente == "https://fuente.test"


def test_falla_si_hay_inconsistencia_y_no_devuelve_grafo_parcial(
    session_factory,
    entidad_repo,
) -> None:
    origen = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.USUARIO, valor="u1", valor_normalizado="u1")
    )
    destino = entidad_repo.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="d1.test", valor_normalizado="d1.test")
    )

    with session_scope(session_factory) as session:
        session.execute(text("PRAGMA foreign_keys=OFF"))
        session.execute(
            text(
                """
                INSERT INTO relacion (origen_id, destino_id, tipo_relacion_id, descripcion, fecha)
                VALUES (:origen_id, :destino_id, :tipo_relacion_id, :descripcion, :fecha)
                """
            ),
            {
                "origen_id": origen.id,
                "destino_id": destino.id,
                "tipo_relacion_id": 999999,
                "descripcion": "inconsistente",
                "fecha": None,
            },
        )
        session.execute(text("PRAGMA foreign_keys=ON"))

    with pytest.raises(GraphReconstructionError):
        load_graph_from_database(session_factory)
