from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import create_app


def test_health_y_documentacion_openapi(tmp_path):
    client = TestClient(create_app(tmp_path / "health.sqlite3"))

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/openapi.json").status_code == 200


def test_crud_basico_grafo_y_algoritmos_con_sqlite_real(tmp_path):
    client = TestClient(create_app(tmp_path / "integration.sqlite3"))

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


def test_validaciones_y_recursos_inexistentes(tmp_path):
    client = TestClient(create_app(tmp_path / "errors.sqlite3"))

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


def test_eliminar_entidad_refresca_el_grafo_y_cascada_relacion(tmp_path):
    client = TestClient(create_app(tmp_path / "delete.sqlite3"))
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
