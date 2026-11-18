from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.errors import DatabaseBusyError, ForeignKeysDisabledError


def sqlite_url_from_path(database_path: str | Path) -> str:
    absolute = Path(database_path).resolve()
    return f"sqlite:///{absolute.as_posix()}"


def create_sqlite_engine(database_url: str, *, echo: bool = False) -> Engine:
    if not database_url.startswith("sqlite"):
        raise ValueError("La URL de base de datos debe apuntar a SQLite.")

    engine = create_engine(database_url, echo=echo, future=True)
    _register_foreign_keys_pragma(engine)
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False, autoflush=False)


def assert_foreign_keys_enabled(resource: Session | Any) -> None:
    if isinstance(resource, Session):
        foreign_keys_state = resource.execute(text("PRAGMA foreign_keys")).scalar_one()
    else:
        foreign_keys_state = resource.exec_driver_sql("PRAGMA foreign_keys").scalar_one()

    if int(foreign_keys_state) != 1:
        raise ForeignKeysDisabledError(
            "SQLite tiene las claves foráneas deshabilitadas para la conexión activa."
        )


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        assert_foreign_keys_enabled(session)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def transaccion_inmediata(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Una sola sesión con BEGIN IMMEDIATE; solo para el flujo de incorporación DNS.

    El modo AUTOCOMMIT se pide a nivel de conexión: sqlite3 no abre un BEGIN propio
    y el engine compartido no cambia. El commit y el rollback siguen siendo los de
    la sesión.
    """
    session = session_factory()
    try:
        conexion = session.connection(execution_options={"isolation_level": "AUTOCOMMIT"})
        assert_foreign_keys_enabled(session)
        conexion.exec_driver_sql("BEGIN IMMEDIATE")
        yield session
        session.commit()
    except OperationalError as exc:
        session.rollback()
        if es_bloqueo_sqlite(exc):
            raise DatabaseBusyError(
                "La base de datos está ocupada por otra escritura; el lote no se aplicó."
            ) from exc
        raise
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def es_bloqueo_sqlite(exc: OperationalError) -> bool:
    error_name = getattr(exc.orig, "sqlite_errorname", None)
    if error_name is not None:
        return error_name.startswith(("SQLITE_BUSY", "SQLITE_LOCKED"))
    return "database is locked" in str(exc.orig)


def _register_foreign_keys_pragma(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine, "checkout")
    def _enable_sqlite_foreign_keys_checkout(
        dbapi_connection: Any, _: Any, __: Any
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
