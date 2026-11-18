"""Crea una base SQLite privada de demostración desde un perfil JSON externo.

Por defecto, tanto el perfil como la base se buscan en
%LOCALAPPDATA%\\MiniMaltego\\demo-personal. Ninguno puede ubicarse dentro del
repositorio y el script se niega a sobrescribir una base existente.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parents[1]
RUTA_LOCAL = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
DIRECTORIO_DEMO = RUTA_LOCAL / "MiniMaltego" / "demo-personal"
BASE_PRINCIPAL = RAIZ / "data" / "mmg.sqlite3"


def _esta_dentro_del_repo(ruta: Path) -> bool:
    try:
        ruta.relative_to(RAIZ)
        return True
    except ValueError:
        return False


def _texto(perfil: dict[str, object], clave: str) -> str:
    valor = perfil.get(clave)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El perfil requiere el campo de texto {clave!r}.")
    return valor.strip()


def _url_https(valor: str, clave: str, host_esperado: str | None = None) -> str:
    partes = urlsplit(valor)
    if (
        partes.scheme != "https"
        or partes.hostname is None
        or (host_esperado is not None and partes.hostname.lower() != host_esperado)
        or partes.username is not None
        or partes.password is not None
        or partes.query
        or partes.fragment
    ):
        destino = f" de {host_esperado}" if host_esperado else ""
        raise ValueError(f"El campo {clave!r} debe ser una URL HTTPS{destino}.")
    return valor


def _leer_perfil(ruta: Path) -> dict[str, str]:
    if _esta_dentro_del_repo(ruta):
        raise ValueError("El archivo de perfil debe estar fuera del repositorio.")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("No se pudo leer el perfil JSON indicado.") from exc
    if not isinstance(datos, dict):
        raise ValueError("El perfil JSON debe ser un objeto.")

    nombre = _texto(datos, "nombre")
    correo = _texto(datos, "correo")
    usuario = _texto(datos, "usuario_github")
    perfil_url = _url_https(
        _texto(datos, "perfil_github"),
        "perfil_github",
        "github.com",
    )
    sitio_url = _url_https(_texto(datos, "sitio_web"), "sitio_web")
    if correo.count("@") != 1 or any(caracter.isspace() for caracter in correo):
        raise ValueError("El campo 'correo' debe tener formato de dirección de email.")
    segmentos = [segmento for segmento in urlsplit(perfil_url).path.split("/") if segmento]
    if not segmentos or segmentos[0].casefold() != usuario.casefold():
        raise ValueError("La ruta del perfil de GitHub debe corresponder al usuario indicado.")

    return {
        "nombre": nombre,
        "correo": correo,
        "usuario_github": usuario,
        "perfil_github": perfil_url,
        "dominio_github": "github.com",
        "sitio_web": sitio_url,
        "dominio_sitio": urlsplit(sitio_url).hostname.lower(),
    }


def _crear_datos(app, perfil: dict[str, str]) -> tuple[int, int]:
    from app.domain.tipos import TipoEntidad, TipoRelacion
    from app.persistence.repositories import EntidadCreateData, RelacionCreateData

    servicio = app.state.graph_service
    entidades = (
        ("persona", TipoEntidad.PERSONA, perfil["nombre"], perfil["nombre"].casefold()),
        ("email", TipoEntidad.EMAIL, perfil["correo"], perfil["correo"].casefold()),
        (
            "usuario",
            TipoEntidad.USUARIO,
            perfil["usuario_github"],
            perfil["usuario_github"].casefold(),
        ),
        ("perfil", TipoEntidad.SITIO_WEB, perfil["perfil_github"], perfil["perfil_github"]),
        (
            "dominio_github",
            TipoEntidad.DOMINIO,
            perfil["dominio_github"],
            perfil["dominio_github"],
        ),
        ("sitio_web", TipoEntidad.SITIO_WEB, perfil["sitio_web"], perfil["sitio_web"]),
        (
            "dominio_sitio",
            TipoEntidad.DOMINIO,
            perfil["dominio_sitio"],
            perfil["dominio_sitio"],
        ),
    )
    ids: dict[str, int] = {}
    for clave, tipo, valor, normalizado in entidades:
        creada = servicio.crear_entidad(
            EntidadCreateData(
                tipo=tipo,
                valor=valor,
                valor_normalizado=normalizado,
            )
        )
        ids[clave] = creada.id

    relaciones = (
        ("persona", "email", TipoRelacion.POSEE),
        ("persona", "usuario", TipoRelacion.UTILIZA),
        ("usuario", "perfil", TipoRelacion.POSEE),
        ("perfil", "dominio_github", TipoRelacion.APUNTA_A),
        ("persona", "sitio_web", TipoRelacion.UTILIZA),
        ("sitio_web", "dominio_sitio", TipoRelacion.APUNTA_A),
    )
    for origen, destino, tipo in relaciones:
        servicio.crear_relacion(
            RelacionCreateData(
                origen_id=ids[origen],
                destino_id=ids[destino],
                tipo=tipo,
            )
        )
    return len(entidades), len(relaciones)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crea una base personal privada; no incluye datos en el repositorio."
    )
    parser.add_argument("--perfil", type=Path, default=DIRECTORIO_DEMO / "perfil.json")
    parser.add_argument("--ruta", type=Path, default=DIRECTORIO_DEMO / "grafo.sqlite3")
    args = parser.parse_args(argv)

    perfil_path = args.perfil.expanduser().resolve()
    ruta = args.ruta.expanduser().resolve()
    try:
        perfil = _leer_perfil(perfil_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if _esta_dentro_del_repo(ruta) or ruta == BASE_PRINCIPAL.resolve():
        print("Error: la base personal debe estar fuera del repositorio.", file=sys.stderr)
        return 1
    if any(Path(f"{ruta}{sufijo}").exists() for sufijo in ("", "-wal", "-shm", "-journal")):
        print("Error: la ruta de destino o un archivo SQLite auxiliar ya existe.", file=sys.stderr)
        return 1

    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ruta.open("xb"):
            pass
    except FileExistsError:
        print("Error: la base ya existe; no se sobrescribió.", file=sys.stderr)
        return 1

    app = None
    creada = False
    try:
        os.environ["MMG_DATABASE_PATH"] = str(ruta)
        if str(RAIZ) not in sys.path:
            sys.path.insert(0, str(RAIZ))
        from app.api.main import app as demo_app

        app = demo_app
        entidades, relaciones = _crear_datos(app, perfil)
        creada = True
    finally:
        if app is not None:
            app.state.engine.dispose()
        if not creada:
            ruta.unlink(missing_ok=True)
            for sufijo in ("-wal", "-shm", "-journal"):
                Path(f"{ruta}{sufijo}").unlink(missing_ok=True)

    print(f"Base personal creada fuera del repositorio: {ruta}")
    print(f"Entidades: {entidades} · Relaciones: {relaciones} · Evidencias: 0")
    print("Para iniciar la demo en esta sesión de PowerShell:")
    print(f'  $env:MMG_DATABASE_PATH = "{ruta}"')
    print(
        "  .\\.venv\\Scripts\\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000"
    )
    print("Abrí http://127.0.0.1:8000/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
