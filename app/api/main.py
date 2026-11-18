from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.dns_routes import router as dns_router
from app.api.routes import router
from app.application.dns_lookup import (
    DnsLookupService,
    DominioInvalidoError,
    TipoRegistroInvalidoError,
)
from app.application.errors import GraphUnavailableError
from app.application.incorporacion_dns import (
    IncorporacionDnsConflictoError,
    IncorporacionDnsFallaInternaError,
    IncorporacionDnsInvalidaError,
    IncorporacionDnsOcupadaError,
    IncorporacionDnsService,
    IncorporacionPersistidaSinGrafoError,
)
from app.integrations.dns_google import GoogleDohProvider
from app.application.service import GraphApplicationService
from app.domain.errores import (
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    ErrorValidacion,
    RelacionDuplicadaError,
    RelacionNoEncontradaError,
)
from app.persistence.database import create_session_factory, create_sqlite_engine, sqlite_url_from_path
from app.persistence.incorporacion_dns import IncorporacionDnsRepository
from app.persistence.errors import (
    ForeignKeyConstraintError,
    GraphReconstructionError,
    PersistenceError,
    RecordNotFoundError,
    UniqueConstraintError,
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

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Mini-Maltego Académico API",
        version="0.1.0",
        description="API académica para entidades, relaciones, evidencias y algoritmos de grafos.",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.entidad_repository = entidad_repository
    app.state.relacion_repository = relacion_repository
    app.state.evidencia_repository = evidencia_repository
    app.state.graph_service = graph_service
    app.state.dns_service = DnsLookupService(GoogleDohProvider())
    app.state.incorporacion_dns_service = IncorporacionDnsService(
        IncorporacionDnsRepository(session_factory),
        refrescar_grafo=graph_service.refrescar_tras_escritura,
    )

    @app.get("/health", tags=["sistema"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(GraphUnavailableError)
    async def graph_unavailable_handler(_: Request, exc: GraphUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(EntidadNoEncontradaError)
    @app.exception_handler(RelacionNoEncontradaError)
    @app.exception_handler(RecordNotFoundError)
    async def domain_not_found_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(EntidadDuplicadaError)
    @app.exception_handler(RelacionDuplicadaError)
    @app.exception_handler(UniqueConstraintError)
    @app.exception_handler(IncorporacionDnsConflictoError)
    async def conflict_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ForeignKeyConstraintError)
    async def foreign_key_not_found_handler(
        _: Request, exc: ForeignKeyConstraintError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ErrorValidacion)
    @app.exception_handler(DominioInvalidoError)
    @app.exception_handler(TipoRegistroInvalidoError)
    @app.exception_handler(IncorporacionDnsInvalidaError)
    async def domain_validation_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(PersistenceError)
    @app.exception_handler(GraphReconstructionError)
    @app.exception_handler(IncorporacionDnsFallaInternaError)
    async def persistence_error_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error interno al acceder a los datos del proyecto."},
        )

    @app.exception_handler(IncorporacionDnsOcupadaError)
    async def incorporacion_ocupada_handler(
        _: Request, exc: IncorporacionDnsOcupadaError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(IncorporacionPersistidaSinGrafoError)
    async def incorporacion_sin_grafo_handler(
        _: Request, exc: IncorporacionPersistidaSinGrafoError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "persistencia": "confirmada"},
        )

    app.include_router(router)
    app.include_router(dns_router)

    frontend = Path(__file__).resolve().parents[1] / "frontend"
    app.mount("/static", StaticFiles(directory=frontend), name="frontend")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend / "index.html")

    return app


app = create_app()
