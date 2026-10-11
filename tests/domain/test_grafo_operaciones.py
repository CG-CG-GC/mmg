import pytest

from app.domain.entidad import Entidad
from app.domain.errores import (
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    RelacionDuplicadaError,
    RelacionNoEncontradaError,
)
from app.domain.grafo import Graph
from app.domain.relacion import Relacion
from app.domain.tipos import TipoEntidad, TipoRelacion


def _grafo_base() -> Graph:
    grafo = Graph()
    grafo.agregar_entidad(Entidad(id=1, tipo=TipoEntidad.PERSONA, valor="ana"))
    grafo.agregar_entidad(Entidad(id=2, tipo=TipoEntidad.EMAIL, valor="ana@example.com"))
    grafo.agregar_entidad(Entidad(id=3, tipo=TipoEntidad.ORGANIZACION, valor="empresa-x"))
    return grafo


def test_agregar_buscar_y_existe_entidad() -> None:
    grafo = Graph()
    entidad = Entidad(id=1, tipo=TipoEntidad.PERSONA, valor="ana")
    grafo.agregar_entidad(entidad)

    assert grafo.buscar_entidad(1) == entidad
    assert grafo.existe_entidad(1) is True
    assert grafo.buscar_entidad(99) is None
    assert grafo.existe_entidad(99) is False


def test_agregar_entidad_duplicada_por_id_falla() -> None:
    grafo = Graph()
    grafo.agregar_entidad(Entidad(id=1, tipo=TipoEntidad.PERSONA, valor="ana"))
    with pytest.raises(EntidadDuplicadaError):
        grafo.agregar_entidad(Entidad(id=1, tipo=TipoEntidad.EMAIL, valor="ana@example.com"))


def test_eliminar_entidad_y_relaciones_incidentes() -> None:
    grafo = _grafo_base()
    r1 = Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE)
    r2 = Relacion(id=11, origen_id=3, destino_id=1, tipo=TipoRelacion.PERTENECE_A)
    grafo.agregar_relacion(r1)
    grafo.agregar_relacion(r2)

    eliminada = grafo.eliminar_entidad(1)
    assert eliminada.id == 1
    assert grafo.existe_entidad(1) is False
    assert grafo.buscar_relacion(10) is None
    assert grafo.buscar_relacion(11) is None


def test_eliminar_entidad_inexistente_falla() -> None:
    grafo = Graph()
    with pytest.raises(EntidadNoEncontradaError):
        grafo.eliminar_entidad(1)


def test_agregar_buscar_eliminar_relacion() -> None:
    grafo = _grafo_base()
    relacion = Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE)
    grafo.agregar_relacion(relacion)

    assert grafo.buscar_relacion(10) == relacion
    assert grafo.existe_relacion(10) is True

    eliminada = grafo.eliminar_relacion(10)
    assert eliminada.id == 10
    assert grafo.buscar_relacion(10) is None
    assert grafo.existe_relacion(10) is False


def test_eliminar_relacion_inexistente_falla() -> None:
    grafo = _grafo_base()
    with pytest.raises(RelacionNoEncontradaError):
        grafo.eliminar_relacion(999)


def test_relaciones_duplicadas_y_paralelas() -> None:
    grafo = _grafo_base()
    base = Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE)
    grafo.agregar_relacion(base)

    with pytest.raises(RelacionDuplicadaError):
        grafo.agregar_relacion(Relacion(id=11, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE))

    grafo.agregar_relacion(Relacion(id=12, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    assert grafo.existe_relacion(12) is True


def test_relacion_con_origen_o_destino_inexistente_falla() -> None:
    grafo = _grafo_base()
    with pytest.raises(EntidadNoEncontradaError):
        grafo.agregar_relacion(Relacion(id=50, origen_id=99, destino_id=2, tipo=TipoRelacion.POSEE))
    with pytest.raises(EntidadNoEncontradaError):
        grafo.agregar_relacion(Relacion(id=51, origen_id=1, destino_id=99, tipo=TipoRelacion.POSEE))


def test_obtener_vecinos_y_grafo_vacio() -> None:
    grafo = _grafo_base()
    grafo.agregar_relacion(Relacion(id=10, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE))
    grafo.agregar_relacion(Relacion(id=11, origen_id=1, destino_id=2, tipo=TipoRelacion.UTILIZA))
    grafo.agregar_relacion(Relacion(id=12, origen_id=1, destino_id=3, tipo=TipoRelacion.TRABAJA_EN))

    vecinos = grafo.obtener_vecinos(1)
    assert [vecino.id for vecino in vecinos] == [2, 3]

    grafo_vacio = Graph()
    assert grafo_vacio.buscar_entidad(1) is None
    assert grafo_vacio.buscar_relacion(1) is None
    with pytest.raises(EntidadNoEncontradaError):
        grafo_vacio.obtener_vecinos(1)
