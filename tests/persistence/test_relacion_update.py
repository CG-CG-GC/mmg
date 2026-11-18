from __future__ import annotations

from datetime import date, datetime

import pytest

pytest.importorskip("sqlalchemy")

from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.errors import (
    IntegrityConstraintError,
    RecordNotFoundError,
    RepositoryError,
    UniqueConstraintError,
)
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.repositories import (
    EntidadCreateData,
    EvidenciaCreateData,
    RelacionCreateData,
    RelacionUpdateData,
)


@pytest.fixture
def entidades(entidad_repo):
    def crear(tipo, valor):
        return entidad_repo.create(
            EntidadCreateData(tipo=tipo, valor=valor, valor_normalizado=valor.lower())
        )

    return (
        crear(TipoEntidad.PERSONA, "Ana"),
        crear(TipoEntidad.ORGANIZACION, "Empresa X"),
        crear(TipoEntidad.DOMINIO, "empresa-x.com"),
    )


def _crear(relacion_repo, origen, destino, tipo, **extra):
    return relacion_repo.create(
        RelacionCreateData(origen_id=origen.id, destino_id=destino.id, tipo=tipo, **extra)
    )


def test_actualiza_relacion_conservando_id_y_evidencias(
    entidades, relacion_repo, evidencia_repo
) -> None:
    ana, empresa, _ = entidades
    original = _crear(
        relacion_repo,
        ana,
        empresa,
        TipoRelacion.TRABAJA_EN,
        descripcion="Inicial",
        fecha=date(2026, 1, 1),
    )
    otra = _crear(relacion_repo, empresa, ana, TipoRelacion.POSEE)
    evidencia_a = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=original.id, fuente="Contrato", fecha=date(2026, 1, 5))
    )
    evidencia_b = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=original.id, fuente="Registro", descripcion="Acta")
    )

    actualizada = relacion_repo.update(
        original.id,
        RelacionUpdateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.ADMINISTRA,
            descripcion="Corregida",
            fecha=datetime(2026, 2, 3, 10, 30),
        ),
    )

    assert actualizada.id == original.id
    assert actualizada.tipo == TipoRelacion.ADMINISTRA
    assert actualizada.descripcion == "Corregida"
    assert actualizada.fecha == datetime(2026, 2, 3, 10, 30)
    assert actualizada.evidencias == [evidencia_a, evidencia_b]
    assert relacion_repo.get_by_id(original.id) == actualizada
    assert evidencia_repo.list_by_relation(original.id) == [evidencia_a, evidencia_b]
    assert [relacion.id for relacion in relacion_repo.list_all()] == [original.id, otra.id]
    assert relacion_repo.get_by_id(otra.id) == otra


def test_actualiza_origen_y_destino_conservando_evidencias(
    entidades, relacion_repo, evidencia_repo
) -> None:
    ana, empresa, dominio = entidades
    original = _crear(relacion_repo, ana, empresa, TipoRelacion.UTILIZA)
    evidencia = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=original.id, fuente="Captura")
    )

    actualizada = relacion_repo.update(
        original.id,
        RelacionUpdateData(
            origen_id=empresa.id, destino_id=dominio.id, tipo=TipoRelacion.UTILIZA
        ),
    )

    assert actualizada.id == original.id
    assert (actualizada.origen_id, actualizada.destino_id) == (empresa.id, dominio.id)
    assert actualizada.evidencias == [evidencia]
    assert relacion_repo.list_by_origen(ana.id) == []
    assert [relacion.id for relacion in relacion_repo.list_by_origen(empresa.id)] == [original.id]


def test_actualiza_fecha_y_descripcion_a_none(entidades, relacion_repo) -> None:
    ana, empresa, _ = entidades
    original = _crear(
        relacion_repo,
        ana,
        empresa,
        TipoRelacion.TRABAJA_EN,
        descripcion="Algo",
        fecha=date(2026, 1, 1),
    )

    actualizada = relacion_repo.update(
        original.id,
        RelacionUpdateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
            descripcion=None,
            fecha=None,
        ),
    )

    assert actualizada.descripcion is None
    assert actualizada.fecha is None
    assert relacion_repo.get_by_id(original.id) == actualizada


def test_actualizar_con_los_mismos_valores_no_genera_conflicto_consigo_misma(
    entidades, relacion_repo
) -> None:
    ana, empresa, _ = entidades
    original = _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)

    actualizada = relacion_repo.update(
        original.id,
        RelacionUpdateData(
            origen_id=ana.id, destino_id=empresa.id, tipo=TipoRelacion.TRABAJA_EN
        ),
    )

    assert actualizada == original


