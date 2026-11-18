from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import text

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import session_scope
from app.persistence.errors import (
    DataMappingError,
    IntegrityConstraintError,
    RecordNotFoundError,
    RepositoryError,
    UniqueConstraintError,
)
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.repositories import (
    EntidadCreateData,
    EntidadUpdateData,
    EvidenciaCreateData,
    RelacionCreateData,
)


def _crear(entidad_repo, tipo, valor, normalizado, **extra):
    return entidad_repo.create(
        EntidadCreateData(tipo=tipo, valor=valor, valor_normalizado=normalizado, **extra)
    )


def _normalizado_persistido(session_factory, entity_id: int) -> str:
    with session_scope(session_factory) as session:
        return session.execute(
            text("SELECT valor_normalizado FROM entidad WHERE id = :id"), {"id": entity_id}
        ).scalar_one()


def test_actualiza_entidad_conservando_id_sin_crear_registros(entidad_repo) -> None:
    original = _crear(
        entidad_repo,
        TipoEntidad.PERSONA,
        "Ana",
        "ana",
        descripcion="Analista",
        metadata={"fuente": "manual"},
    )
    otra = _crear(entidad_repo, TipoEntidad.PERSONA, "Beto", "beto")

    actualizada = entidad_repo.update(
        original.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="Ana Pérez",
            valor_normalizado="ana perez",
            descripcion="Analista senior",
            metadata={"fuente": "revisada", "nivel": 2},
        ),
    )

    assert actualizada.id == original.id
    assert actualizada.valor == "Ana Pérez"
    assert actualizada.descripcion == "Analista senior"
    assert actualizada.metadata == {"fuente": "revisada", "nivel": 2}
    assert entidad_repo.get_by_id(original.id) == actualizada
    assert [entidad.id for entidad in entidad_repo.list_all()] == [original.id, otra.id]
    assert entidad_repo.get_by_id(otra.id) == otra


def test_actualiza_tipo_y_vacia_descripcion_y_metadata(entidad_repo) -> None:
    original = _crear(
        entidad_repo,
        TipoEntidad.USUARIO,
        "ana",
        "ana",
        descripcion="Cuenta",
        metadata={"k": "v"},
    )

    actualizada = entidad_repo.update(
        original.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="ana",
            valor_normalizado="ana",
            descripcion=None,
            metadata=None,
        ),
    )

    assert actualizada.id == original.id
    assert actualizada.tipo == TipoEntidad.PERSONA
    assert actualizada.descripcion is None
    assert actualizada.metadata is None
    assert entidad_repo.get_by_id(original.id) == actualizada


def test_persiste_valor_normalizado_recibido_sin_recalcularlo(
    session_factory, entidad_repo
) -> None:
    original = _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")

    entidad_repo.update(
        original.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="  ANA   Pérez ",
            valor_normalizado="valor-definido-por-el-llamador",
        ),
    )

    assert _normalizado_persistido(session_factory, original.id) == "valor-definido-por-el-llamador"


def test_editar_entidad_conserva_relaciones_y_evidencias(
    entidad_repo, relacion_repo, evidencia_repo
) -> None:
    ana = _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")
    empresa = _crear(entidad_repo, TipoEntidad.ORGANIZACION, "Empresa X", "empresa x")
    saliente = relacion_repo.create(
        RelacionCreateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
            descripcion="Relación laboral",
            fecha=date(2026, 1, 15),
        )
    )
    entrante = relacion_repo.create(
        RelacionCreateData(
            origen_id=empresa.id,
            destino_id=ana.id,
            tipo=TipoRelacion.POSEE,
        )
    )
    evidencia_a = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=saliente.id, fuente="Contrato", fecha=date(2026, 1, 20))
    )
    evidencia_b = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=entrante.id, fuente="Registro", descripcion="Acta")
    )
    antes = relacion_repo.list_all()

    entidad_repo.update(
        ana.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="Ana Pérez",
            valor_normalizado="ana perez",
        ),
    )

    assert relacion_repo.list_all() == antes
    assert relacion_repo.get_by_id(saliente.id).evidencias == [evidencia_a]
    assert relacion_repo.get_by_id(entrante.id).evidencias == [evidencia_b]
    assert evidencia_repo.list_by_relation(saliente.id) == [evidencia_a]


def test_actualizar_con_los_mismos_valores_no_genera_conflicto_consigo_misma(
    entidad_repo,
) -> None:
    original = _crear(entidad_repo, TipoEntidad.EMAIL, "ana@example.com", "ana@example.com")

    actualizada = entidad_repo.update(
        original.id,
        EntidadUpdateData(
            tipo=TipoEntidad.EMAIL,
            valor="ana@example.com",
            valor_normalizado="ana@example.com",
        ),
    )

    assert actualizada == original


