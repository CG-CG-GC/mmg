"""Publicación del grafo bajo escrituras concurrentes dentro de un proceso.

Las pausas usan eventos explícitos, no sleep(). El único tiempo de espera es una
comprobación negativa: otra reconstrucción no debe empezar mientras la primera
mantiene la publicación. Esa comprobación falla con la versión sin cerrojo.
"""

import threading
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.application.incorporacion_dns import (
    IncorporacionDnsService,
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
from app.persistence.graph_loader import load_graph_from_database
from app.persistence.incorporacion_dns import IncorporacionDnsRepository
from app.persistence.repositories import (
    EntidadCreateData,
    EntidadRepository,
    EvidenciaRepository,
    RelacionRepository,
)
from app.persistence.schema import (
    EntidadModel,
    EvidenciaModel,
    RelacionModel,
    initialize_database,
)

ESPERA = 10
NEGATIVA = 0.3
AHORA = datetime(2026, 11, 18, 12, tzinfo=UTC)


class CargadorControlado:
    """Carga real del grafo. Puede pausar la llamada n después de leer la base."""

    def __init__(self, pausar_en=None, fallar_en_pausa=False):
        self._contador = threading.Lock()
        self.llamadas = 0
        self.pausar_en = pausar_en
        self.fallar_en_pausa = fallar_en_pausa
        self.inicio = [threading.Event() for _ in range(20)]
        self.pausada = threading.Event()
        self.liberar = threading.Event()

    def __call__(self, session_factory):
        with self._contador:
            self.llamadas += 1
            n = self.llamadas
        self.inicio[n - 1].set()
        grafo = load_graph_from_database(session_factory)
        if n == self.pausar_en:
            self.pausada.set()
            if not self.liberar.wait(timeout=ESPERA):
                raise AssertionError("la prueba no liberó la reconstrucción pausada")
            if self.fallar_en_pausa:
                raise RuntimeError("fallo simulado de reconstrucción")
        return grafo


@pytest.fixture
def ctx(tmp_path):
    engine = create_sqlite_engine(sqlite_url_from_path(tmp_path / "concurrencia.sqlite3"))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)
    cargador = CargadorControlado()
    servicio = GraphApplicationService(
        session_factory=session_factory,
        entidad_repository=EntidadRepository(session_factory),
        relacion_repository=RelacionRepository(session_factory),
        evidencia_repository=EvidenciaRepository(session_factory),
        graph_loader=cargador,
    )
    incorporacion = IncorporacionDnsService(
        IncorporacionDnsRepository(session_factory),
        refrescar_grafo=servicio.refrescar_tras_escritura,
    )
    yield SimpleNamespace(
        engine=engine,
        session_factory=session_factory,
        servicio=servicio,
        incorporacion=incorporacion,
        cargador=cargador,
    )
    engine.dispose()


def _hilo(funcion, *args):
    """Ejecuta en un hilo y guarda la excepción para revisarla en la prueba."""
    resultado = SimpleNamespace(error=None, valor=None)

    def ejecutar():
        try:
            resultado.valor = funcion(*args)
        except BaseException as exc:  # Se revisa en el hilo principal.
            resultado.error = exc

    hilo = threading.Thread(target=ejecutar, daemon=True)
    hilo.start()
    return hilo, resultado


def _cerrar(hilo, resultado):
    hilo.join(ESPERA)
    assert not hilo.is_alive(), "un hilo quedó bloqueado"
    assert resultado.error is None, resultado.error


def _ids_bd(ctx):
    with ctx.session_factory() as session:
        entidades = set(session.scalars(select(EntidadModel.id)).all())
        relaciones = set(session.scalars(select(RelacionModel.id)).all())
        evidencias = set(session.scalars(select(EvidenciaModel.id)).all())
    return entidades, relaciones, evidencias


def _ids_grafo(grafo):
    entidades = set(grafo._entidades_por_id)
    relaciones = [r for lista in grafo._adyacencia.values() for r in lista]
    ids_relaciones = {r.id for r in relaciones}
    evidencias = {e.id for relacion in relaciones for e in relacion.evidencias}
    return entidades, ids_relaciones, evidencias


def _afirmar_grafo_igual_a_bd(ctx):
    assert _ids_grafo(ctx.servicio.graph) == _ids_bd(ctx)


def _crear(ctx, valor):
    return EntidadRepository(ctx.session_factory).create(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor=valor, valor_normalizado=valor.lower())
    )


def _solicitud(valor_ip):
    return SolicitudIncorporacionDns(
        dominio="example.com",
        registros=(
            RegistroSolicitadoDns(tipo="A", valor=valor_ip, fuente="google-public-dns-doh", consultado_en=AHORA),
        ),
    )


def _crear_servicio(ctx, valor):
    return ctx.servicio.crear_entidad(
        EntidadCreateData(tipo=TipoEntidad.PERSONA, valor=valor, valor_normalizado=valor.lower())
    )


def test_reconstruccion_antigua_no_sobrescribe_una_mas_reciente(ctx):
    ctx.cargador.pausar_en = 2  # La llamada 1 fue la del constructor.
    _crear(ctx, "Ana")
    hilo1, res1 = _hilo(ctx.servicio.refrescar_tras_escritura)
    try:
        assert ctx.cargador.pausada.wait(ESPERA), "la primera reconstrucción no llegó a leer"
        _crear(ctx, "Beto")  # Commit posterior a la lectura de la primera reconstrucción.
        hilo2, res2 = _hilo(ctx.servicio.refrescar_tras_escritura)
        # Con el cerrojo, la segunda reconstrucción espera a que la primera publique.
        assert not ctx.cargador.inicio[2].wait(NEGATIVA), "la segunda carga no esperó la publicación"
    finally:
        ctx.cargador.liberar.set()
    _cerrar(hilo1, res1)
    _cerrar(hilo2, res2)

    _afirmar_grafo_igual_a_bd(ctx)
    assert len(_ids_bd(ctx)[0]) == 2