def test_conflicto_de_unicidad_por_tipo_es_distinguible_y_no_modifica_datos(
    entidades, relacion_repo, evidencia_repo
) -> None:
    ana, empresa, _ = entidades
    _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)
    otra = _crear(relacion_repo, ana, empresa, TipoRelacion.UTILIZA, descripcion="Original")
    evidencia = evidencia_repo.create(EvidenciaCreateData(relacion_id=otra.id, fuente="Fuente"))
    antes = relacion_repo.get_by_id(otra.id)
    assert antes.evidencias == [evidencia]

    with pytest.raises(UniqueConstraintError) as excinfo:
        relacion_repo.update(
            otra.id,
            RelacionUpdateData(
                origen_id=ana.id,
                destino_id=empresa.id,
                tipo=TipoRelacion.TRABAJA_EN,
                descripcion="Cambiada",
            ),
        )

    assert isinstance(excinfo.value, IntegrityConstraintError)
    assert relacion_repo.get_by_id(otra.id) == antes


def test_conflicto_de_unicidad_al_cambiar_destino(entidades, relacion_repo) -> None:
    ana, empresa, dominio = entidades
    _crear(relacion_repo, ana, empresa, TipoRelacion.UTILIZA)
    otra = _crear(relacion_repo, ana, dominio, TipoRelacion.UTILIZA)

    with pytest.raises(UniqueConstraintError):
        relacion_repo.update(
            otra.id,
            RelacionUpdateData(
                origen_id=ana.id, destino_id=empresa.id, tipo=TipoRelacion.UTILIZA
            ),
        )

    assert relacion_repo.get_by_id(otra.id) == otra


def test_rechaza_actualizar_identificador_inexistente(entidades, relacion_repo) -> None:
    ana, empresa, _ = entidades
    existente = _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)

    with pytest.raises(RecordNotFoundError) as excinfo:
        relacion_repo.update(
            9999,
            RelacionUpdateData(
                origen_id=ana.id, destino_id=empresa.id, tipo=TipoRelacion.POSEE
            ),
        )

    assert isinstance(excinfo.value, RepositoryError)
    assert [relacion.id for relacion in relacion_repo.list_all()] == [existente.id]


def test_entidad_inexistente_es_violacion_de_integridad_pero_no_de_unicidad(
    entidades, relacion_repo, evidencia_repo
) -> None:
    ana, empresa, _ = entidades
    original = _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)
    evidencia = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=original.id, fuente="Fuente")
    )
    antes = relacion_repo.get_by_id(original.id)
    assert antes.evidencias == [evidencia]

    with pytest.raises(IntegrityConstraintError) as excinfo:
        relacion_repo.update(
            original.id,
            RelacionUpdateData(
                origen_id=ana.id, destino_id=9999, tipo=TipoRelacion.TRABAJA_EN
            ),
        )

    assert not isinstance(excinfo.value, UniqueConstraintError)
    assert relacion_repo.get_by_id(original.id) == antes


def test_crear_relacion_duplicada_se_reporta_como_conflicto_de_unicidad(
    entidades, relacion_repo
) -> None:
    ana, empresa, _ = entidades
    _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)

    with pytest.raises(UniqueConstraintError):
        _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)

    # La clase base sigue capturándolo: el contrato previo de creación no cambia.
    with pytest.raises(IntegrityConstraintError):
        _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)


def test_crear_relacion_con_entidad_inexistente_no_es_conflicto_de_unicidad(
    entidades, relacion_repo
) -> None:
    ana, _, _ = entidades

    with pytest.raises(IntegrityConstraintError) as excinfo:
        relacion_repo.create(
            RelacionCreateData(origen_id=ana.id, destino_id=9999, tipo=TipoRelacion.POSEE)
        )

    assert not isinstance(excinfo.value, UniqueConstraintError)


def test_grafo_reconstruido_refleja_la_edicion_de_relacion(
    session_factory, entidades, relacion_repo, evidencia_repo
) -> None:
    ana, empresa, dominio = entidades
    original = _crear(relacion_repo, ana, empresa, TipoRelacion.TRABAJA_EN)
    evidencia = evidencia_repo.create(
        EvidenciaCreateData(relacion_id=original.id, fuente="Contrato")
    )

    relacion_repo.update(
        original.id,
        RelacionUpdateData(
            origen_id=ana.id,
            destino_id=dominio.id,
            tipo=TipoRelacion.UTILIZA,
            descripcion="Editada",
        ),
    )

    graph = load_graph_from_database(session_factory)
    en_grafo = graph.buscar_relacion(original.id)
    assert (en_grafo.origen_id, en_grafo.destino_id) == (ana.id, dominio.id)
    assert en_grafo.tipo == TipoRelacion.UTILIZA
    assert en_grafo.descripcion == "Editada"
    assert en_grafo.evidencias == [evidencia]