def test_conflicto_de_unicidad_al_actualizar_es_distinguible_y_no_modifica_datos(
    entidad_repo,
) -> None:
    _crear(entidad_repo, TipoEntidad.USUARIO, "Ana", "ana")
    otra = _crear(entidad_repo, TipoEntidad.USUARIO, "Beto", "beto", descripcion="Original")

    with pytest.raises(UniqueConstraintError) as excinfo:
        entidad_repo.update(
            otra.id,
            EntidadUpdateData(
                tipo=TipoEntidad.USUARIO,
                valor="ANA",
                valor_normalizado="ana",
                descripcion="Cambiada",
            ),
        )

    assert isinstance(excinfo.value, IntegrityConstraintError)
    assert entidad_repo.get_by_id(otra.id) == otra


def test_conflicto_de_unicidad_al_cambiar_solo_el_tipo(entidad_repo) -> None:
    _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")
    usuario = _crear(entidad_repo, TipoEntidad.USUARIO, "ana", "ana")

    with pytest.raises(UniqueConstraintError):
        entidad_repo.update(
            usuario.id,
            EntidadUpdateData(
                tipo=TipoEntidad.PERSONA, valor="ana", valor_normalizado="ana"
            ),
        )

    assert entidad_repo.get_by_id(usuario.id).tipo == TipoEntidad.USUARIO


def test_mismo_valor_normalizado_en_otro_tipo_no_es_conflicto(entidad_repo) -> None:
    _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")
    usuario = _crear(entidad_repo, TipoEntidad.USUARIO, "beto", "beto")

    actualizada = entidad_repo.update(
        usuario.id,
        EntidadUpdateData(tipo=TipoEntidad.USUARIO, valor="ana", valor_normalizado="ana"),
    )

    assert actualizada.id == usuario.id
    assert actualizada.valor == "ana"


def test_rechaza_actualizar_identificador_inexistente(entidad_repo) -> None:
    existente = _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")

    with pytest.raises(RecordNotFoundError) as excinfo:
        entidad_repo.update(
            9999,
            EntidadUpdateData(tipo=TipoEntidad.PERSONA, valor="X", valor_normalizado="x"),
        )

    assert isinstance(excinfo.value, RepositoryError)
    assert [entidad.id for entidad in entidad_repo.list_all()] == [existente.id]
    assert entidad_repo.get_by_id(9999) is None


def test_metadata_no_serializable_en_update_falla_y_no_modifica_la_entidad(entidad_repo) -> None:
    original = _crear(
        entidad_repo, TipoEntidad.PERSONA, "Ana", "ana", metadata={"fuente": "manual"}
    )

    with pytest.raises(DataMappingError):
        entidad_repo.update(
            original.id,
            EntidadUpdateData(
                tipo=TipoEntidad.PERSONA,
                valor="Ana Pérez",
                valor_normalizado="ana perez",
                metadata={"invalid": {1, 2, 3}},
            ),
        )

    assert entidad_repo.get_by_id(original.id) == original


def test_crear_entidad_duplicada_se_reporta_como_conflicto_de_unicidad(entidad_repo) -> None:
    _crear(entidad_repo, TipoEntidad.USUARIO, "Ana", "ana")

    with pytest.raises(UniqueConstraintError):
        _crear(entidad_repo, TipoEntidad.USUARIO, "ANA", "ana")

    # La clase base sigue capturándolo: el contrato previo de creación no cambia.
    with pytest.raises(IntegrityConstraintError):
        _crear(entidad_repo, TipoEntidad.USUARIO, "ANA", "ana")


def test_grafo_reconstruido_refleja_la_edicion_de_entidad(
    session_factory, entidad_repo, relacion_repo, evidencia_repo
) -> None:
    ana = _crear(entidad_repo, TipoEntidad.PERSONA, "Ana", "ana")
    empresa = _crear(entidad_repo, TipoEntidad.ORGANIZACION, "Empresa X", "empresa x")
    relacion = relacion_repo.create(
        RelacionCreateData(
            origen_id=ana.id, destino_id=empresa.id, tipo=TipoRelacion.TRABAJA_EN
        )
    )
    evidencia = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=relacion.id, fuente="Contrato")
    )

    entidad_repo.update(
        ana.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="Ana Pérez",
            valor_normalizado="ana perez",
            descripcion="Editada",
        ),
    )

    graph = load_graph_from_database(session_factory)
    entidad_en_grafo = graph.buscar_entidad(ana.id)
    assert entidad_en_grafo.valor == "Ana Pérez"
    assert entidad_en_grafo.descripcion == "Editada"
    relacion_en_grafo = graph.buscar_relacion(relacion.id)
    assert relacion_en_grafo.origen_id == ana.id
    assert relacion_en_grafo.evidencias == [evidencia]
