"""Coherencia de la política DNS entre dominio, aplicación y persistencia (QA-06-01 y QA-06-04)."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.application.dns_lookup import DominioInvalidoError, normalizar_dominio
from app.persistence.database import create_session_factory, create_sqlite_engine, sqlite_url_from_path
from app.persistence.errors import RepositoryError
from app.persistence.incorporacion_dns import (
    IncorporacionDnsRepository,
    LoteDnsIncorporacion,
    LoteDnsInvalidoError,
    RegistroDnsIncorporacion,
    canonizar_dominio,
)
from app.domain.tipos import TipoEntidad
from app.persistence.repositories import EntidadCreateData, EntidadRepository
from app.persistence.schema import EntidadModel, EvidenciaModel, RelacionModel, initialize_database

ACEPTADOS = [
    "example.com",
    "EXAMPLE.com.",
    "  Example.COM  ",
    "M\xdcNCHEN.de",
    "m\xfcnchen.de",
    "münchen.de",
    "xn--mnchen-3ya.de",
    "XN--MNCHEN-3YA.DE",
    "xn--strae-oqa.de",
    "sub.m\xfcnchen.de",
]
RECHAZADOS = [
    "İstanbul.tr",
    "xn--bogus.de",
    "xn--invalid-zz.de",
    "stra\xdfe.de",
    "a..b",
    "example。com",
]


@pytest.mark.parametrize("entrada", ACEPTADOS)
def test_canonizacion_coincide_entre_persistencia_y_aplicacion(entrada):
    assert canonizar_dominio(entrada) == normalizar_dominio(entrada)


@pytest.mark.parametrize("entrada", RECHAZADOS)
def test_rechazos_coinciden_entre_persistencia_y_aplicacion(entrada):
    with pytest.raises(ValueError):
        canonizar_dominio(entrada)
    with pytest.raises(DominioInvalidoError):
        normalizar_dominio(entrada)


@pytest.fixture
def repositorio(tmp_path):
    engine = create_sqlite_engine(sqlite_url_from_path(tmp_path / "politica.sqlite3"))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)
    yield IncorporacionDnsRepository(session_factory), session_factory
    engine.dispose()


def _lote(dominio):
    return LoteDnsIncorporacion(
        dominio=dominio,
        registros=(
            RegistroDnsIncorporacion(
                tipo="A",
                valor="192.0.2.1",
                fuente="google-public-dns-doh",
                consultado_en=datetime(2026, 11, 18, 12, tzinfo=UTC),
            ),
        ),
    )


def _cantidades(session_factory):
    with session_factory() as sesion:
        return tuple(
            sesion.scalar(select(func.count()).select_from(modelo))
            for modelo in (EntidadModel, RelacionModel, EvidenciaModel)
        )


@pytest.mark.parametrize("dominio", RECHAZADOS)
def test_repositorio_rechaza_sin_escribir(repositorio, dominio):
    repo, session_factory = repositorio

    with pytest.raises((LoteDnsInvalidoError, RepositoryError, ValueError)):
        repo.incorporar_lote(_lote(dominio))

    assert _cantidades(session_factory) == (0, 0, 0)


def test_repositorio_no_reutiliza_entidad_de_otro_dominio(repositorio):
    repo, session_factory = repositorio
    EntidadRepository(session_factory).create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="İstanbul.tr", valor_normalizado="İstanbul.tr")
    )

    resultado = repo.incorporar_lote(_lote("istanbul.tr"))

    assert resultado.dominio.estado == "creada"
