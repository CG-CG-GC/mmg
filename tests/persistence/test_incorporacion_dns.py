from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, func, select

from app.application.dns_lookup import DominioInvalidoError, normalizar_dominio
from app.domain.tipos import TipoEntidad, TipoRelacion
from app.persistence import incorporacion_dns
from app.persistence.database import (
    create_session_factory,
    create_sqlite_engine,
    sqlite_url_from_path,
    transaccion_inmediata,
)
from app.persistence.errors import (
    CoincidenciaAmbiguaError,
    DatabaseBusyError,
    ForeignKeyConstraintError,
    UniqueConstraintError,
)
from app.persistence.incorporacion_dns import (
    PREFIJO_PROCEDENCIA_DECLARADA,
    IncorporacionDnsRepository,
    LoteDnsIncorporacion,
    LoteDnsInvalidoError,
    ObjetoIncorporado,
    RegistroDnsIncorporacion,
    canonizar_dominio,
)
from app.persistence.repositories import (
    EntidadCreateData,
    EntidadRepository,
    RelacionCreateData,
    RelacionRepository,
)
from app.persistence.schema import (
    EntidadModel,
    EvidenciaModel,
    RelacionModel,
    TipoEntidadModel,
    initialize_database,
)

FUENTE = "google-public-dns-doh"
CONSULTA = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def _registro(tipo="A", valor="192.0.2.1", consultado_en=CONSULTA, fuente=FUENTE):
    return RegistroDnsIncorporacion(tipo=tipo, valor=valor, fuente=fuente, consultado_en=consultado_en)


def _lote(*registros, dominio="example.com"):
    return LoteDnsIncorporacion(dominio=dominio, registros=registros or (_registro(),))


def _contar(factory, modelo) -> int:
    with factory() as sesion:
        return sesion.scalar(select(func.count()).select_from(modelo))


def _tipo_entidad_id(factory, tipo: TipoEntidad) -> int:
    with factory() as sesion:
        return sesion.scalar(select(TipoEntidadModel.id).where(TipoEntidadModel.codigo == tipo.value))


def _ejecutar_en_hilos(*funciones) -> None:
    errores: list[BaseException] = []

    def envolver(funcion) -> None:
        try:
            funcion()
        except BaseException as exc:
            errores.append(exc)

    hilos = [threading.Thread(target=envolver, args=(funcion,)) for funcion in funciones]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=30)
    assert not errores, errores


def _contar_todo(factory) -> tuple[int, int, int]:
    return (
        _contar(factory, EntidadModel),
        _contar(factory, RelacionModel),
        _contar(factory, EvidenciaModel),
    )


@pytest.fixture
def ruta_base(tmp_path):
    return tmp_path / "incorporacion_dns.sqlite3"


@pytest.fixture
def motor(ruta_base):
    engine = create_sqlite_engine(sqlite_url_from_path(ruta_base))
    initialize_database(engine, create_session_factory(engine))
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(motor):
    return create_session_factory(motor)


@pytest.fixture
def repo(session_factory):
    return IncorporacionDnsRepository(session_factory)


def test_crea_dominio_ip_relacion_y_evidencia(session_factory, repo):
    resultado = repo.incorporar_lote(_lote())

    assert resultado.dominio.estado == "creada"
    (registro,) = resultado.resultados
    assert (registro.tipo, registro.valor) == ("A", "192.0.2.1")
    assert registro.entidad.estado == "creada"
    assert registro.relacion.estado == "creada"
    assert registro.evidencia.estado == "creada"
    assert _contar_todo(session_factory) == (2, 1, 1)

    with session_factory() as sesion:
        fuente, fecha, descripcion = sesion.execute(
            select(EvidenciaModel.fuente, EvidenciaModel.fecha, EvidenciaModel.descripcion)
        ).one()
    assert fuente == PREFIJO_PROCEDENCIA_DECLARADA + FUENTE
    assert fecha == "2025-01-01T12:00:00+00:00"
    assert descripcion == "Consulta DNS A de example.com"