def test_fallo_de_una_reconstruccion_no_deja_fuera_el_commit_de_otra(ctx):
    ctx.cargador.pausar_en = 2
    ctx.cargador.fallar_en_pausa = True
    _crear(ctx, "Ana")
    hilo1, res1 = _hilo(ctx.servicio.refrescar_tras_escritura)
    try:
        assert ctx.cargador.pausada.wait(ESPERA)
        _crear(ctx, "Beto")
        hilo2, res2 = _hilo(ctx.servicio.refrescar_tras_escritura)
        assert not ctx.cargador.inicio[2].wait(NEGATIVA)
    finally:
        ctx.cargador.liberar.set()
    hilo1.join(ESPERA)
    hilo2.join(ESPERA)

    assert isinstance(res1.error, RuntimeError)  # La reconstrucción fallida informa su error.
    assert res2.error is None
    _afirmar_grafo_igual_a_bd(ctx)


def test_incorporacion_y_crud_concurrentes_publican_un_grafo_completo(ctx):
    ctx.cargador.pausar_en = 2
    hilo1, res1 = _hilo(ctx.incorporacion.incorporar, _solicitud("192.0.2.1"))
    try:
        assert ctx.cargador.pausada.wait(ESPERA)
        hilo2, res2 = _hilo(_crear_servicio, ctx, "Carla")
        assert not ctx.cargador.inicio[2].wait(NEGATIVA)
    finally:
        ctx.cargador.liberar.set()
    _cerrar(hilo1, res1)
    _cerrar(hilo2, res2)

    _afirmar_grafo_igual_a_bd(ctx)
    entidades, relaciones, evidencias = _ids_bd(ctx)
    assert len(entidades) == 3  # Dominio, IP y Carla.
    assert len(relaciones) == 1
    assert len(evidencias) == 1
    dominio_id = res1.valor.dominio.id
    ip_id = res1.valor.registros[0].entidad.id
    grafo = ctx.servicio.graph
    assert ip_id in grafo.bfs(dominio_id).orden_recorrido  # Regresión de BFS.
    assert grafo.buscar_camino(dominio_id, ip_id).encontrado  # Regresión de camino.


def test_escrituras_crud_simultaneas_no_pierden_entidades(ctx):
    total = 6
    barrera = threading.Barrier(total)

    def crear(indice):
        barrera.wait(ESPERA)
        return _crear_servicio(ctx, f"Persona {indice}")

    hilos = [_hilo(crear, indice) for indice in range(total)]
    for hilo, resultado in hilos:
        _cerrar(hilo, resultado)

    assert len(_ids_bd(ctx)[0]) == total
    _afirmar_grafo_igual_a_bd(ctx)


def test_incorporaciones_identicas_simultaneas_reutilizan_el_lote(ctx):
    barrera = threading.Barrier(2)

    def incorporar():
        barrera.wait(ESPERA)
        return ctx.incorporacion.incorporar(_solicitud("192.0.2.1"))

    hilos = [_hilo(incorporar) for _ in range(2)]
    resultados = []
    for hilo, resultado in hilos:
        _cerrar(hilo, resultado)
        resultados.append(resultado.valor)

    estados_dominio = sorted(r.dominio.estado for r in resultados)
    estados_entidad = sorted(r.registros[0].entidad.estado for r in resultados)
    estados_relacion = sorted(r.registros[0].relacion.estado for r in resultados)
    estados_evidencia = sorted(r.registros[0].evidencia.estado for r in resultados)
    assert estados_dominio == ["creada", "reutilizada"]
    assert estados_entidad == ["creada", "reutilizada"]
    assert estados_relacion == ["creada", "reutilizada"]
    assert estados_evidencia == ["creada", "reutilizada"]
    entidades, relaciones, evidencias = _ids_bd(ctx)
    assert (len(entidades), len(relaciones), len(evidencias)) == (2, 1, 1)
    _afirmar_grafo_igual_a_bd(ctx)


def _servicio_nuevo(ruta):
    engine = create_sqlite_engine(sqlite_url_from_path(ruta))
    session_factory = create_session_factory(engine)
    initialize_database(engine, session_factory)
    cargador = CargadorControlado()
    servicio = GraphApplicationService(
        session_factory=session_factory,
        entidad_repository=EntidadRepository(session_factory),
        relacion_repository=RelacionRepository(session_factory),
        evidencia_repository=EvidenciaRepository(session_factory),
        graph_loader=cargador,
    )
    return engine, servicio, cargador


def test_instancias_distintas_del_proceso_comparten_el_cerrojo(ctx, tmp_path):
    from app.application import service as modulo_servicio

    engine_otro, otro, cargador_otro = _servicio_nuevo(tmp_path / "otro.sqlite3")
    try:
        with modulo_servicio._PUBLICACION_GRAFO:
            hilo1, res1 = _hilo(ctx.servicio.refrescar_tras_escritura)
            hilo2, res2 = _hilo(otro.refrescar_tras_escritura)
            # Ninguna instancia debe cargar mientras otra mantiene el cerrojo del proceso.
            assert not ctx.cargador.inicio[1].wait(NEGATIVA)
            assert not cargador_otro.inicio[1].wait(NEGATIVA)
        _cerrar(hilo1, res1)
        _cerrar(hilo2, res2)
    finally:
        engine_otro.dispose()
