"""Prueba opt-in del transporte real contra Google DoH.

No corre en la suite habitual ni en CI. Para ejecutarla:
    MMG_RUN_NETWORK_TESTS=1 python -m pytest tests/network -q
"""

import os

import pytest

from app.application.dns_lookup import DnsLookupService
from app.integrations.dns_google import FUENTE_GOOGLE_DOH, GoogleDohProvider

pytestmark = pytest.mark.skipif(
    os.environ.get("MMG_RUN_NETWORK_TESTS") != "1",
    reason="prueba de red opt-in: definir MMG_RUN_NETWORK_TESTS=1",
)


def test_consulta_real_a_google_doh():
    servicio = DnsLookupService(GoogleDohProvider(timeout=10))
    resultado = servicio.consultar("example.com", ["A", "NS"])
    estados = {e.tipo: e.estado for e in resultado.estados}
    assert estados == {"A": "ok", "NS": "ok"}
    assert all(r.fuente == FUENTE_GOOGLE_DOH for r in resultado.registros)
