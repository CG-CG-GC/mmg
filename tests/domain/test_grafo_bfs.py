import pytest

from app.domain.entidad import Entidad
from app.domain.errores import EntidadNoEncontradaError
from app.domain.grafo import Graph
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion


def _entidad(entity_id: int) -> Entidad:
    return Entidad(id=entity_id, tipo=TipoEntidad.USUARIO, valor=f"user-{entity_id}")


def test_bfs_nodo_unico() -> None:
    grafo = Graph()
    grafo.agregar_entidad(_entidad(1))

    resultado = grafo.bfs(1)
    assert resultado.orden_recorrido == [1]
    assert resultado.niveles == {1: 0}
    assert resultado.predecesores == {1: None}


def test_bfs_camino_simple_y_predecesores() -> None:
    grafo = Graph()
    for i in [1, 2, 3]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=11, origen_id=2, destino_id=3, tipo=TipoRelacion.UTILIZA))

    resultado = grafo.bfs(1)
    assert resultado.orden_recorrido == [1, 2, 3]
    assert resultado.niveles == {1: 0, 2: 1, 3: 2}
    assert resultado.predecesores == {1: None, 2: 1, 3: 2}


def test_bfs_con_ramas_y_ciclo() -> None:
    grafo = Graph()
    for i in [1, 2, 3, 4]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=11, origen_id=1, destino_id=3, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=12, origen_id=2, destino_id=4, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=13, origen_id=4, destino_id=1, tipo=TipoRelacion.UTILIZA))

    resultado = grafo.bfs(1)
    assert resultado.orden_recorrido == [1, 2, 3, 4]
    assert resultado.niveles[1] == 0
    assert resultado.niveles[2] == 1
    assert resultado.niveles[3] == 1
    assert resultado.niveles[4] == 2


def test_bfs_nodo_aislado_y_grafo_desconectado() -> None:
    grafo = Graph()
    for i in [1, 2, 3, 4]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=11, origen_id=3, destino_id=4, tipo=TipoRelacion.UTILIZA))

    resultado_1 = grafo.bfs(1)
    assert resultado_1.orden_recorrido == [1, 2]

    resultado_3 = grafo.bfs(3)
    assert resultado_3.orden_recorrido == [3, 4]

    resultado_aislado = grafo.bfs(4)
    assert resultado_aislado.orden_recorrido == [4]


def test_bfs_origen_inexistente() -> None:
    grafo = Graph()
    with pytest.raises(EntidadNoEncontradaError):
        grafo.bfs(999)
