from __future__ import annotations

import importlib.util

import pytest

SQLALCHEMY_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None

if SQLALCHEMY_AVAILABLE:
    from app.persistence.database import create_session_factory, create_sqlite_engine, sqlite_url_from_path
    from app.persistence.repositories import EvidenciaRepository, EntidadRepository, RelacionRepository
    from app.persistence.schema import initialize_database


@pytest.fixture
def session_factory(tmp_path: pytest.TempPathFactory):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy no está disponible en el entorno actual.")

    database_path = tmp_path / "mini_maltego_persistencia.sqlite3"
    engine = create_sqlite_engine(sqlite_url_from_path(database_path))
    factory = create_session_factory(engine)
    initialize_database(engine, factory)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture
def entidad_repo(session_factory):
    return EntidadRepository(session_factory)


@pytest.fixture
def relacion_repo(session_factory):
    return RelacionRepository(session_factory)


@pytest.fixture
def evidencia_repo(session_factory):
    return EvidenciaRepository(session_factory)