def test_reutiliza_entidades_y_relacion_existentes(session_factory, repo):
    entidades = EntidadRepository(session_factory)
    dominio = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="example.com", valor_normalizado="example.com")
    )
    ip = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="192.0.2.1", valor_normalizado="192.0.2.1")
    )
    relacion = RelacionRepository(session_factory).create(
        RelacionCreateData(origen_id=dominio.id, destino_id=ip.id, tipo=TipoRelacion.APUNTA_A)
    )

    resultado = repo.incorporar_lote(_lote())

    (registro,) = resultado.resultados
    assert resultado.dominio == ObjetoIncorporado(id=dominio.id, estado="reutilizada")
    assert registro.entidad == ObjetoIncorporado(id=ip.id, estado="reutilizada")
    assert registro.relacion == ObjetoIncorporado(id=relacion.id, estado="reutilizada")
    assert registro.evidencia.estado == "creada"
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_repetir_el_lote_no_duplica_nada(session_factory, repo):
    lote = _lote(_registro("A", "192.0.2.1"), _registro("AAAA", "2001:db8::1"))

    primera = repo.incorporar_lote(lote)
    segunda = repo.incorporar_lote(lote)

    assert primera.dominio.estado == "creada"
    assert segunda.dominio == ObjetoIncorporado(id=primera.dominio.id, estado="reutilizada")
    for previo, actual in zip(primera.resultados, segunda.resultados, strict=True):
        assert actual.entidad == ObjetoIncorporado(id=previo.entidad.id, estado="reutilizada")
        assert actual.relacion == ObjetoIncorporado(id=previo.relacion.id, estado="reutilizada")
        assert actual.evidencia == ObjetoIncorporado(id=previo.evidencia.id, estado="reutilizada")
    assert _contar_todo(session_factory) == (3, 2, 2)


def test_registro_repetido_dentro_del_mismo_lote_reutiliza_relacion_y_evidencia(session_factory, repo):
    resultado = repo.incorporar_lote(_lote(_registro(), _registro()))

    primero, segundo = resultado.resultados
    assert primero.entidad.estado == "creada"
    assert segundo.entidad == ObjetoIncorporado(id=primero.entidad.id, estado="reutilizada")
    assert segundo.relacion == ObjetoIncorporado(id=primero.relacion.id, estado="reutilizada")
    assert segundo.evidencia == ObjetoIncorporado(id=primero.evidencia.id, estado="reutilizada")
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_otra_consulta_agrega_evidencia_sin_alterar_la_anterior(session_factory, repo):
    primera = repo.incorporar_lote(_lote())
    otra_hora = datetime(2025, 1, 2, 12, 0, tzinfo=timezone.utc)

    segunda = repo.incorporar_lote(_lote(_registro(consultado_en=otra_hora)))

    assert segunda.resultados[0].evidencia.estado == "creada"
    assert segunda.resultados[0].evidencia.id != primera.resultados[0].evidencia.id
    assert _contar_todo(session_factory) == (2, 1, 2)


def test_error_intermedio_revierte_todo_el_lote(session_factory, repo, monkeypatch):
    original = incorporacion_dns._obtener_o_crear_evidencia
    llamadas = []

    def fallar_en_segundo_registro(*args, **kwargs):
        llamadas.append(1)
        if len(llamadas) == 2:
            raise RuntimeError("fallo simulado")
        return original(*args, **kwargs)

    monkeypatch.setattr(incorporacion_dns, "_obtener_o_crear_evidencia", fallar_en_segundo_registro)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        repo.incorporar_lote(_lote(_registro("A", "192.0.2.1"), _registro("AAAA", "2001:db8::1")))

    assert _contar_todo(session_factory) == (0, 0, 0)


