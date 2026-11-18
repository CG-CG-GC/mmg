import sqlite3
from datetime import UTC, datetime

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.api.main import create_app
from app.application.dns_lookup import DnsLookupService
from app.integrations.dns_google import RespuestaCrudaDns
from app.persistence.graph_loader import load_graph_from_database

AHORA = "2026-11-16T12:00:00Z"
URL = "/api/v1/osint/dns/incorporaciones"


class ProveedorRegistrador:
    fuente = "no-debe-usarse"

    def __init__(self):
        self.llamadas = []

    def consultar(self, dominio, tipo):
        self.llamadas.append((dominio, tipo))
        return RespuestaCrudaDns(0, ())


def _registro(tipo="A", valor="192.0.2.1", fuente="google-public-dns-doh", consultado_en=AHORA):
    return {"tipo": tipo, "valor": valor, "fuente": fuente, "consultado_en": consultado_en}


def _cuerpo(registros=None, dominio="example.com"):
    if registros is None:
        registros = [_registro()]
    return {"dominio": dominio, "registros": registros}


@pytest.fixture
def proveedor():
    return ProveedorRegistrador()


@pytest.fixture
def app(tmp_path, proveedor):
    app = create_app(tmp_path / "incorporacion-api.sqlite3")
    app.state.dns_service = DnsLookupService(proveedor, reloj=lambda: datetime(2026, 11, 16, tzinfo=UTC))
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def _entidades(client):
    return client.get("/api/v1/entidades").json()


def _relaciones(client):
    return client.get("/api/v1/relaciones").json()


def test_incorporacion_devuelve_contrato_y_no_consulta_dns(client, proveedor):
    response = client.post(URL, json=_cuerpo())

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"dominio", "resultados"}
    assert body["dominio"]["estado"] == "creada"
    assert body["resultados"][0]["tipo"] == "A"
    assert body["resultados"][0]["valor"] == "192.0.2.1"
    assert body["resultados"][0]["entidad"]["estado"] == "creada"
    assert body["resultados"][0]["relacion"]["estado"] == "creada"
    assert body["resultados"][0]["evidencia"]["estado"] == "creada"
    assert body["resultados"][0]["procedencia"] == {
        "declarada_por": "cliente",
        "fuente": "google-public-dns-doh",
        "consultado_en": AHORA,
    }
    assert proveedor.llamadas == []


def test_a_y_aaaa_con_idna_y_normalizacion(client):
    response = client.post(
        URL,
        json=_cuerpo(
            [_registro("A", "192.0.2.1"), _registro("AAAA", "2001:DB8::1")],
            dominio="München.DE.",
        ),
    )

    assert response.status_code == 200, response.text
    resultados = response.json()["resultados"]
    assert [r["valor"] for r in resultados] == ["192.0.2.1", "2001:db8::1"]
    pares = {(e["tipo"], e["valor"]) for e in _entidades(client)}
    assert ("DOMINIO", "xn--mnchen-3ya.de") in pares
    assert ("IP", "2001:db8::1") in pares


def test_reintento_identico_reutiliza_y_no_duplica_evidencias(client):
    primero = client.post(URL, json=_cuerpo()).json()
    segundo = client.post(URL, json=_cuerpo())

    assert segundo.status_code == 200
    cuerpo = segundo.json()
    assert cuerpo["dominio"] == {"id": primero["dominio"]["id"], "estado": "reutilizada"}
    assert cuerpo["resultados"][0]["entidad"]["estado"] == "reutilizada"
    assert cuerpo["resultados"][0]["relacion"]["estado"] == "reutilizada"
    assert cuerpo["resultados"][0]["evidencia"]["estado"] == "reutilizada"
    assert cuerpo["resultados"][0]["evidencia"]["id"] == primero["resultados"][0]["evidencia"]["id"]
    assert len(_entidades(client)) == 2
    relacion = _relaciones(client)[0]
    assert len(relacion["evidencias"]) == 1


