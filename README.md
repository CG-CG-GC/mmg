# Mini-Maltego Académico

Aplicación web pequeña para registrar entidades y relaciones, visualizarlas como
un grafo dirigido y estudiar BFS, DFS y caminos mínimos por cantidad de aristas.
Es un ejercicio de Algoritmos y Estructuras de Datos 3 inspirado en el análisis
de relaciones; no es una herramienta OSINT completa ni recopila información
externa automáticamente.

## Alcance implementado

- Crear, listar, consultar y eliminar entidades y relaciones mediante la API.
- Crear evidencias asociadas a relaciones mediante la API; las evidencias se
  incluyen al consultar relaciones.
- Visualizar y seleccionar elementos, crear entidades y relaciones y ejecutar
  los tres algoritmos desde la interfaz web.
- Persistir en SQLite y reconstruir una proyección del grafo en memoria.

La interfaz no ofrece eliminación de entidades o relaciones ni creación de
evidencias; esas operaciones se realizan mediante la API. No hay edición de
entidades o relaciones ni eliminación de evidencias mediante la API. Las
limitaciones y mejoras posibles están en
[la guía del MVP](docs/mvp-academico.md#limitaciones-y-posibles-mejoras).

## Instalación y ejecución

Desde la raíz del proyecto, en Windows con PowerShell y Python instalado:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

La versión usada para esta verificación fue Python 3.13.3; el repositorio no
declara una versión mínima de Python. Si `py` no está disponible, usá el
ejecutable de Python instalado para crear el entorno. No hace falta activar el
entorno virtual. Detené el servidor con `Ctrl+C`.

- Interfaz: <http://127.0.0.1:8000/>
- Documentación interactiva de la API: <http://127.0.0.1:8000/docs>
- Esquema OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Estado del servidor: <http://127.0.0.1:8000/health>

La página interactiva `/docs` carga recursos de Swagger UI desde una CDN y
puede requerir conexión; el esquema `/openapi.json` se sirve desde la aplicación.

Por defecto se crea o reutiliza `data/mmg.sqlite3`, relativo al directorio
desde el que se inicia el proceso. Para no alterar datos existentes, antes de
iniciar el servidor elegí otra ruta:

```powershell
$env:MMG_DATABASE_PATH = "C:\ruta\demo.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Reemplazá la ruta por una ubicación válida y escribible. La variable queda
definida en esa sesión de PowerShell; `Remove-Item Env:MMG_DATABASE_PATH`
restaura el comportamiento por defecto para procesos posteriores. El esquema y
los catálogos se inicializan al crear la aplicación. La visualización usa una
copia local de Cytoscape.js; no requiere compilación del frontend.

## Pruebas

Desde la raíz y con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan bases temporales, no la base de trabajo. En la ejecución de
verificación del MVP se obtuvieron **61 aprobadas**; los resultados futuros
dependen del entorno y de los cambios posteriores. Las pruebas automatizadas
del frontend comprueban la entrega de archivos, no toda la interacción visual
en un navegador.

## Documentación

- [Arquitectura, modelo, algoritmos, pruebas y defensa](docs/mvp-academico.md).
- [Interfaz](docs/frontend.md).
- [Estado del proyecto](docs/estado-proyecto.md).
- Los documentos de arquitectura, dominio, diseño y contrato conservan
  propuestas y decisiones previas; sus indicaciones sobre implementación deben
  contrastarse con el código y la guía del MVP.