def test_clave_foranea_inexistente_se_clasifica_y_revierte(session_factory, repo, monkeypatch):
    original = incorporacion_dns._obtener_o_crear_entidad

    def ip_inexistente(session, tipo_id, tipo, canonico, canonizar):
        if tipo is TipoEntidad.IP:
            return ObjetoIncorporado(id=999999, estado="reutilizada")
        return original(session, tipo_id, tipo, canonico, canonizar)

    monkeypatch.setattr(incorporacion_dns, "_obtener_o_crear_entidad", ip_inexistente)

    with pytest.raises(ForeignKeyConstraintError):
        repo.incorporar_lote(_lote())

    assert _contar_todo(session_factory) == (0, 0, 0)


def test_unicidad_de_relacion_se_clasifica_y_revierte(session_factory, repo, monkeypatch):
    entidades = EntidadRepository(session_factory)
    dominio = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="example.com", valor_normalizado="example.com")
    )
    ip = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="192.0.2.1", valor_normalizado="192.0.2.1")
    )
    RelacionRepository(session_factory).create(
        RelacionCreateData(origen_id=dominio.id, destino_id=ip.id, tipo=TipoRelacion.APUNTA_A)
    )

    def relacion_sin_busqueda(session, origen_id, destino_id, tipo_relacion_id):
        session.add(
            RelacionModel(origen_id=origen_id, destino_id=destino_id, tipo_relacion_id=tipo_relacion_id)
        )
        session.flush()
        return ObjetoIncorporado(id=0, estado="creada")

    monkeypatch.setattr(incorporacion_dns, "_obtener_o_crear_relacion", relacion_sin_busqueda)

    with pytest.raises(UniqueConstraintError):
        repo.incorporar_lote(_lote())

    assert _contar_todo(session_factory) == (2, 1, 0)


def test_coincidencias_de_dominio_ambiguas_rechazan_el_lote(session_factory, repo):
    entidades = EntidadRepository(session_factory)
    for valor in ("Example.COM.", "EXAMPLE.com"):
        entidades.create(
            EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor=valor, valor_normalizado=valor)
        )

    with pytest.raises(CoincidenciaAmbiguaError):
        repo.incorporar_lote(_lote())

    assert _contar_todo(session_factory) == (2, 0, 0)


def test_coincidencias_de_ipv6_ambiguas_revierten_el_dominio_creado(session_factory, repo):
    entidades = EntidadRepository(session_factory)
    for valor in ("2001:DB8::1", "2001:db8:0::1"):
        entidades.create(EntidadCreateData(tipo=TipoEntidad.IP, valor=valor, valor_normalizado=valor))

    with pytest.raises(CoincidenciaAmbiguaError):
        repo.incorporar_lote(_lote(_registro("AAAA", "2001:db8::1")))

    assert _contar_todo(session_factory) == (2, 0, 0)


def test_reutiliza_coincidencia_canonica_unica(session_factory, repo):
    entidades = EntidadRepository(session_factory)
    dominio = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="Example.COM.", valor_normalizado="Example.COM.")
    )
    ip = entidades.create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="2001:DB8::1", valor_normalizado="2001:DB8::1")
    )

    resultado = repo.incorporar_lote(_lote(_registro("AAAA", "2001:db8::1")))

    assert resultado.dominio == ObjetoIncorporado(id=dominio.id, estado="reutilizada")
    assert resultado.resultados[0].entidad == ObjetoIncorporado(id=ip.id, estado="reutilizada")
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_valor_existente_no_interpretable_no_coincide(session_factory, repo):
    EntidadRepository(session_factory).create(
        EntidadCreateData(tipo=TipoEntidad.IP, valor="no-es-ip", valor_normalizado="no-es-ip")
    )

    resultado = repo.incorporar_lote(_lote())

    assert resultado.resultados[0].entidad.estado == "creada"
    assert _contar_todo(session_factory) == (3, 1, 1)


