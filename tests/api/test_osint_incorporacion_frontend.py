import json
import shutil
import subprocess  # nosec B404 - solo ejecuta Node con un script fijo del repositorio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app

FRONTEND = Path(__file__).resolve().parents[2] / "app" / "frontend"
HARNESS = Path(__file__).with_name("osint_incorporacion_harness.js")
KEY_A1 = "A|192.0.2.1|"


def test_pagina_incluye_la_incorporacion_y_sus_recursos(tmp_path):
    with TestClient(create_app(tmp_path / "incorporacion-frontend.sqlite3")) as client:
        page = client.get("/")
        for fragment in (
            'id="osint-incorporate-open"',
            'id="osint-incorporate-refresh"',
            'id="osint-incorporate-count"',
            'id="osint-confirm"',
            'id="osint-incorporate-message"',
            'id="osint-incorporate-result"',
            "/static/osint-incorporacion.js",
        ):
            assert fragment in page.text
        assert client.get("/static/osint-incorporacion.js").status_code == 200


def test_incorporacion_no_usa_html_dinamico_ni_endpoints_de_escritura_del_grafo():
    for name in ("osint.js", "osint-incorporacion.js"):
        script = (FRONTEND / name).read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            assert forbidden not in script, f"{name} usa {forbidden}"
    script = (FRONTEND / "osint.js").read_text(encoding="utf-8")
    assert "/osint/dns/incorporaciones" in script
    assert "/entidades" not in script
    assert "/relaciones" not in script


