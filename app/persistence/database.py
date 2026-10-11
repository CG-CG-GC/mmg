from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.errors import ForeignKeysDisabledError


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
