import json
import shutil
import subprocess  # nosec B404 - solo ejecuta Node con un script fijo del repositorio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import app, create_app


def test_app_global_usa_una_base_temporal_durante_pytest():
    database_path = Path(app.state.engine.url.database)
    assert database_path.name == "app-import.sqlite3"
    assert any("mini-maltego-pytest-" in part for part in database_path.parts)


def test_frontend_y_recursos_estaticos(tmp_path):
    with TestClient(create_app(tmp_path / "frontend.sqlite3")) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "Mini-Maltego académico" in page.text
        assert 'id="graph"' in page.text
        assert 'id="layout"' in page.text
        assert 'id="entity-stats"' in page.text
        assert 'id="relation-stats"' in page.text
        assert client.get("/static/styles.css").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        library = client.get("/static/vendor/cytoscape.min.js")
        assert library.status_code == 200
        assert "cytoscape" in library.text.lower()
        assert client.get("/static/vendor/CYTOSCAPE-LICENSE.txt").status_code == 200
        assert client.get("/api/v1/grafo").json() == {"nodes": [], "edges": []}


def test_actualizar_conserva_seleccion_existente_y_limpia_la_inexistente():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js no está disponible")
    harness = Path(__file__).with_name("frontend_refresh_harness.js")
    # Node resuelto con shutil.which; argumentos fijos, sin shell ni entrada externa.
    completed = subprocess.run(  # nosec B603
        [node, str(harness)], capture_output=True, text=True, timeout=30, check=True
    )
    assert json.loads(completed.stdout) == {
        "entity": '{"kind":"entity","id":1}',
        "relation": '{"kind":"relation","id":7}',
        "missingRelation": "null",
        "missingEntity": "null",
    }


def test_respuesta_entidad_incluye_valor_normalizado_para_editar(tmp_path):
    with TestClient(create_app(tmp_path / "entity-response.sqlite3")) as client:
        created = client.post(
            "/api/v1/entidades",
            json={
                "tipo": "PERSONA",
                "valor": "Ana",
                "valor_normalizado": "ana distinta",
            },
        )
        assert created.status_code == 201
        entity_id = created.json()["id"]
        assert created.json()["valor_normalizado"] == "ana distinta"
        assert client.get("/api/v1/entidades").json()[0]["valor_normalizado"] == "ana distinta"
        assert client.get(f"/api/v1/entidades/{entity_id}").json()["valor_normalizado"] == (
            "ana distinta"
        )
        updated = client.put(
            f"/api/v1/entidades/{entity_id}",
            json={
                "tipo": "PERSONA",
                "valor": "Ana editada",
                "valor_normalizado": "normalizacion conservada",
            },
        )
        assert updated.status_code == 200
        assert updated.json()["valor_normalizado"] == "normalizacion conservada"
