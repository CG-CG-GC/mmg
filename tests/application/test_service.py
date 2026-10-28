from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.errors import GraphUnavailableError
from app.application.service import GraphApplicationService


@dataclass
class FakeGraph:
    generation: int


class FakeRepository:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def create(self, data):
        self.calls.append(("create", data))
        return self.result if self.result is not None else data

    def delete_by_id(self, item_id):
        self.calls.append(("delete", item_id))
        return True


def build_service(loader=None):
    state = {"generation": 0, "fail": False}

    def default_loader(_factory):
        if state["fail"]:
            raise RuntimeError("fallo simulado de reconstrucción")
        return FakeGraph(state["generation"])

    loader = loader or default_loader
    entidades, relaciones, evidencias = FakeRepository(), FakeRepository(), FakeRepository()
    service = GraphApplicationService(
        session_factory=object(),
        entidad_repository=entidades,
        relacion_repository=relaciones,
        evidencia_repository=evidencias,
        graph_loader=loader,
    )
    return service, state, entidades, relaciones, evidencias


def test_inicializa_grafo_desde_el_cargador():
    service, _, *_ = build_service()
    assert service.graph == FakeGraph(0)


def test_publica_grafo_nuevo_solo_despues_de_reconstruccion():
    service, state, entidades, *_ = build_service()
    state["generation"] = 1
    result = service.crear_entidad({"valor": "Ana"})
    assert result == {"valor": "Ana"}
    assert entidades.calls == [("create", {"valor": "Ana"})]
    assert service.graph == FakeGraph(1)


def test_no_cambia_el_grafo_publicado_si_la_escritura_falla():
    service, _, entidades, *_ = build_service()

    def fail_create(_data):
        raise RuntimeError("fallo de persistencia")

    entidades.create = fail_create
    with pytest.raises(RuntimeError, match="fallo de persistencia"):
        service.crear_entidad({"valor": "Ana"})
    assert service.graph == FakeGraph(0)


def test_invalida_grafo_si_falla_la_reconstruccion_despues_de_escribir():
    service, state, *_ = build_service()
    state["fail"] = True
    with pytest.raises(RuntimeError, match="reconstrucción"):
        service.crear_entidad({"valor": "Ana"})
    with pytest.raises(GraphUnavailableError):
        _ = service.graph


def test_no_permite_escrituras_mientras_el_grafo_este_invalidado():
    service, state, *_ = build_service()
    state["fail"] = True
    with pytest.raises(RuntimeError):
        service.crear_entidad({"valor": "Ana"})
    with pytest.raises(GraphUnavailableError):
        service.crear_entidad({"valor": "Bea"})


def test_reconstruccion_manual_recupera_el_servicio():
    service, state, *_ = build_service()
    state["fail"] = True
    with pytest.raises(RuntimeError):
        service.reconstruir_grafo()
    state["fail"] = False
    state["generation"] = 2
    assert service.reconstruir_grafo() == FakeGraph(2)
    assert service.graph == FakeGraph(2)


def test_no_reconstruye_si_eliminacion_no_encuentra_registro():
    service, state, entidades, *_ = build_service()
    entidades.delete_by_id = lambda _id: False
    assert service.eliminar_entidad(42) is False
    assert service.graph == FakeGraph(0)
    assert state["generation"] == 0
