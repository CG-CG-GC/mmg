import inspect

import pytest

from app.domain.entidad import Entidad
from app.domain.errores import EntidadNoEncontradaError
from app.domain.grafo import Graph
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion


def _entidad(entity_id: int) -> Entidad:
    return Entidad(id=entity_id, tipo=TipoEntidad.USUARIO, valor=f"user-{entity_id}")


def test_dfs_nodo_unico() -> None:
    grafo = Graph()
    grafo.agregar_entidad(_entidad(1))
    resultado = grafo.dfs(1)
    assert resultado.orden_recorrido == [1]


def test_dfs_camino_simple() -> None:
    grafo = Graph()
    for i in [1, 2, 3]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=11, origen_id=2, destino_id=3, tipo=TipoRelacion.UTILIZA))

    resultado = grafo.dfs(1)
    assert resultado.orden_recorrido == [1, 2, 3]


def test_dfs_ramas_y_ciclo() -> None:
    grafo = Graph()
    for i in [1, 2, 3, 4]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=11, origen_id=1, destino_id=3, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=12, origen_id=2, destino_id=4, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=13, origen_id=4, destino_id=1, tipo=TipoRelacion.UTILIZA))

    resultado = grafo.dfs(1)
    assert resultado.orden_recorrido == [1, 2, 4, 3]


def test_dfs_nodo_aislado() -> None:
    grafo = Graph()
    for i in [1, 2]:
        grafo.agregar_entidad(_entidad(i))
    resultado = grafo.dfs(2)
    assert resultado.orden_recorrido == [2]


def test_dfs_origen_inexistente() -> None:
    grafo = Graph()
    with pytest.raises(EntidadNoEncontradaError):
        grafo.dfs(999)


def test_dfs_es_recursivo_en_la_implementacion() -> None:
    source = inspect.getsource(Graph.dfs)
    assert "def visitar" in source
    assert "visitar(vecino_id)" in source
