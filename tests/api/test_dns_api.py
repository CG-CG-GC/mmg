from datetime import UTC, datetime

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.application.dns_lookup import DnsLookupService
from app.integrations.dns_google import ProveedorDnsTimeoutError, RespuestaCrudaDns

AHORA = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)


class ProveedorFalso:
    fuente = "falso"

    def __init__(self):
        self.llamadas = []

    def consultar(self, dominio, tipo):
        self.llamadas.append((dominio, tipo))
        if tipo == "A":
            return RespuestaCrudaDns(0, ((1, "93.184.216.34"), (1, "93.184.216.34")))
        if tipo == "MX":
            return RespuestaCrudaDns(0, ((15, "10 mail.example.com."),))
        if tipo == "NS":
            raise ProveedorDnsTimeoutError()
        return RespuestaCrudaDns(3, ())


@pytest.fixture
def proveedor():
    return ProveedorFalso()


@pytest.fixture
def client(tmp_path, proveedor):
    app = create_app(tmp_path / "dns-api.sqlite3")
    app.state.dns_service = DnsLookupService(proveedor, reloj=lambda: AHORA)
    with TestClient(app) as test_client:
        yield test_client


def test_consulta_devuelve_contrato_con_errores_parciales(client, proveedor):
    response = client.post("/api/v1/osint/dns", json={"dominio": "Example.com"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"dominio", "fuente", "consultado_en", "registros", "estados"}
    assert body["dominio"] == "example.com"
    assert body["fuente"] == "falso"
    assert body["consultado_en"] == "2025-01-01T12:00:00Z"
    assert body["registros"] == [
        {
            "tipo": "A",
            "valor": "93.184.216.34",
            "estado": "encontrado",
            "fuente": "falso",
            "consultado_en": "2025-01-01T12:00:00Z",
            "prioridad": None,
        },
        {
            "tipo": "MX",
            "valor": "mail.example.com",
            "estado": "encontrado",
            "fuente": "falso",
            "consultado_en": "2025-01-01T12:00:00Z",
            "prioridad": 10,
        },
    ]
    assert body["estados"] == [
        {"tipo": "A", "estado": "ok", "descartados": 0},
        {"tipo": "AAAA", "estado": "dominio_inexistente", "descartados": 0},
        {"tipo": "CNAME", "estado": "dominio_inexistente", "descartados": 0},
        {"tipo": "MX", "estado": "ok", "descartados": 0},
        {"tipo": "NS", "estado": "error_timeout", "descartados": 0},
    ]
    assert [t for _, t in proveedor.llamadas] == ["A", "AAAA", "CNAME", "MX", "NS"]


def test_consulta_con_tipos_explicitos(client, proveedor):
    response = client.post("/api/v1/osint/dns", json={"dominio": "example.com", "tipos": ["mx"]})
    assert response.status_code == 200
    assert [e["tipo"] for e in response.json()["estados"]] == ["MX"]
    assert proveedor.llamadas == [("example.com", "MX")]


@pytest.mark.parametrize(
    "payload",
    [
        {"dominio": "http://example.com"},
        {"dominio": "1.2.3.4"},
        {"dominio": "example.com", "tipos": ["TXT"]},
        {"dominio": "example.com", "tipos": []},
        {"dominio": ""},
        {},
    ],
)
def test_entrada_invalida_devuelve_422_sin_consultar(client, proveedor, payload):
    response = client.post("/api/v1/osint/dns", json=payload)
    assert response.status_code == 422
    assert proveedor.llamadas == []


def test_consulta_no_escribe_entidades_relaciones_ni_evidencias(client):
    antes = client.get("/api/v1/grafo").json()
    assert client.post("/api/v1/osint/dns", json={"dominio": "example.com"}).status_code == 200
    assert client.get("/api/v1/grafo").json() == antes
    assert client.get("/api/v1/entidades").json() == []
    assert client.get("/api/v1/relaciones").json() == []
