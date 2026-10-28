from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.persistence.errors import GraphReconstructionError


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "api.sqlite3")) as test_client:
        yield test_client


def test_health_y_documentacion_openapi(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/openapi.json").status_code == 200


def test_crud_basico_grafo_y_algoritmos_con_sqlite_real(client):
    ana = client.post(
        "/api/v1/entidades",
        json={
            "tipo": "PERSONA",
            "valor": "Ana",
            "valor_normalizado": "Ana",
            "metadata": {"origen": "test"},
        },
    )
    assert ana.status_code == 201, ana.text
    ana_id = ana.json()["id"]
    assert ana.json()["metadata"] == {"origen": "test"}

    sitio = client.post(
        "/api/v1/entidades",
        json={"tipo": "SITIO_WEB", "valor": "example.test", "valor_normalizado": "example.test"},
    )
    assert sitio.status_code == 201, sitio.text
    sitio_id = sitio.json()["id"]

    relation = client.post(
        "/api/v1/relaciones",
        json={"origen_id": ana_id, "destino_id": sitio_id, "tipo": "UTILIZA"},
    )
    assert relation.status_code == 201, relation.text
    relation_id = relation.json()["id"]

    evidence = client.post(
        f"/api/v1/relaciones/{relation_id}/evidencias",
        json={"fuente": "https://example.test/evidencia", "descripcion": "Prueba"},
    )
    assert evidence.status_code == 201, evidence.text

    graph = client.get("/api/v1/grafo")
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) == 2
    assert len(graph.json()["edges"]) == 1
    node_data = graph.json()["nodes"][0]["data"]
    edge_data = graph.json()["edges"][0]["data"]
    assert set(node_data) == {"id", "entity_id", "label", "tipo", "descripcion"}
    assert set(edge_data) == {
        "id",
        "relation_id",
        "source",
        "target",
        "tipo",
        "descripcion",
    }
    assert edge_data["source"] == str(ana_id)
    assert edge_data["target"] == str(sitio_id)
    assert edge_data["relation_id"] == relation_id

    bfs = client.post("/api/v1/algoritmos/bfs", json={"id_inicial": ana_id})
    assert bfs.status_code == 200
    assert bfs.json()["orden_recorrido"] == [ana_id, sitio_id]

    dfs = client.post("/api/v1/algoritmos/dfs", json={"id_inicial": ana_id})
    assert dfs.status_code == 200
    assert dfs.json()["orden_recorrido"] == [ana_id, sitio_id]

    path = client.post(
        "/api/v1/algoritmos/camino",
        json={"id_origen": ana_id, "id_destino": sitio_id},
    )
    assert path.status_code == 200
    assert path.json() == {
        "encontrado": True,
        "entidades_camino": [ana_id, sitio_id],
        "relaciones_camino": [relation_id],
    }

    listed_relation = client.get(f"/api/v1/relaciones/{relation_id}")
    assert listed_relation.status_code == 200
    assert len(listed_relation.json()["evidencias"]) == 1


def test_validaciones_y_recursos_inexistentes(client):
    invalid_entity = client.post(
        "/api/v1/entidades",
        json={"tipo": "NO_EXISTE", "valor": "x", "valor_normalizado": "x"},
    )
    assert invalid_entity.status_code == 422

    missing_entity = client.get("/api/v1/entidades/999")
    assert missing_entity.status_code == 404

    missing_relation = client.post(
        "/api/v1/relaciones",
        json={"origen_id": 999, "destino_id": 1000, "tipo": "UTILIZA"},
    )
    assert missing_relation.status_code == 404


def test_eliminar_entidad_refresca_el_grafo_y_cascada_relacion(client):
    created = []
    for value in ("A", "B"):
        response = client.post(
            "/api/v1/entidades",
            json={"tipo": "PERSONA", "valor": value, "valor_normalizado": value},
        )
        assert response.status_code == 201, response.text
        created.append(response.json()["id"])
    relation = client.post(
        "/api/v1/relaciones",
        json={"origen_id": created[0], "destino_id": created[1], "tipo": "UTILIZA"},
    )
    assert relation.status_code == 201, relation.text

    deleted = client.delete(f"/api/v1/entidades/{created[0]}")
    assert deleted.status_code == 204
    assert client.get("/api/v1/grafo").json() == {
        "nodes": [
            {
                "data": {
                    "id": str(created[1]),
                    "entity_id": created[1],
                    "label": "B",
                    "tipo": "PERSONA",
                    "descripcion": None,
                }
            }
        ],
        "edges": [],
    }


def test_lifespan_cierra_bases_aisladas(tmp_path, monkeypatch):
    first_app = create_app(tmp_path / "first.sqlite3")
    second_app = create_app(tmp_path / "second.sqlite3")
    first_engine = first_app.state.engine
    second_engine = second_app.state.engine
    first_dispose = Mock(wraps=first_engine.dispose)
    second_dispose = Mock(wraps=second_engine.dispose)
    monkeypatch.setattr(first_engine, "dispose", first_dispose)
    monkeypatch.setattr(second_engine, "dispose", second_dispose)

    with TestClient(first_app) as first_client:
        created = first_client.post(
            "/api/v1/entidades",
            json={"tipo": "PERSONA", "valor": "A", "valor_normalizado": "A"},
        )
        assert created.status_code == 201, created.text

    with TestClient(second_app) as second_client:
        assert second_client.get("/api/v1/entidades").json() == []

    first_dispose.assert_called_once_with()
    second_dispose.assert_called_once_with()


def test_crud_de_relaciones_y_respuesta_de_duplicado(client):
    entity_ids = []
    for value in ("A", "B"):
        response = client.post(
            "/api/v1/entidades",
            json={"tipo": "PERSONA", "valor": value, "valor_normalizado": value},
        )
        assert response.status_code == 201, response.text
        entity_ids.append(response.json()["id"])

    assert len(client.get("/api/v1/entidades").json()) == 2
    assert client.get(f"/api/v1/entidades/{entity_ids[0]}").status_code == 200

    payload = {
        "origen_id": entity_ids[0],
        "destino_id": entity_ids[1],
        "tipo": "UTILIZA",
    }
    created = client.post("/api/v1/relaciones", json=payload)
    assert created.status_code == 201, created.text
    relation_id = created.json()["id"]
    assert len(client.get("/api/v1/relaciones").json()) == 1

    duplicate = client.post("/api/v1/relaciones", json=payload)
    assert duplicate.status_code == 409

    deleted = client.delete(f"/api/v1/relaciones/{relation_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/relaciones/{relation_id}").status_code == 404
    assert client.get("/api/v1/grafo").json()["edges"] == []


def test_write_confirmed_if_graph_reconstruction_fails(client, monkeypatch):
    graph_service = client.app.state.graph_service

    def fail_reconstruction(_session_factory):
        raise GraphReconstructionError("fallo simulado de reconstrucción")

    monkeypatch.setattr(graph_service, "_graph_loader", fail_reconstruction)
    created = client.post(
        "/api/v1/entidades",
        json={"tipo": "PERSONA", "valor": "Persistida", "valor_normalizado": "persistida"},
    )
    assert created.status_code == 500
    assert created.json()["detail"] == (
        "Ocurrió un error interno al acceder a los datos del proyecto."
    )

    persisted = client.get("/api/v1/entidades/1")
    assert persisted.status_code == 200
    assert persisted.json()["valor"] == "Persistida"

    unavailable_graph = client.post(
        "/api/v1/algoritmos/bfs", json={"id_inicial": persisted.json()["id"]}
    )
    assert unavailable_graph.status_code == 503
