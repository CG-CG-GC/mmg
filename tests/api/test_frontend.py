from pathlib import Path

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
        assert client.get("/static/styles.css").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        library = client.get("/static/vendor/cytoscape.min.js")
        assert library.status_code == 200
        assert "cytoscape" in library.text.lower()
        assert client.get("/static/vendor/CYTOSCAPE-LICENSE.txt").status_code == 200
        assert client.get("/api/v1/grafo").json() == {"nodes": [], "edges": []}
