import pytest

from app.domain.entidad import Entidad
from app.domain.errores import EntidadNoEncontradaError
from app.domain.grafo import Graph
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion


def _entidad(entity_id: int) -> Entidad:
    return Entidad(id=entity_id, tipo=TipoEntidad.DOMINIO, valor=f"d-{entity_id}.test")


def test_camino_existente() -> None:
    grafo = Graph()
    for i in [1, 2, 3]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.APUNTA_A))
    grafo.agregar_relacion(Relacion(id=11, origen_id=2, destino_id=3, tipo=TipoRelacion.APUNTA_A))

    resultado = grafo.buscar_camino(1, 3)
    assert resultado.encontrado is True
    assert resultado.entidades_camino == [1, 2, 3]
    assert resultado.relaciones_camino == [10, 11]


def test_camino_inexistente_y_respetando_direccion() -> None:
    grafo = Graph()
    for i in [1, 2]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.APUNTA_A))

    resultado = grafo.buscar_camino(2, 1)
    assert resultado.encontrado is False
    assert resultado.entidades_camino == []
    assert resultado.relaciones_camino == []


def test_camino_origen_igual_destino() -> None:
    grafo = Graph()
    grafo.agregar_entidad(_entidad(1))

    resultado = grafo.buscar_camino(1, 1)
    assert resultado.encontrado is True
    assert resultado.entidades_camino == [1]
    assert resultado.relaciones_camino == []


def test_camino_multiple_devuelve_minimo_en_aristas() -> None:
    grafo = Graph()
    for i in [1, 2, 3, 4, 5]:
        grafo.agregar_entidad(_entidad(i))
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.APUNTA_A))
    grafo.agregar_relacion(Relacion(id=11, origen_id=2, destino_id=4, tipo=TipoRelacion.APUNTA_A))
    grafo.agregar_relacion(Relacion(id=12, origen_id=1, destino_id=3, tipo=TipoRelacion.APUNTA_A))
    grafo.agregar_relacion(Relacion(id=13, origen_id=3, destino_id=5, tipo=TipoRelacion.APUNTA_A))
    grafo.agregar_relacion(Relacion(id=14, origen_id=5, destino_id=4, tipo=TipoRelacion.APUNTA_A))

    resultado = grafo.buscar_camino(1, 4)
    assert resultado.encontrado is True
    assert resultado.entidades_camino == [1, 2, 4]
    assert resultado.relaciones_camino == [10, 11]


def test_camino_con_origen_o_destino_inexistente() -> None:
    grafo = Graph()
    grafo.agregar_entidad(_entidad(1))
    with pytest.raises(EntidadNoEncontradaError):
        grafo.buscar_camino(99, 1)
    with pytest.raises(EntidadNoEncontradaError):
        grafo.buscar_camino(1, 99)
