from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.routes import router
from app.application.errors import GraphUnavailableError
from app.application.service import GraphApplicationService
from app.domain.errores import (
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    ErrorValidacion,
    RelacionDuplicadaError,
    RelacionNoEncontradaError,
)
from app.persistence.database import create_session_factory, create_sqlite_engine, sqlite_url_from_path
from app.persistence.errors import (
    GraphReconstructionError,
    IntegrityConstraintError,
    PersistenceError,
)
from app.persistence.repositories import EntidadRepository, EvidenciaRepository, RelacionRepository
from app.persistence.schema import initialize_database


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Crea la aplicación y sus dependencias para un archivo SQLite concreto."""
    path = Path(database_path or os.getenv("MMG_DATABASE_PATH", "data/mmg.sqlite3")).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_sqlite_engine(sqlite_url_from_path(path))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)

    entidad_repository = EntidadRepository(session_factory)
    relacion_repository = RelacionRepository(session_factory)
    evidencia_repository = EvidenciaRepository(session_factory)
    graph_service = GraphApplicationService(
        session_factory=session_factory,
        entidad_repository=entidad_repository,
        relacion_repository=relacion_repository,
        evidencia_repository=evidencia_repository,
    )

    app = FastAPI(
        title="Mini-Maltego Académico API",
        version="0.1.0",
        description="API académica para entidades, relaciones, evidencias y algoritmos de grafos.",
    )
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.entidad_repository = entidad_repository
    app.state.relacion_repository = relacion_repository
    app.state.evidencia_repository = evidencia_repository
    app.state.graph_service = graph_service

    @app.get("/health", tags=["sistema"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(GraphUnavailableError)
    async def graph_unavailable_handler(_: Request, exc: GraphUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(EntidadNoEncontradaError)
    @app.exception_handler(RelacionNoEncontradaError)
    async def domain_not_found_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(EntidadDuplicadaError)
    @app.exception_handler(RelacionDuplicadaError)
    @app.exception_handler(IntegrityConstraintError)
    async def conflict_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ErrorValidacion)
    async def domain_validation_handler(_: Request, exc: ErrorValidacion) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(PersistenceError)
    @app.exception_handler(GraphReconstructionError)
    async def persistence_error_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error interno al acceder a los datos del proyecto."},
        )

    app.include_router(router)

    @app.on_event("shutdown")
    def close_engine() -> None:
        engine.dispose()

    return app


app = create_app()