@pytest.mark.parametrize(
    "lote",
    [
        LoteDnsIncorporacion(dominio="example.com", registros=()),
        _lote(dominio=""),
        _lote(dominio="a..b.com"),
        _lote(dominio="a b.com"),
        _lote(dominio="-a.com"),
        _lote(dominio="example.com/ruta"),
        _lote(_registro("A", "2001:db8::1")),
        _lote(_registro("AAAA", "fe80::1%eth0")),
        _lote(_registro("AAAA", "192.0.2.1")),
        _lote(_registro(valor="no-es-ip")),
        _lote(_registro(consultado_en=datetime(2025, 1, 1, 12))),
        _lote(_registro(fuente=" ")),
        _lote(_registro(tipo="MX")),
    ],
)
def test_rechaza_lote_no_canonico_sin_escribir(session_factory, repo, lote):
    with pytest.raises(LoteDnsInvalidoError):
        repo.incorporar_lote(lote)

    assert _contar_todo(session_factory) == (0, 0, 0)


def test_dos_sesiones_concurrentes_no_duplican_el_lote(session_factory, repo):
    barrera = threading.Barrier(2, timeout=10)
    resultados = []

    def incorporar() -> None:
        barrera.wait()
        resultados.append(repo.incorporar_lote(_lote()))

    _ejecutar_en_hilos(incorporar, incorporar)

    assert sorted(r.dominio.estado for r in resultados) == ["creada", "reutilizada"]
    assert sorted(r.resultados[0].relacion.estado for r in resultados) == ["creada", "reutilizada"]
    assert sorted(r.resultados[0].evidencia.estado for r in resultados) == ["creada", "reutilizada"]
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_escritura_ajena_en_curso_hace_esperar_al_lote(session_factory, repo):
    retenida = threading.Event()
    liberar = threading.Event()

    def escritor_ajeno() -> None:
        with transaccion_inmediata(session_factory) as sesion:
            sesion.add(
                EntidadModel(
                    tipo_entidad_id=_tipo_entidad_id(session_factory, TipoEntidad.DOMINIO),
                    valor="example.com",
                    valor_normalizado="example.com",
                )
            )
            sesion.flush()
            retenida.set()
            liberar.wait(10)

    hilo = threading.Thread(target=escritor_ajeno)
    hilo.start()
    retenida.wait(10)
    liberar.set()
    resultado = repo.incorporar_lote(_lote())
    hilo.join(timeout=10)

    assert resultado.dominio.estado == "reutilizada"
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_base_ocupada_devuelve_error_sin_escritura_parcial(ruta_base, session_factory):
    motor_corto = create_sqlite_engine(sqlite_url_from_path(ruta_base))

    @event.listens_for(motor_corto, "connect")
    def _busy_corto(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA busy_timeout=300")

    retenida = threading.Event()
    liberar = threading.Event()

    def escritor_ajeno() -> None:
        with transaccion_inmediata(session_factory) as sesion:
            sesion.add(
                EntidadModel(
                    tipo_entidad_id=_tipo_entidad_id(session_factory, TipoEntidad.DOMINIO),
                    valor="ajena.example",
                    valor_normalizado="ajena.example",
                )
            )
            sesion.flush()
            retenida.set()
            liberar.wait(10)

    hilo = threading.Thread(target=escritor_ajeno)
    hilo.start()
    try:
        retenida.wait(10)
        repo_corto = IncorporacionDnsRepository(create_session_factory(motor_corto))
        with pytest.raises(DatabaseBusyError):
            repo_corto.incorporar_lote(_lote())
    finally:
        liberar.set()
        hilo.join(timeout=10)
        motor_corto.dispose()

    assert _contar_todo(session_factory) == (1, 0, 0)


def test_procedencia_declarada_no_se_presenta_como_verificada(session_factory, repo):
    repo.incorporar_lote(_lote())

    with session_factory() as sesion:
        fuentes = sesion.scalars(select(EvidenciaModel.fuente)).all()

    assert fuentes == [PREFIJO_PROCEDENCIA_DECLARADA + FUENTE]


def test_normaliza_la_fecha_consultada_a_utc_para_la_idempotencia(session_factory, repo):
    zona_local = timezone(timedelta(hours=-3))
    repo.incorporar_lote(_lote(_registro(consultado_en=datetime(2025, 1, 1, 9, 0, tzinfo=zona_local))))

    repo.incorporar_lote(_lote(_registro(consultado_en=CONSULTA)))

    with session_factory() as sesion:
        fechas = sesion.scalars(select(EvidenciaModel.fecha)).all()
    assert fechas == ["2025-01-01T12:00:00+00:00"]
    assert _contar_todo(session_factory) == (2, 1, 1)


IDNA = "xn--mnchen-3ya.de"


@pytest.mark.parametrize("existente", ["m\u00fcnchen.de", "mu\u0308nchen.de", IDNA, "XN--MNCHEN-3YA.DE", "M\u00dcNCHEN.de.", " M\u00fcnchen.DE "])
def test_reutiliza_dominio_guardado_en_cualquier_representacion(session_factory, repo, existente):
    EntidadRepository(session_factory).create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor=existente, valor_normalizado=existente)
    )

    resultado = repo.incorporar_lote(_lote(dominio=IDNA))

    assert resultado.dominio.estado == "reutilizada"
    assert _contar_todo(session_factory) == (2, 1, 1)


