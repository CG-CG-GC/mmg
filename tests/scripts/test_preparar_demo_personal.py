import json
import sqlite3
import subprocess
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "scripts" / "preparar_demo_personal.py"


def _ejecutar(perfil: Path, base: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--perfil",
            str(perfil),
            "--ruta",
            str(base),
        ],
        cwd=RAIZ,
        capture_output=True,
        check=False,
        text=True,
    )


def test_prepara_el_grafo_con_datos_externos_y_rechaza_repetir(tmp_path: Path) -> None:
    perfil = tmp_path / "perfil.json"
    perfil.write_text(
        json.dumps(
            {
                "nombre": "Mara Prueba",
                "correo": "mara@example.net",
                "usuario_github": "mara-prueba",
                "perfil_github": "https://github.com/mara-prueba",
                "sitio_web": "https://sitio.example/",
            }
        ),
        encoding="utf-8",
    )
    base = tmp_path / "demo.sqlite3"

    primera = _ejecutar(perfil, base)

    assert primera.returncode == 0, primera.stderr
    assert "Entidades: 7" in primera.stdout
    assert "Relaciones: 6" in primera.stdout
    assert "Evidencias: 0" in primera.stdout

    with sqlite3.connect(base) as connection:
        entidades = connection.execute(
            """
            SELECT tipo_entidad.codigo, entidad.valor
            FROM entidad
            JOIN tipo_entidad ON tipo_entidad.id = entidad.tipo_entidad_id
            ORDER BY entidad.id
            """
        ).fetchall()
        relaciones = connection.execute(
            """
            SELECT origen.valor, tipo_relacion.codigo, destino.valor
            FROM relacion
            JOIN entidad AS origen ON origen.id = relacion.origen_id
            JOIN entidad AS destino ON destino.id = relacion.destino_id
            JOIN tipo_relacion ON tipo_relacion.id = relacion.tipo_relacion_id
            ORDER BY relacion.id
            """
        ).fetchall()
        evidencia_count = connection.execute("SELECT COUNT(*) FROM evidencia").fetchone()[0]

    assert [tipo for tipo, _ in entidades] == [
        "PERSONA",
        "EMAIL",
        "USUARIO",
        "SITIO_WEB",
        "DOMINIO",
        "SITIO_WEB",
        "DOMINIO",
    ]
    assert relaciones == [
        ("Mara Prueba", "POSEE", "mara@example.net"),
        ("Mara Prueba", "UTILIZA", "mara-prueba"),
        ("mara-prueba", "POSEE", "https://github.com/mara-prueba"),
        ("https://github.com/mara-prueba", "APUNTA_A", "github.com"),
        ("Mara Prueba", "UTILIZA", "https://sitio.example/"),
        ("https://sitio.example/", "APUNTA_A", "sitio.example"),
    ]
    assert evidencia_count == 0

    antes = base.read_bytes()
    segunda = _ejecutar(perfil, base)

    assert segunda.returncode == 1
    assert "ya existe" in segunda.stderr
    assert base.read_bytes() == antes


def test_rechaza_crear_la_base_dentro_del_repositorio(tmp_path: Path) -> None:
    perfil = tmp_path / "perfil.json"
    perfil.write_text(
        json.dumps(
            {
                "nombre": "Mara Prueba",
                "correo": "mara@example.net",
                "usuario_github": "mara-prueba",
                "perfil_github": "https://github.com/mara-prueba",
                "sitio_web": "https://sitio.example/",
            }
        ),
        encoding="utf-8",
    )
    base = RAIZ / "data" / f"demo-personal-test-{tmp_path.name}.sqlite3"

    resultado = _ejecutar(perfil, base)

    assert resultado.returncode == 1
    assert "fuera del repositorio" in resultado.stderr
    assert not base.exists()
