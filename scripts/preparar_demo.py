"""Crea una base SQLite nueva con datos ficticios para la demostración.

Uso desde la raíz del proyecto (PowerShell):

    .\\.venv\\Scripts\\python.exe scripts\\preparar_demo.py
    .\\.venv\\Scripts\\python.exe scripts\\preparar_demo.py --ruta "$env:TEMP\\mmg-demo-clase.sqlite3"

El script nunca sobrescribe ni reutiliza un archivo existente y nunca usa
data/mmg.sqlite3. Por eso cada ejecución produce un conjunto de datos sin
duplicados. Solo usa la capa de aplicación ya existente; no cambia el código de producción.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE_PRINCIPAL = RAIZ / "data" / "mmg.sqlite3"

# (tipo, valor, valor_normalizado, descripcion)
ENTIDADES = (
    ("PERSONA", "Ana Demo", "ana-demo", "Persona ficticia de la demostración."),
    ("PERSONA", "Bruno Demo", "bruno-demo", "Persona ficticia de la demostración."),
    ("ORGANIZACION", "Laboratorio Ejemplo", "laboratorio-ejemplo", "Organización ficticia."),
    ("ORGANIZACION", "Universidad Demo", "universidad-demo", "Organización ficticia."),
    ("EMAIL", "ana.demo@example.org", "ana.demo@example.org", "Correo ficticio."),
    ("USUARIO", "ana.demo", "ana.demo", "Usuario ficticio."),
    ("SITIO_WEB", "https://portal.example.org", "https://portal.example.org", "Sitio ficticio."),
    ("DOMINIO", "example.com", "example.com", "Dominio reservado para documentación (RFC 2606)."),
    ("IP", "192.0.2.10", "192.0.2.10", "Dirección reservada para documentación (RFC 5737)."),
)

# (clave de origen, clave de destino, tipo, descripcion, fecha)
RELACIONES = (
    (
        "ana-demo",
        "laboratorio-ejemplo",
        "TRABAJA_EN",
        "Ana trabaja en el laboratorio ficticio.",
        date(2026, 3, 1),
    ),
    ("ana-demo", "ana.demo@example.org", "POSEE", None, None),
    ("ana-demo", "ana.demo", "UTILIZA", None, None),
    ("bruno-demo", "laboratorio-ejemplo", "PERTENECE_A", None, None),
    ("bruno-demo", "https://portal.example.org", "ADMINISTRA", None, None),
    ("laboratorio-ejemplo", "universidad-demo", "PERTENECE_A", None, None),
    ("laboratorio-ejemplo", "https://portal.example.org", "POSEE", None, None),
    (
        "https://portal.example.org",
        "example.com",
        "APUNTA_A",
        "Portal ficticio que apunta al dominio de ejemplo.",
        None,
    ),
    (
        "example.com",
        "192.0.2.10",
        "APUNTA_A",
        "Registro cargado a mano para la demostración.",
        None,
    ),
)

# (clave de relación, origen, destino, fuente, descripcion)
EVIDENCIAS = (
    (
        "ana-demo>laboratorio-ejemplo",
        "Ficha ficticia de la demostración",
        "Dato para practicar la lectura de evidencias.",
    ),
    (
        "https://portal.example.org>example.com",
        "Documentación académica ficticia",
        "Evidencia de ejemplo sin fuente real.",
    ),
)


def _crear_base_demo(ruta: Path):
    """Importa la aplicación solo después de fijar la ruta, para no tocar la base por defecto."""
    os.environ["MMG_DATABASE_PATH"] = str(ruta)
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from app.api.main import app

    return app


def _sembrar(app) -> dict[str, int]:
    from app.domain.tipos import TipoEntidad, TipoRelacion
    from app.persistence.repositories import (
        EntidadCreateData,
        EvidenciaCreateData,
        RelacionCreateData,
    )

    servicio = app.state.graph_service
    ids: dict[str, int] = {}
    for tipo, valor, normalizado, descripcion in ENTIDADES:
        creada = servicio.crear_entidad(
            EntidadCreateData(
                tipo=TipoEntidad(tipo),
                valor=valor,
                valor_normalizado=normalizado,
                descripcion=descripcion,
            )
        )
        ids[normalizado] = creada.id

    relaciones: dict[str, int] = {}
    for origen, destino, tipo, descripcion, fecha in RELACIONES:
        creada = servicio.crear_relacion(
            RelacionCreateData(
                origen_id=ids[origen],
                destino_id=ids[destino],
                tipo=TipoRelacion(tipo),
                descripcion=descripcion,
                fecha=fecha,
            )
        )
        relaciones[f"{origen}>{destino}"] = creada.id

    for clave, fuente, descripcion in EVIDENCIAS:
        servicio.crear_evidencia(
            EvidenciaCreateData(
                relacion_id=relaciones[clave],
                fuente=fuente,
                descripcion=descripcion,
                fecha=date(2026, 3, 1),
            )
        )
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara una base SQLite de demostración.")
    parser.add_argument(
        "--ruta",
        type=Path,
        help="Archivo nuevo que se va a crear. Por defecto, un archivo temporal único.",
    )
    args = parser.parse_args(argv)

    ruta = args.ruta or Path(tempfile.gettempdir()) / f"mmg-demo-{uuid.uuid4().hex[:8]}.sqlite3"
    ruta = ruta.resolve()

    if ruta == BASE_PRINCIPAL.resolve():
        print("Error: esa ruta corresponde a la base principal. Elegí otra.", file=sys.stderr)
        return 1
    if ruta.exists():
        print(
            f"Error: ya existe {ruta}. Elegí una ruta nueva para no duplicar datos.",
            file=sys.stderr,
        )
        return 1

    ruta.parent.mkdir(parents=True, exist_ok=True)
    app = _crear_base_demo(ruta)
    try:
        ids = _sembrar(app)
    except Exception:
        app.state.engine.dispose()
        ruta.unlink(missing_ok=True)
        raise
    app.state.engine.dispose()

    print(f"Base de demostración creada: {ruta}")
    print(f"Entidades: {len(ids)} · Relaciones: {len(RELACIONES)} · Evidencias: {len(EVIDENCIAS)}")
    print("Para iniciar la aplicación con esta base (PowerShell, desde la raíz):")
    print(f'  $env:MMG_DATABASE_PATH = "{ruta}"')
    print(
        "  .\\.venv\\Scripts\\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