def test_entidad_con_valor_y_valor_normalizado_equivalentes_cuenta_una_vez(session_factory, repo):
    dominio = EntidadRepository(session_factory).create(
        EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor="münchen.de", valor_normalizado=IDNA)
    )

    resultado = repo.incorporar_lote(_lote(dominio=IDNA))

    assert resultado.dominio == ObjetoIncorporado(id=dominio.id, estado="reutilizada")


def test_unicode_y_punycode_existentes_son_ambiguos_y_revierten(session_factory, repo):
    entidades = EntidadRepository(session_factory)
    for valor in ("münchen.de", IDNA):
        entidades.create(EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor=valor, valor_normalizado=valor))

    with pytest.raises(CoincidenciaAmbiguaError):
        repo.incorporar_lote(_lote(dominio=IDNA))

    assert _contar_todo(session_factory) == (2, 0, 0)


def test_dominio_en_unicode_se_guarda_en_forma_canonica(session_factory, repo):
    resultado = repo.incorporar_lote(_lote(dominio="München.DE."))

    with session_factory() as sesion:
        valor, valor_normalizado = sesion.execute(
            select(EntidadModel.valor, EntidadModel.valor_normalizado).where(
                EntidadModel.id == resultado.dominio.id
            )
        ).one()
    assert (valor, valor_normalizado) == (IDNA, IDNA)


def test_consulta_en_punycode_reutiliza_dominio_creado_en_unicode(session_factory, repo):
    primera = repo.incorporar_lote(_lote(dominio="münchen.de"))

    segunda = repo.incorporar_lote(_lote(dominio=IDNA))

    assert primera.dominio.estado == "creada"
    assert segunda.dominio == ObjetoIncorporado(id=primera.dominio.id, estado="reutilizada")
    assert _contar_todo(session_factory) == (2, 1, 1)


@pytest.mark.parametrize(
    "entrada",
    ["m\u00fcnchen.de", "mu\u0308nchen.de", "M\u00dcNCHEN.DE.", "example.com", IDNA, "a-b.example.org"],
)
def test_canonizacion_coincide_con_la_de_la_aplicacion(entrada):
    assert canonizar_dominio(entrada) == normalizar_dominio(entrada)


