import sqlite3
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import event, func, select

from app.application.errors import GraphUnavailableError
from app.application.incorporacion_dns import (
    MAX_REGISTROS_INCORPORACION,
    IncorporacionDnsConflictoError,
    IncorporacionDnsFallaInternaError,
    IncorporacionDnsInvalidaError,
    IncorporacionDnsOcupadaError,
    IncorporacionDnsService,
    IncorporacionPersistidaSinGrafoError,
    RegistroSolicitadoDns,
    SolicitudIncorporacionDns,
)
from app.application.service import GraphApplicationService
from app.domain.tipos import TipoEntidad
from app.persistence.database import (
    create_session_factory,
    create_sqlite_engine,
    sqlite_url_from_path,
)
from app.persistence.errors import (
    CoincidenciaAmbiguaError,
    DatabaseBusyError,
    ForeignKeyConstraintError,
    UniqueConstraintError,
)
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.incorporacion_dns import (
    PREFIJO_PROCEDENCIA_DECLARADA,
    IncorporacionDnsRepository,
    LoteDnsInvalidoError,
)
from app.persistence.repositories import (
    EntidadCreateData,
    EntidadRepository,
    EvidenciaRepository,
    RelacionRepository,
)
from app.persistence.schema import EntidadModel, EvidenciaModel, RelacionModel, initialize_database

AHORA = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
FUENTE = "google-public-dns-doh"


def _registro(tipo="A", valor="192.0.2.1", fuente=FUENTE, consultado_en=AHORA):
    return RegistroSolicitadoDns(tipo=tipo, valor=valor, fuente=fuente, consultado_en=consultado_en)


def _solicitud(*registros, dominio="example.com"):
    return SolicitudIncorporacionDns(dominio=dominio, registros=tuple(registros))


@pytest.fixture
def ctx(tmp_path):
    ruta = tmp_path / "incorporacion-aplicacion.sqlite3"
    engine = create_sqlite_engine(sqlite_url_from_path(ruta))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)
    fallar = {"activo": False}

    def cargador(factory):
        if fallar["activo"]:
            raise RuntimeError("fallo simulado de reconstrucción")
        return load_graph_from_database(factory)

    grafo = GraphApplicationService(
        session_factory=session_factory,
        entidad_repository=EntidadRepository(session_factory),
        relacion_repository=RelacionRepository(session_factory),
        evidencia_repository=EvidenciaRepository(session_factory),
        graph_loader=cargador,
    )
    servicio = IncorporacionDnsService(
        IncorporacionDnsRepository(session_factory),
        refrescar_grafo=grafo.refrescar_tras_escritura,
    )
    yield SimpleNamespace(
        ruta=ruta,
        engine=engine,
        session_factory=session_factory,
        grafo=grafo,
        servicio=servicio,
        fallar=fallar,
    )
    engine.dispose()


def _contar(ctx, modelo) -> int:
    with ctx.session_factory() as session:
        return session.scalar(select(func.count()).select_from(modelo))


def _estado_bd(ctx) -> tuple[int, int, int]:
    return (
        _contar(ctx, EntidadModel),
        _contar(ctx, RelacionModel),
        _contar(ctx, EvidenciaModel),
    )


def test_incorpora_a_y_aaaa_con_entidades_relaciones_y_evidencias(ctx):
    resultado = ctx.servicio.incorporar(
        _solicitud(_registro("A", "192.0.2.1"), _registro("AAAA", "2001:DB8::1"))
    )

    assert resultado.dominio.estado == "creada"
    assert [r.valor for r in resultado.registros] == ["192.0.2.1", "2001:db8::1"]
    assert all(
        r.entidad.estado == "creada"
        and r.relacion.estado == "creada"
        and r.evidencia.estado == "creada"
        for r in resultado.registros
    )
    assert _estado_bd(ctx) == (3, 2, 2)

    grafo = ctx.grafo.graph
    for registro in resultado.registros:
        assert grafo.existe_entidad(registro.entidad.id)
        assert grafo.existe_relacion(registro.relacion.id)


def test_la_procedencia_queda_marcada_como_declarada(ctx):
    ctx.servicio.incorporar(_solicitud(_registro()))

    with ctx.session_factory() as session:
        fuente, fecha = session.execute(
            select(EvidenciaModel.fuente, EvidenciaModel.fecha)
        ).one()

    assert fuente == PREFIJO_PROCEDENCIA_DECLARADA + FUENTE
    assert fecha == "2026-11-16T12:00:00+00:00"
    resultado = ctx.servicio.incorporar(_solicitud(_registro()))
    assert resultado.registros[0].fuente == FUENTE
    assert resultado.registros[0].consultado_en == AHORA