def test_incorporacion_frontend_cumple_los_escenarios():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js no está disponible")
    # Node resuelto con shutil.which; argumentos fijos, sin shell ni entrada externa.
    completed = subprocess.run(  # nosec B603
        [node, str(HARNESS)], capture_output=True, text=True, encoding="utf-8", timeout=60, check=True
    )
    results = json.loads(completed.stdout)

    pure = results["pure"]
    assert pure["respuestaVacia"] is False
    assert pure["respuestaCorrecta"] is True
    assert pure["clasificacionConfirmada"] == "guardado_sin_grafo"
    assert pure["clasificacionOcupada"] == "ocupada"
    assert pure["clasificacionConflicto"] == "conflicto"
    assert pure["clasificacionValidacion"] == "validacion"
    assert pure["clasificacionHttp500"] == "incierto"
    assert pure["clasificacionSinRespuesta"] == "incierto"
    assert "Elegí al menos" in pure["motivoVacio"]

    success = results["success"]
    # 1. Visualización: solo A y AAAA tienen control; CNAME, MX y NS se muestran como no incorporables.
    assert success["cnameHasControl"] is False
    assert len(success["notes"]) == 3
    # 2 y 4. Revisión, selección y lote HTTP sin CNAME, MX ni NS.
    assert success["unreviewedDisabled"] is True
    assert success["afterUnreview"] == "Seleccionados para incorporar: 2 registros (A: 2, AAAA: 0)."
    assert [record["tipo"] for record in success["body"]["registros"]] == ["A", "A", "AAAA"]
    assert success["body"]["dominio"] == "example.com"
    assert success["body"]["registros"][0] == {
        "tipo": "A",
        "valor": "192.0.2.1",
        "fuente": "google-public-dns-doh",
        "consultado_en": "2026-11-16T12:00:00Z",
    }
    # 5. Confirmación previa al envío.
    assert "Se incorporarán 3 registros: 2 A y 1 AAAA." in success["confirmText"]
    assert "Procedencia declarada por el cliente" in success["confirmText"]
    assert success["confirmFocus"] == "osint-confirm-title"
    assert success["requestsBeforeConfirm"] == 1
    # 6. Doble clic: una sola solicitud.
    assert success["after"]["requests"] == 1
    # 7 y 8. Creados frente a reutilizados.
    assert "Creadas: 2 · Reutilizadas: 1" in success["after"]["result"]
    assert "Creadas: 3 · Reutilizadas: 0" in success["after"]["result"]
    assert "entidad reutilizada, relación reutilizada" in success["after"]["result"]
    assert "El servidor no verificó esta consulta." in success["after"]["result"]
    assert success["after"]["messageSuccess"] is True
    assert success["after"]["focused"] == "osint-result-title"
    assert success["after"]["badges"] == 3
    assert success["after"]["selectedChecked"] == 0
    assert success["after"]["openDisabled"] is True
    assert success["after"]["confirmOpen"] is False
    # 14, 15 y 16. Grafo actualizado sin duplicados, layout y selección conservados.
    assert len(success["graph"]["nodeIds"]) == success["graph"]["serverEntities"] == 4
    assert len(success["graph"]["edgeIds"]) == success["graph"]["serverRelations"] == 3
    assert "n1" in success["graph"]["nodeIds"] and "n5" in success["graph"]["nodeIds"]
    assert success["layoutSelected"] == "circle"
    assert success["lastLayoutCall"] == "circle"
    assert success["selectionBefore"] == success["selectionAfter"] == '{"kind":"entity","id":1}'

    cancel = results["confirmControls"]["cancel"]
    # 5. Cancelar no envía y devuelve el foco al botón de revisión.
    assert cancel["confirmOpen"] is False
    assert cancel["requests"] == 0
    assert cancel["focused"] == "osint-incorporate-open"
    assert cancel["selectedChecked"] == 1
    escape = results["confirmControls"]["escape"]
    assert escape["confirmOpen"] is False
    assert escape["requests"] == 0
    assert escape["focused"] == "osint-incorporate-open"

    errors = results["errors"]
    # 9. HTTP 422: error de validación y selección conservada.
    assert errors["validacion"]["messageError"] is True
    assert "El servidor rechazó el lote" in errors["validacion"]["message"]
    assert "No se incorporó nada" in errors["validacion"]["message"]
    assert errors["validacion"]["selectedChecked"] == 2
    assert errors["validacion"]["openDisabled"] is False
    assert errors["validacion"]["refreshVisible"] is False
    # 10. HTTP 409: conflicto, lote no incorporado.
    assert "Existe un conflicto o una ambigüedad" in errors["conflicto"]["message"]
    assert "El lote no se incorporó" in errors["conflicto"]["message"]
    assert errors["conflicto"]["selectedChecked"] == 2
    # 11. HTTP 503 por bloqueo: reintento permitido de forma controlada.
    assert "ocupada" in errors["ocupada"]["message"]
    assert "no se incorporó" in errors["ocupada"]["message"]
    assert errors["ocupada"]["selectedChecked"] == 2
    assert errors["ocupada"]["openDisabled"] is False
    assert errors["ocupada"]["refreshVisible"] is False
    # 13. Red, timeout y respuestas malformadas: resultado incierto, sin afirmar guardado ni revertido.
    for label in ("red", "tiempo", "formato", "forma", "http500"):
        outcome = errors[label]
        assert "No se puede confirmar si el lote se guardó" in outcome["message"], label
        assert "Usá Actualizar grafo" in outcome["message"], label
        assert outcome["refreshVisible"] is True, label
        assert outcome["openDisabled"] is True, label
        assert outcome["badges"] == 0, label
        assert outcome["selectedChecked"] == 2, label
        assert outcome["focused"] == "osint-incorporate-refresh", label
    assert "La respuesta tardó demasiado." in errors["tiempo"]["message"]

    sent = results["recovery"]["sentState"]
    # 12. HTTP 503 con persistencia confirmada: datos guardados, sin hablar de deshacer ni de reintentar.
    assert sent["messageError"] is True
    assert "se guardaron" in sent["message"]
    assert "Actualizar grafo" in sent["message"]
    assert "no hace falta volver a incorporar" in sent["message"]
    assert "No se incorporó" not in sent["message"]
    assert "Reintent" not in sent["message"]
    assert sent["refreshVisible"] is True
    assert sent["openDisabled"] is True
    assert sent["badges"] == 2
    assert sent["focused"] == "osint-incorporate-refresh"
    # Recuperación: primero falla y sigue pendiente; después actualiza y libera el control.
    assert "No se pudo actualizar el grafo" in results["recovery"]["failed"]["message"]
    assert results["recovery"]["failed"]["refreshVisible"] is True
    recovered = results["recovery"]["recovered"]
    assert recovered["messageSuccess"] is True
    assert recovered["refreshVisible"] is False

    session = results["session"]
    # Persistencia de sesión: la selección se restaura y una consulta nueva la descarta.
    assert session["restored"]["selectedChecked"] == 2
    assert session["newQuery"]["selectedChecked"] == 0
    assert session["newQuery"]["count"] == "No hay registros seleccionados para incorporar."
