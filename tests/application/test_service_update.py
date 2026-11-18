from datetime import date

import pytest

from app.application.service import GraphApplicationService
from app.domain.errores import EntidadNoEncontradaError
from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence.database import (
    create_session_factory,
    create_sqlite_engine,
    sqlite_url_from_path,
)
from app.persistence.errors import ForeignKeyConstraintError
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.repositories import (
    EntidadCreateData,
    EntidadRepository,
    EntidadUpdateData,
    EvidenciaCreateData,
    EvidenciaRepository,
    RelacionCreateData,
    RelacionRepository,
    RelacionUpdateData,
)
from app.persistence.schema import initialize_database


@pytest.fixture
def service_context(tmp_path):
    engine = create_sqlite_engine(sqlite_url_from_path(tmp_path / "service-update.sqlite3"))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)
    entidades = EntidadRepository(session_factory)
    relaciones = RelacionRepository(session_factory)
    evidencias = EvidenciaRepository(session_factory)
    service = GraphApplicationService(
        session_factory=session_factory,
        entidad_repository=entidades,
        relacion_repository=relaciones,
        evidencia_repository=evidencias,
        graph_loader=load_graph_from_database,
    )
    yield service, entidades, relaciones, evidencias
    engine.dispose()


def _crear_entidad(service, tipo: TipoEntidad, valor: str):
    return service.crear_entidad(
        EntidadCreateData(tipo=tipo, valor=valor, valor_normalizado=valor.lower())
    )


def test_actualizar_entidad_refresca_grafo_y_conserva_relaciones_y_evidencias(
    service_context,
) -> None:
    service, _, _, _ = service_context
    ana = _crear_entidad(service, TipoEntidad.PERSONA, "Ana")
    empresa = _crear_entidad(service, TipoEntidad.ORGANIZACION, "Empresa X")
    relacion = service.crear_relacion(
        RelacionCreateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
        )
    )
    evidencia = service.crear_evidencia(
        EvidenciaCreateData(relacion_id=relacion.id, fuente="Contrato")
    )

    actualizada = service.actualizar_entidad(
        ana.id,
        EntidadUpdateData(
            tipo=TipoEntidad.PERSONA,
            valor="Ana Pérez",
            valor_normalizado="ana perez",
            descripcion="Actualizada",
        ),
    )

    assert actualizada.id == ana.id
    assert service.graph.buscar_entidad(ana.id).valor == "Ana Pérez"
    relacion_en_grafo = service.graph.buscar_relacion(relacion.id)
    assert relacion_en_grafo.origen_id == ana.id
    assert relacion_en_grafo.evidencias == [evidencia]


def test_actualizar_relacion_refresca_grafo_y_conserva_id_y_evidencias(
    service_context,
) -> None:
    service, _, _, _ = service_context
    ana = _crear_entidad(service, TipoEntidad.PERSONA, "Ana")
    empresa = _crear_entidad(service, TipoEntidad.ORGANIZACION, "Empresa X")
    dominio = _crear_entidad(service, TipoEntidad.DOMINIO, "empresa.test")
    relacion = service.crear_relacion(
        RelacionCreateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
            fecha=date(2026, 10, 31),
        )
    )
    evidencia = service.crear_evidencia(
        EvidenciaCreateData(relacion_id=relacion.id, fuente="Registro")
    )

    actualizada = service.actualizar_relacion(
        relacion.id,
        RelacionUpdateData(
            origen_id=ana.id,
            destino_id=dominio.id,
            tipo=TipoRelacion.UTILIZA,
            descripcion="Editada",
        ),
    )

    assert actualizada.id == relacion.id
    relacion_en_grafo = service.graph.buscar_relacion(relacion.id)
    assert (relacion_en_grafo.origen_id, relacion_en_grafo.destino_id) == (
        ana.id,
        dominio.id,
    )
    assert relacion_en_grafo.tipo == TipoRelacion.UTILIZA
    assert relacion_en_grafo.evidencias == [evidencia]
    assert service.graph.obtener_vecinos(ana.id) == [service.graph.buscar_entidad(dominio.id)]


def test_actualizar_relacion_rechaza_referencia_ausente_antes_de_persistir(
    service_context, monkeypatch
) -> None:
    service, _, relacion_repo, _ = service_context
    ana = _crear_entidad(service, TipoEntidad.PERSONA, "Ana")
    empresa = _crear_entidad(service, TipoEntidad.ORGANIZACION, "Empresa X")
    relacion = service.crear_relacion(
        RelacionCreateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
        )
    )
    update = relacion_repo.update
    calls = []

    def track_update(relation_id, data):
        calls.append((relation_id, data))
        return update(relation_id, data)

    monkeypatch.setattr(relacion_repo, "update", track_update)
    grafo_anterior = service.graph
    with pytest.raises(EntidadNoEncontradaError):
        service.actualizar_relacion(
            relacion.id,
            RelacionUpdateData(
                origen_id=ana.id,
                destino_id=999,
                tipo=TipoRelacion.TRABAJA_EN,
            ),
        )

    assert calls == []
    assert service.graph is grafo_anterior
    assert relacion_repo.get_by_id(relacion.id) == relacion


def test_actualizar_relacion_clasifica_fk_durante_escritura(
    service_context, monkeypatch
) -> None:
    service, _, relacion_repo, _ = service_context
    ana = _crear_entidad(service, TipoEntidad.PERSONA, "Ana")
    empresa = _crear_entidad(service, TipoEntidad.ORGANIZACION, "Empresa X")
    relacion = service.crear_relacion(
        RelacionCreateData(
            origen_id=ana.id,
            destino_id=empresa.id,
            tipo=TipoRelacion.TRABAJA_EN,
        )
    )
    update = relacion_repo.update

    def race_with_missing_reference(relation_id, data):
        raced_data = RelacionUpdateData(
            origen_id=data.origen_id,
            destino_id=999,
            tipo=data.tipo,
            descripcion=data.descripcion,
            fecha=data.fecha,
        )
        return update(relation_id, raced_data)

    monkeypatch.setattr(relacion_repo, "update", race_with_missing_reference)
    grafo_anterior = service.graph

    with pytest.raises(ForeignKeyConstraintError):
        service.actualizar_relacion(
            relacion.id,
            RelacionUpdateData(
                origen_id=ana.id,
                destino_id=empresa.id,
                tipo=TipoRelacion.UTILIZA,
            ),
        )

    assert service.graph is grafo_anterior
    assert relacion_repo.get_by_id(relacion.id) == relacion