def test_stra_e_sharp_s_no_se_canonicaliza_como_strasse():
    # IDNA 2003 convertia la sharp s en ss. La regla compartida ahora rechaza el nombre.
    with pytest.raises(ValueError):
        canonizar_dominio("straße.de")
    with pytest.raises(DominioInvalidoError):
        normalizar_dominio("straße.de")


@pytest.mark.parametrize(
    "entrada",
    ["\u0130stanbul.tr", "xn--bogus.de", "xn--invalid-zz.de"],
)
def test_canonizacion_rechaza_i_con_punto_y_a_labels_invalidas(entrada):
    with pytest.raises(ValueError):
        canonizar_dominio(entrada)
    with pytest.raises(DominioInvalidoError):
        normalizar_dominio(entrada)


def test_fuente_con_espacios_de_borde_se_guarda_recortada(session_factory, repo):
    repo.incorporar_lote(_lote(_registro(fuente="  google-public-dns-doh ")))

    with session_factory() as sesion:
        fuentes = sesion.scalars(select(EvidenciaModel.fuente)).all()
    assert fuentes == [PREFIJO_PROCEDENCIA_DECLARADA + FUENTE]


@pytest.mark.parametrize("entrada", ["a b.com", "-a.com", "a..b.com", "example.com/ruta"])
def test_rechazo_de_dominio_coincide_con_la_aplicacion(entrada):
    with pytest.raises(ValueError):
        canonizar_dominio(entrada)
    with pytest.raises(DominioInvalidoError):
        normalizar_dominio(entrada)


def test_conexion_del_pool_vuelve_al_modo_por_defecto(session_factory, repo, motor):
    def modo_de_la_conexion() -> str | None:
        raw = motor.raw_connection()
        try:
            return raw.dbapi_connection.isolation_level
        finally:
            raw.close()

    repo.incorporar_lote(_lote())
    assert modo_de_la_conexion() == ""

    entidades = EntidadRepository(session_factory)
    for valor in ("münchen.de", IDNA):
        entidades.create(EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor=valor, valor_normalizado=valor))
    with pytest.raises(CoincidenciaAmbiguaError):
        repo.incorporar_lote(_lote(dominio=IDNA))
    assert modo_de_la_conexion() == ""


def test_commit_bloqueado_por_lector_revierte_y_el_reintento_funciona(ruta_base, session_factory):
    motor_corto = create_sqlite_engine(sqlite_url_from_path(ruta_base))

    @event.listens_for(motor_corto, "connect")
    def _busy_corto(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA busy_timeout=300")

    repo_corto = IncorporacionDnsRepository(create_session_factory(motor_corto))
    lector = sqlite3.connect(str(ruta_base), isolation_level=None)
    try:
        # Un lector con SHARED impide el COMMIT del lote, que necesita EXCLUSIVE.
        lector.execute("BEGIN")
        lector.execute("SELECT count(*) FROM entidad").fetchall()
        with pytest.raises(DatabaseBusyError):
            repo_corto.incorporar_lote(_lote())
        assert _contar_todo(session_factory) == (0, 0, 0)

        raw = motor_corto.raw_connection()
        try:
            assert raw.dbapi_connection.isolation_level == ""
        finally:
            raw.close()

        lector.execute("ROLLBACK")
        assert repo_corto.incorporar_lote(_lote()).dominio.estado == "creada"
    finally:
        lector.close()
        motor_corto.dispose()

    assert _contar_todo(session_factory) == (2, 1, 1)


def test_cada_fallo_devuelve_la_conexion_al_pool(session_factory, repo, motor):
    entidades = EntidadRepository(session_factory)
    for valor in ("münchen.de", IDNA):
        entidades.create(EntidadCreateData(tipo=TipoEntidad.DOMINIO, valor=valor, valor_normalizado=valor))

    for _ in range(3 * motor.pool.size()):
        with pytest.raises(CoincidenciaAmbiguaError):
            repo.incorporar_lote(_lote(dominio=IDNA))
        assert motor.pool.checkedout() == 0

