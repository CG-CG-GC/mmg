"""Dominios Unicode con transformaciones IDNA no equivalentes (QA-06-01) y CRUD ambiguo (QA-06-03).

Las respuestas de red quedan bloqueadas: si una entrada rechazada llegara al
transporte HTTP del proveedor real, la prueba falla.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.application.dns_lookup import DnsLookupService
from app.integrations.dns_google import GoogleDohProvider, RespuestaCrudaDns

STRASSE_SHARP_S = "straße.de"
MUNCHEN_UNICODE = "münchen.de"
MUNCHEN_PUNYCODE = "xn--mnchen-3ya.de"
A_LABEL = "xn--strae-oqa.de"
URL_INCORPORACION = "/api/v1/osint/dns/incorporaciones"


class ProveedorRegistrador:
    fuente = "falso"

    def __init__(self):
        self.llamadas = []

    def consultar(self, dominio, tipo):
        self.llamadas.append((dominio, tipo))
        return RespuestaCrudaDns(0, ())


def _sin_red(monkeypatch):
    def fallar(*_args, **_kwargs):
        raise AssertionError("una entrada rechazada no debe llegar a la red")

    monkeypatch.setattr("urllib.request.urlopen", fallar)


def _cuerpo(dominio, valor="192.0.2.1"):
    return {
        "dominio": dominio,
        "registros": [
            {
                "tipo": "A",
                "valor": valor,
                "fuente": "google-public-dns-doh",
                "consultado_en": "2026-11-18T12:00:00Z",
            }
        ],
    }


@pytest.fixture
def app_real(tmp_path):
    app = create_app(tmp_path / "dns-idna.sqlite3")
    app.state.dns_service = DnsLookupService(GoogleDohProvider())
    return app


@pytest.fixture
def client(app_real):
    with TestClient(app_real) as test_client:
        yield test_client


@pytest.mark.parametrize("dominio", [STRASSE_SHARP_S, "straße.de.", " STRAßE.de "])
def test_consulta_dns_rechaza_sharp_s_sin_red(client, monkeypatch, dominio):
    _sin_red(monkeypatch)

    response = client.post("/api/v1/osint/dns", json={"dominio": dominio, "tipos": ["A"]})

    assert response.status_code == 422, response.text
    assert "xn--" in response.json()["detail"]
    assert client.get("/api/v1/entidades").json() == []


def test_consulta_dns_acepta_a_label_sin_sustituirla(tmp_path):
    proveedor = ProveedorRegistrador()
    app = create_app(tmp_path / "dns-a-label.sqlite3")
    app.state.dns_service = DnsLookupService(proveedor)
    with TestClient(app) as client:
        response = client.post("/api/v1/osint/dns", json={"dominio": A_LABEL, "tipos": ["A"]})

    assert response.status_code == 200, response.text
    assert response.json()["dominio"] == A_LABEL
    assert proveedor.llamadas == [(A_LABEL, "A")]


@pytest.mark.parametrize("dominio", ["\u0130stanbul.tr", "xn--bogus.de", "xn--invalid-zz.de"])
def test_consulta_rechaza_i_con_punto_y_a_labels_invalidas_sin_llamar_proveedor(app_real, dominio):
    proveedor = ProveedorRegistrador()
    app_real.state.dns_service = DnsLookupService(proveedor)

    with TestClient(app_real) as client:
        response = client.post("/api/v1/osint/dns", json={"dominio": dominio, "tipos": ["A"]})

    assert response.status_code == 422, response.text
    assert proveedor.llamadas == []


def test_incorporacion_rechaza_sharp_s_sin_escribir(client, monkeypatch):
    _sin_red(monkeypatch)

    response = client.post(URL_INCORPORACION, json=_cuerpo(STRASSE_SHARP_S))

    assert response.status_code == 422, response.text
    assert client.get("/api/v1/entidades").json() == []
    assert client.get("/api/v1/relaciones").json() == []


@pytest.mark.parametrize("dominio", ["\u0130stanbul.tr", "xn--bogus.de", "xn--invalid-zz.de"])
def test_incorporacion_rechaza_i_con_punto_y_a_labels_invalidas_sin_escribir(client, dominio):
    response = client.post(URL_INCORPORACION, json=_cuerpo(dominio))

    assert response.status_code == 422, response.text
    assert client.get("/api/v1/entidades").json() == []
    assert client.get("/api/v1/relaciones").json() == []


def test_incorporacion_no_reutiliza_una_entidad_de_otro_dominio(client):
    creada = client.post(
        "/api/v1/entidades",
        json={"tipo": "DOMINIO", "valor": STRASSE_SHARP_S, "valor_normalizado": STRASSE_SHARP_S},
    )
    assert creada.status_code == 201

    response = client.post(URL_INCORPORACION, json=_cuerpo("strasse.de"))

    assert response.status_code == 200, response.text
    assert response.json()["dominio"]["estado"] == "creada"
    valores = {e["valor"] for e in client.get("/api/v1/entidades").json() if e["tipo"] == "DOMINIO"}
    assert valores == {STRASSE_SHARP_S, "strasse.de"}


def test_incorporacion_guarda_a_label_tal_cual(client):
    response = client.post(URL_INCORPORACION, json=_cuerpo(A_LABEL))

    assert response.status_code == 200, response.text
    valores = {e["valor"] for e in client.get("/api/v1/entidades").json() if e["tipo"] == "DOMINIO"}
    assert valores == {A_LABEL}


def test_crud_con_unicode_y_punycode_equivalentes_responde_409_sin_escribir(client):
    for valor in (MUNCHEN_UNICODE, MUNCHEN_PUNYCODE):
        creada = client.post(
            "/api/v1/entidades",
            json={"tipo": "DOMINIO", "valor": valor, "valor_normalizado": valor},
        )
        assert creada.status_code == 201, creada.text

    response = client.post(URL_INCORPORACION, json=_cuerpo("MÜNCHEN.de."))

    assert response.status_code == 409, response.text
    assert "equivalentes" in response.json()["detail"]
    assert len(client.get("/api/v1/entidades").json()) == 2
    assert client.get("/api/v1/relaciones").json() == []


@pytest.mark.parametrize("dominio", ["İstanbul.tr", "xn--bogus.de", "xn--invalid-zz.de", "xn--a.com"])
def test_rechazos_idna_no_llegan_a_la_red_ni_escriben(client, monkeypatch, dominio):
    _sin_red(monkeypatch)

    consulta = client.post("/api/v1/osint/dns", json={"dominio": dominio, "tipos": ["A"]})
    incorporacion = client.post(URL_INCORPORACION, json=_cuerpo(dominio))

    assert consulta.status_code == 422, consulta.text
    assert incorporacion.status_code == 422, incorporacion.text
    assert client.get("/api/v1/entidades").json() == []
    assert client.get("/api/v1/relaciones").json() == []


def test_lote_con_una_a_label_invalida_no_escribe_nada_aunque_otra_sea_valida(client):
    cuerpo = {
        "dominio": "xn--bogus.de",
        "registros": [
            _cuerpo("example.com")["registros"][0],
            {
                "tipo": "AAAA",
                "valor": "2001:db8::1",
                "fuente": "google-public-dns-doh",
                "consultado_en": "2026-11-18T12:00:00Z",
            },
        ],
    }

    response = client.post(URL_INCORPORACION, json=cuerpo)

    assert response.status_code == 422, response.text
    assert client.get("/api/v1/entidades").json() == []


def test_incorporacion_con_a_label_valida_es_idempotente(client):
    primera = client.post(URL_INCORPORACION, json=_cuerpo(MUNCHEN_PUNYCODE))
    segunda = client.post(URL_INCORPORACION, json=_cuerpo(MUNCHEN_PUNYCODE))

    assert primera.status_code == 200, primera.text
    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["dominio"]["estado"] == "reutilizada"
    assert segunda.json()["dominio"]["id"] == primera.json()["dominio"]["id"]
    assert len(client.get("/api/v1/entidades").json()) == 2


def test_incorporacion_no_reutiliza_entidad_con_mayuscula_turca(client):
    creada = client.post(
        "/api/v1/entidades",
        json={"tipo": "DOMINIO", "valor": "İstanbul.tr", "valor_normalizado": "İstanbul.tr"},
    )
    assert creada.status_code == 201

    response = client.post(URL_INCORPORACION, json=_cuerpo("istanbul.tr"))

    assert response.status_code == 200, response.text
    assert response.json()["dominio"]["estado"] == "creada"
    valores = {e["valor"] for e in client.get("/api/v1/entidades").json() if e["tipo"] == "DOMINIO"}
    assert valores == {"İstanbul.tr", "istanbul.tr"}


def test_consulta_envia_a_label_en_minusculas_al_proveedor(tmp_path):
    proveedor = ProveedorRegistrador()
    app = create_app(tmp_path / "dns-mayusculas.sqlite3")
    app.state.dns_service = DnsLookupService(proveedor)
    with TestClient(app) as client:
        response = client.post("/api/v1/osint/dns", json={"dominio": "XN--STRAE-OQA.DE", "tipos": ["A"]})

    assert response.status_code == 200, response.text
    assert proveedor.llamadas == [(A_LABEL, "A")]