def test_repetir_el_lote_reutiliza_todo_sin_duplicar_evidencias(ctx):
    primero = ctx.servicio.incorporar(_solicitud(_registro()))
    antes = _estado_bd(ctx)

    segundo = ctx.servicio.incorporar(_solicitud(_registro()))

    assert _estado_bd(ctx) == antes
    assert segundo.dominio.id == primero.dominio.id
    assert segundo.dominio.estado == "reutilizada"
    assert segundo.registros[0].entidad.id == primero.registros[0].entidad.id
    assert segundo.registros[0].relacion.id == primero.registros[0].relacion.id
    assert segundo.registros[0].evidencia.id == primero.registros[0].evidencia.id
    assert segundo.registros[0].evidencia.estado == "reutilizada"


def test_reutiliza_entidades_existentes_con_otra_forma_canonica(ctx):
    repo_entidades = EntidadRepository(ctx.session_factory)
    dominio = repo_entidades.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="Example.COM", valor_normalizado="Example.COM")
    )
    ip = repo_entidades.create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="2001:DB8::1", valor_normalizado="2001:DB8::1")
    )

    resultado = ctx.servicio.incorporar(
        _solicitud(_registro("AAAA", "2001:db8::1"), dominio="example.com")
    )

    assert resultado.dominio.id == dominio.id
    assert resultado.dominio.estado == "reutilizada"
    assert resultado.registros[0].entidad.id == ip.id
    assert resultado.registros[0].entidad.estado == "reutilizada"
    assert _contar(ctx, EntidadModel) == 2


def test_dominio_idna_y_mayusculas_se_guardan_en_forma_canonica(ctx):
    resultado = ctx.servicio.incorporar(_solicitud(_registro(), dominio="München.DE."))

    assert resultado.dominio.estado == "creada"
    with ctx.session_factory() as session:
        valores = set(session.scalars(select(EntidadModel.valor)).all())
    assert "xn--mnchen-3ya.de" in valores


def test_registros_repetidos_se_incorporan_una_sola_vez(ctx):
    resultado = ctx.servicio.incorporar(_solicitud(_registro(), _registro()))

    assert len(resultado.registros) == 1
    assert _estado_bd(ctx) == (2, 1, 1)


INVALIDOS = [
    pytest.param(_solicitud(), id="lote_vacio"),
    pytest.param(_solicitud(_registro(), dominio="stra\u00dfe.de"), id="dominio_idna_no_equivalente"),
    pytest.param(_solicitud(_registro(), dominio="http://example.com"), id="dominio_con_esquema"),
    pytest.param(_solicitud(_registro(), dominio="1.2.3.4"), id="dominio_ip"),
    pytest.param(_solicitud(_registro(), dominio="localhost"), id="dominio_sin_punto"),
    pytest.param(_solicitud(_registro(tipo="CNAME")), id="tipo_cname"),
    pytest.param(_solicitud(_registro(tipo="MX")), id="tipo_mx"),
    pytest.param(_solicitud(_registro(tipo="a")), id="tipo_en_minusculas"),
    pytest.param(_solicitud(_registro("A", "2001:db8::1")), id="a_con_ipv6"),
    pytest.param(_solicitud(_registro("AAAA", "192.0.2.1")), id="aaaa_con_ipv4"),
    pytest.param(_solicitud(_registro(valor="no-es-ip")), id="ip_malformada"),
    pytest.param(_solicitud(_registro(fuente="")), id="fuente_vacia"),
    pytest.param(_solicitud(_registro(fuente="   ")), id="fuente_solo_espacios"),
    pytest.param(_solicitud(_registro(fuente="x" * 101)), id="fuente_demasiado_larga"),
    pytest.param(_solicitud(_registro(consultado_en=datetime(2026, 11, 16, 12))), id="fecha_sin_zona"),
    pytest.param(_solicitud(_registro(), _registro(tipo="CNAME")), id="un_registro_invalido_en_el_lote"),
]