INVALIDOS = [
    pytest.param({"dominio": "example.com", "registros": []}, id="lote_vacio"),
    pytest.param({"dominio": "example.com"}, id="sin_registros"),
    pytest.param(_cuerpo(dominio="http://example.com"), id="dominio_con_esquema"),
    pytest.param(_cuerpo(dominio="1.2.3.4"), id="dominio_ip"),
    pytest.param(_cuerpo([_registro(tipo="TXT")]), id="tipo_no_admitido"),
    pytest.param(_cuerpo([_registro(tipo="CNAME", valor="ejemplo.com")]), id="tipo_cname"),
    pytest.param(_cuerpo([_registro("A", "2001:db8::1")]), id="a_con_ipv6"),
    pytest.param(_cuerpo([_registro("AAAA", "192.0.2.1")]), id="aaaa_con_ipv4"),
    pytest.param(_cuerpo([_registro(valor="no-es-ip")]), id="ip_malformada"),
    pytest.param(_cuerpo([_registro("AAAA", "fe80::1%eth0")]), id="ipv6_con_zona"),
    pytest.param(_cuerpo([_registro(fuente="")]), id="fuente_vacia"),
    pytest.param(_cuerpo([_registro(fuente="x" * 101)]), id="fuente_demasiado_larga"),
    pytest.param(_cuerpo([_registro(consultado_en="2026-11-16T12:00:00")]), id="fecha_sin_zona"),
    pytest.param(
        _cuerpo([{"tipo": "A", "valor": "192.0.2.1", "consultado_en": AHORA}]), id="falta_fuente"
    ),
    pytest.param(
        _cuerpo([_registro(valor=f"192.0.2.{i}") for i in range(1, 102)]), id="lote_excesivo"
    ),
]


@pytest.mark.parametrize("payload", INVALIDOS)
def test_payload_invalido_responde_422_sin_escribir(client, payload):
    response = client.post(URL, json=payload)

    assert response.status_code == 422, response.text
    assert _entidades(client) == []
    assert _relaciones(client) == []


def test_coincidencia_ambigua_responde_409_sin_escribir(client):
    primera = client.post(
        "/api/v1/entidades",
        json={"tipo": "DOMINIO", "valor": "Example.com.", "valor_normalizado": "example.com."},
    )
    segunda = client.post(
        "/api/v1/entidades",
        json={"tipo": "DOMINIO", "valor": "EXAMPLE.com", "valor_normalizado": "EXAMPLE.com"},
    )
    assert primera.status_code == 201 and segunda.status_code == 201

    response = client.post(URL, json=_cuerpo())

    assert response.status_code == 409, response.text
    assert "equivalentes" in response.json()["detail"]
    assert len(_entidades(client)) == 2
    assert _relaciones(client) == []


def test_sqlite_ocupado_responde_503_sin_escritura(client, app, tmp_path):
    def busy_timeout_corto(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=50")
        cursor.close()

    event.listen(app.state.engine, "connect", busy_timeout_corto)
    app.state.engine.dispose()
    bloqueo = sqlite3.connect(tmp_path / "incorporacion-api.sqlite3", isolation_level=None)
    bloqueo.execute("BEGIN IMMEDIATE")
    try:
        response = client.post(URL, json=_cuerpo())
    finally:
        bloqueo.execute("ROLLBACK")
        bloqueo.close()

    assert response.status_code == 503, response.text
    assert "ocupada" in response.json()["detail"]
    assert _entidades(client) == []
    assert _relaciones(client) == []


def test_fallo_de_reconstruccion_responde_503_con_persistencia_confirmada(client, app):
    servicio_grafo = app.state.graph_service

    def cargador_fallido(_):
        raise RuntimeError("fallo simulado de reconstrucción")

    # Atributo privado: solo para simular el fallo posterior al commit.
    servicio_grafo._graph_loader = cargador_fallido
    try:
        response = client.post(URL, json=_cuerpo())
    finally:
        servicio_grafo._graph_loader = load_graph_from_database

    assert response.status_code == 503, response.text
    cuerpo = response.json()
    assert cuerpo["persistencia"] == "confirmada"
    assert "sí se guardaron" in cuerpo["detail"]
    assert "rollback" not in cuerpo["detail"].lower()
    assert len(_entidades(client)) == 2
    assert len(_relaciones(client)) == 1

    reintento = client.post(URL, json=_cuerpo())

    assert reintento.status_code == 200, reintento.text
    assert reintento.json()["dominio"]["estado"] == "reutilizada"
    assert len(_relaciones(client)[0]["evidencias"]) == 1


def test_endpoints_existentes_siguen_funcionando(client, app, proveedor):
    crear = client.post(
        "/api/v1/entidades",
        json={"tipo": "PERSONA", "valor": "Ana", "valor_normalizado": "ana"},
    )
    assert crear.status_code == 201
    assert client.get("/api/v1/grafo").status_code == 200

    consulta = client.post("/api/v1/osint/dns", json={"dominio": "example.com", "tipos": ["A"]})
    assert consulta.status_code == 200, consulta.text
    assert proveedor.llamadas == [("example.com", "A")]
    assert [e["valor"] for e in _entidades(client)] == ["Ana"]

    incorporacion = client.post(URL, json=_cuerpo())
    assert incorporacion.status_code == 200, incorporacion.text
    assert len(_entidades(client)) == 3
