import pytest

from app.domain.entidad import Entidad
from app.domain.errores import EntidadInvalidaError
from app.domain.tipos import TipoEntidad


def test_creacion_entidad_valida() -> None:
    entidad = Entidad(
        id=1,
        tipo=TipoEntidad.EMAIL,
        valor="ana@example.com",
        descripcion="Correo principal",
        metadata={"fuente": "manual"},
    )
    assert entidad.id == 1
    assert entidad.tipo == TipoEntidad.EMAIL
    assert entidad.valor == "ana@example.com"
    assert entidad.descripcion == "Correo principal"
    assert entidad.metadata == {"fuente": "manual"}


def test_entidad_con_datos_invalidos() -> None:
    with pytest.raises(EntidadInvalidaError):
        Entidad(id=0, tipo=TipoEntidad.PERSONA, valor="Ana")

    with pytest.raises(EntidadInvalidaError):
        Entidad(id=1, tipo=TipoEntidad.PERSONA, valor="  ")

    with pytest.raises(EntidadInvalidaError):
        Entidad(id=1, tipo="PERSONA", valor="Ana")  # type: ignore[arg-type]


def test_entidad_con_campos_opcionales() -> None:
    entidad = Entidad(id=2, tipo=TipoEntidad.IP, valor="192.168.0.1")
    assert entidad.descripcion is None
    assert entidad.metadata is None
