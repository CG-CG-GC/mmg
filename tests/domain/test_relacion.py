from datetime import date

import pytest

from app.domain.errores import RelacionInvalidaError
from app.domain.evidencia import Evidencia
from app.domain.relacion import Relacion
from app.domain.tipos import TipoRelacion


def test_creacion_relacion_valida() -> None:
    evidencia = Evidencia(id=1, fuente="https://ejemplo.test", descripcion="Fuente")
    relacion = Relacion(
        id=10,
        origen_id=1,
        destino_id=2,
        tipo=TipoRelacion.POSEE,
        descripcion="Posee correo",
        fecha=date(2026, 10, 7),
        evidencias=[evidencia],
    )
    assert relacion.id == 10
    assert relacion.origen_id == 1
    assert relacion.destino_id == 2
    assert relacion.tipo == TipoRelacion.POSEE
    assert len(relacion.evidencias) == 1


def test_relacion_con_datos_invalidos() -> None:
    with pytest.raises(RelacionInvalidaError):
        Relacion(id=0, origen_id=1, destino_id=2, tipo=TipoRelacion.POSEE)

    with pytest.raises(RelacionInvalidaError):
        Relacion(id=1, origen_id=0, destino_id=2, tipo=TipoRelacion.POSEE)

    with pytest.raises(RelacionInvalidaError):
        Relacion(id=1, origen_id=1, destino_id=0, tipo=TipoRelacion.POSEE)

    with pytest.raises(RelacionInvalidaError):
        Relacion(id=1, origen_id=1, destino_id=2, tipo="POSEE")  # type: ignore[arg-type]

    with pytest.raises(RelacionInvalidaError):
        Relacion(
            id=1,
            origen_id=1,
            destino_id=2,
            tipo=TipoRelacion.POSEE,
            evidencias=["no-es-evidencia"],  # type: ignore[list-item]
        )


def test_relacion_permite_bucles_y_evidencias_opcionales() -> None:
    relacion = Relacion(id=22, origen_id=7, destino_id=7, tipo=TipoRelacion.UTILIZA)
    assert relacion.origen_id == relacion.destino_id == 7
    assert relacion.evidencias == []
