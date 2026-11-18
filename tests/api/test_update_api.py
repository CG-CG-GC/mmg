from unittest.mock import Mock

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.persistence.errors import IntegrityConstraintError
from app.persistence.repositories import RelacionUpdateData


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "update-api.sqlite3")) as test_client:
        yield test_client


def _crear_entidad(client: TestClient, tipo: str, valor: str) -> int:
    response = client.post(
        "/api/v1/entidades",
        json={"tipo": tipo, "valor": valor, "valor_normalizado": valor.lower()},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _crear_relacion(client: TestClient, origen_id: int, destino_id: int) -> dict:
    response = client.post(
        "/api/v1/relaciones",
        json={
            "origen_id": origen_id,
            "destino_id": destino_id,
            "tipo": "TRABAJA_EN",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_actualiza_entidad_y_refleja_el_cambio_en_grafo(client: TestClient) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    empresa_id = _crear_entidad(client, "ORGANIZACION", "Empresa")
    relacion = _crear_relacion(client, ana_id, empresa_id)
    evidence_response = client.post(
        f"/api/v1/relaciones/{relacion['id']}/evidencias",
        json={"fuente": "Registro"},
    )
    assert evidence_response.status_code == 201

    response = client.put(
        f"/api/v1/entidades/{ana_id}",
        json={
            "tipo": "PERSONA",
            "valor": "Ana Pérez",
            "valor_normalizado": "ana perez",
            "descripcion": "Actualizada",
            "metadata": {"origen": "edición"},
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == ana_id
    assert response.json()["valor"] == "Ana Pérez"
    graph = client.app.state.graph_service.graph
    assert graph.buscar_entidad(ana_id).valor == "Ana Pérez"
    assert graph.buscar_relacion(relacion["id"]).evidencias[0].fuente == "Registro"


def test_actualiza_relacion_conservando_id_evidencias_y_direccion(
    client: TestClient,
) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    empresa_id = _crear_entidad(client, "ORGANIZACION", "Empresa")
    dominio_id = _crear_entidad(client, "DOMINIO", "empresa.test")
    relacion = _crear_relacion(client, ana_id, empresa_id)
    evidence_response = client.post(
        f"/api/v1/relaciones/{relacion['id']}/evidencias",
        json={"fuente": "Registro"},
    )
    assert evidence_response.status_code == 201

    response = client.put(
        f"/api/v1/relaciones/{relacion['id']}",
        json={
            "origen_id": dominio_id,
            "destino_id": ana_id,
            "tipo": "APUNTA_A",
            "descripcion": "Editada",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == relacion["id"]
    assert (body["origen_id"], body["destino_id"]) == (dominio_id, ana_id)
    assert body["evidencias"][0]["fuente"] == "Registro"
    graph_relation = client.app.state.graph_service.graph.buscar_relacion(relacion["id"])
    assert (graph_relation.origen_id, graph_relation.destino_id) == (dominio_id, ana_id)
    assert client.app.state.graph_service.graph.buscar_camino(dominio_id, ana_id).relaciones_camino == [
        relacion["id"]
    ]


def test_actualizar_referencia_inexistente_devuelve_404_antes_de_persistir(
    client: TestClient, monkeypatch
) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    empresa_id = _crear_entidad(client, "ORGANIZACION", "Empresa")
    relacion = _crear_relacion(client, ana_id, empresa_id)
    repository_update = client.app.state.graph_service._relaciones.update
    update_spy = Mock(wraps=repository_update)
    monkeypatch.setattr(client.app.state.graph_service._relaciones, "update", update_spy)

    response = client.put(
        f"/api/v1/relaciones/{relacion['id']}",
        json={
            "origen_id": ana_id,
            "destino_id": 99999,
            "tipo": "TRABAJA_EN",
        },
    )

    assert response.status_code == 404
    update_spy.assert_not_called()
    assert client.app.state.graph_service.graph.buscar_relacion(relacion["id"]).destino_id == (
        empresa_id
    )


def test_fk_detectada_durante_escritura_devuelve_404_y_no_publica_grafo_inconsistente(
    client: TestClient, monkeypatch
) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    empresa_id = _crear_entidad(client, "ORGANIZACION", "Empresa")
    relacion = _crear_relacion(client, ana_id, empresa_id)
    graph_service = client.app.state.graph_service
    repository_update = graph_service._relaciones.update
    grafo_anterior = graph_service.graph

    def trigger_fk_error(relation_id: int, data: RelacionUpdateData):
        return repository_update(
            relation_id,
            RelacionUpdateData(
                origen_id=data.origen_id,
                destino_id=99999,
                tipo=data.tipo,
                descripcion=data.descripcion,
                fecha=data.fecha,
            ),
        )

    monkeypatch.setattr(graph_service._relaciones, "update", trigger_fk_error)
    response = client.put(
        f"/api/v1/relaciones/{relacion['id']}",
        json={
            "origen_id": ana_id,
            "destino_id": empresa_id,
            "tipo": "UTILIZA",
        },
    )

    assert response.status_code == 404
    assert graph_service.graph is grafo_anterior
    assert graph_service.graph.buscar_relacion(relacion["id"]).destino_id == empresa_id


def test_update_clasifica_recurso_ausente_unicidad_y_entrada_invalida(
    client: TestClient,
) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    otro_id = _crear_entidad(client, "PERSONA", "Beto")

    missing = client.put(
        "/api/v1/entidades/99999",
        json={
            "tipo": "PERSONA",
            "valor": "Ausente",
            "valor_normalizado": "ausente",
        },
    )
    assert missing.status_code == 404

    duplicate = client.put(
        f"/api/v1/entidades/{otro_id}",
        json={
            "tipo": "PERSONA",
            "valor": "ANA",
            "valor_normalizado": "ana",
        },
    )
    assert duplicate.status_code == 409
    assert client.get(f"/api/v1/entidades/{ana_id}").json()["valor"] == "Ana"

    invalid = client.put(
        "/api/v1/relaciones/1",
        json={"origen_id": ana_id, "destino_id": 0, "tipo": "UTILIZA"},
    )
    assert invalid.status_code == 422

    blank_entity = client.put(
        f"/api/v1/entidades/{ana_id}",
        json={
            "tipo": "PERSONA",
            "valor": "   ",
            "valor_normalizado": "ana",
        },
    )
    assert blank_entity.status_code == 422


def test_integridad_no_clasificada_no_se_convierte_en_404_o_409(
    client: TestClient, monkeypatch
) -> None:
    ana_id = _crear_entidad(client, "PERSONA", "Ana")
    empresa_id = _crear_entidad(client, "ORGANIZACION", "Empresa")
    relacion = _crear_relacion(client, ana_id, empresa_id)

    def raise_unclassified_integrity(_relation_id, _data):
        raise IntegrityConstraintError("Restricción de integridad no clasificada.")

    monkeypatch.setattr(
        client.app.state.graph_service._relaciones,
        "update",
        raise_unclassified_integrity,
    )
    response = client.put(
        f"/api/v1/relaciones/{relacion['id']}",
        json={
            "origen_id": ana_id,
            "destino_id": empresa_id,
            "tipo": "UTILIZA",
        },
    )

    assert response.status_code == 500