@pytest.mark.parametrize("solicitud", INVALIDOS)
def test_registros_invalidos_se_rechazan_sin_escribir(ctx, solicitud):
    with pytest.raises(IncorporacionDnsInvalidaError):
        ctx.servicio.incorporar(solicitud)

    assert _estado_bd(ctx) == (0, 0, 0)


def test_ipv6_con_zona_se_rechaza_sin_escribir(ctx):
    with pytest.raises(IncorporacionDnsInvalidaError):
        ctx.servicio.incorporar(_solicitud(_registro("AAAA", "fe80::1%eth0")))

    assert _estado_bd(ctx) == (0, 0, 0)


def test_lote_excesivo_se_rechaza_sin_escribir(ctx):
    registros = [_registro(valor=f"192.0.2.{i}") for i in range(1, MAX_REGISTROS_INCORPORACION + 2)]

    with pytest.raises(IncorporacionDnsInvalidaError, match="máximo"):
        ctx.servicio.incorporar(_solicitud(*registros))

    assert _estado_bd(ctx) == (0, 0, 0)


def test_coincidencias_ambiguas_rechazan_todo_el_lote(ctx):
    repo = EntidadRepository(ctx.session_factory)
    repo.create(EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="Example.com.", valor_normalizado="example.com."))
    repo.create(EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="EXAMPLE.com", valor_normalizado="EXAMPLE.com"))
    antes = _estado_bd(ctx)

    with pytest.raises(IncorporacionDnsConflictoError, match="equivalentes"):
        ctx.servicio.incorporar(_solicitud(_registro()))

    assert _estado_bd(ctx) == (antes[0], 0, 0)


def test_sqlite_ocupado_responde_ocupada_sin_escritura_parcial(ctx):
    def busy_timeout_corto(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=50")
        cursor.close()

    event.listen(ctx.engine, "connect", busy_timeout_corto)
    ctx.engine.dispose()
    bloqueo = sqlite3.connect(ctx.ruta, isolation_level=None)
    bloqueo.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(IncorporacionDnsOcupadaError):
            ctx.servicio.incorporar(_solicitud(_registro()))
    finally:
        bloqueo.execute("ROLLBACK")
        bloqueo.close()

    assert _estado_bd(ctx) == (0, 0, 0)
    resultado = ctx.servicio.incorporar(_solicitud(_registro()))
    assert resultado.dominio.estado == "creada"


def test_fallo_de_reconstruccion_informa_persistencia_confirmada_y_reintento_recupera(ctx):
    ctx.fallar["activo"] = True

    with pytest.raises(IncorporacionPersistidaSinGrafoError) as info:
        ctx.servicio.incorporar(_solicitud(_registro()))

    mensaje = str(info.value)
    assert "sí se guardaron" in mensaje
    assert "rollback" not in mensaje.lower()
    assert _estado_bd(ctx) == (2, 1, 1)
    with pytest.raises(GraphUnavailableError):
        _ = ctx.grafo.graph

    ctx.fallar["activo"] = False
    resultado = ctx.servicio.incorporar(_solicitud(_registro()))

    assert resultado.dominio.estado == "reutilizada"
    assert resultado.registros[0].evidencia.estado == "reutilizada"
    assert _estado_bd(ctx) == (2, 1, 1)
    assert ctx.grafo.graph.existe_relacion(resultado.registros[0].relacion.id)


class _RepositorioFalso:
    def __init__(self, error):
        self._error = error

    def incorporar_lote(self, lote):
        raise self._error


@pytest.mark.parametrize(
    ("error_persistencia", "error_aplicacion"),
    [
        (LoteDnsInvalidoError("lote"), IncorporacionDnsInvalidaError),
        (CoincidenciaAmbiguaError("ambiguo"), IncorporacionDnsConflictoError),
        (UniqueConstraintError("unico"), IncorporacionDnsConflictoError),
        (DatabaseBusyError("ocupada"), IncorporacionDnsOcupadaError),
        (ForeignKeyConstraintError("fk"), IncorporacionDnsFallaInternaError),
    ],
)
def test_errores_de_persistencia_se_traducen_sin_refrescar_grafo(error_persistencia, error_aplicacion):
    refrescos = []
    servicio = IncorporacionDnsService(
        _RepositorioFalso(error_persistencia), refrescar_grafo=lambda: refrescos.append(1)
    )

    with pytest.raises(error_aplicacion):
        servicio.incorporar(_solicitud(_registro()))

    assert refrescos == []
