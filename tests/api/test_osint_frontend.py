from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import create_app

FRONTEND = Path(__file__).resolve().parents[2] / "app" / "frontend"


def test_pagina_incluye_seccion_osint_dns_y_sus_recursos(tmp_path):
    with TestClient(create_app(tmp_path / "osint-frontend.sqlite3")) as client:
        page = client.get("/")
        for fragment in (
            'id="osint-form"',
            'id="osint-domain"',
            'id="osint-preview"',
            "/static/osint.js",
            "/static/osint.css",
        ):
            assert fragment in page.text
        for tipo in ("A", "AAAA", "CNAME", "MX", "NS"):
            assert f'id="osint-type-{tipo}"' in page.text
        assert client.get("/static/osint.js").status_code == 200
        assert client.get("/static/osint.css").status_code == 200


def test_frontend_osint_solo_usa_el_endpoint_del_backend():
    script = (FRONTEND / "osint.js").read_text(encoding="utf-8")
    assert "/osint/dns" in script
    assert "dns.google" not in script
    assert "innerHTML" not in script
    assert "outerHTML" not in script
    assert "insertAdjacentHTML" not in script
    # Solo consulta: no debe llamar a los endpoints de escritura del grafo.
    assert "/entidades" not in script
    assert "/relaciones" not in script
    assert "/evidencias" not in script
