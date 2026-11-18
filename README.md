# Mini-Maltego Académico

Aplicación web pequeña para registrar entidades y relaciones, visualizarlas como
un grafo dirigido y estudiar BFS, DFS y caminos mínimos por cantidad de aristas.
Es un ejercicio de Algoritmos y Estructuras de Datos 3 inspirado en el análisis
de relaciones; no es una herramienta OSINT completa ni recopila información
externa automáticamente.

## Alcance implementado

- API: crear, listar, consultar, editar (`PUT`) y eliminar (`DELETE`) entidades
  y relaciones; crear evidencias asociadas a relaciones; las evidencias se
  incluyen al consultar una relación.
- Interfaz web: visualizar el grafo dirigido, seleccionar elementos, crear y
  editar entidades y relaciones, cambiar la distribución y ejecutar BFS, DFS y
  camino más corto.
- Consulta DNS pública (A, AAAA, CNAME, MX y NS) como vista previa que no guarda
  nada, y la incorporación de registros A y AAAA revisados y confirmados por el
  usuario. Solo esos dos tipos se incorporan.
- Persistencia en SQLite y reconstrucción de una proyección del grafo en memoria.

La interfaz no elimina entidades ni relaciones, no crea evidencias y no tiene
buscador por texto; esas operaciones están en la API. Las limitaciones están
en [la sección 27 del manual](docs/manual-usuario.md#27-limitaciones-conocidas)
y en [la guía del MVP](docs/mvp-academico.md#limitaciones-y-posibles-mejoras).

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
entorno virtual: los comandos usan la ruta completa `.\.venv\Scripts\python.exe`.
Si querés activarlo y PowerShell bloquea `Activate.ps1`, ejecutá
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` en esa misma
ventana. Detené el servidor con `Ctrl+C`.

- Interfaz: <http://127.0.0.1:8000/>
- Documentación interactiva de la API: <http://127.0.0.1:8000/docs>
- Esquema OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Estado del servidor: <http://127.0.0.1:8000/health>

No hace falta Live Server ni otro servidor: FastAPI entrega la interfaz y la API
desde el mismo puerto. La página `/docs` carga recursos de Swagger UI desde una CDN y
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

Desde la raíz y con las dependencias de desarrollo instaladas
(`requirements-dev.txt`; `requirements.txt` contiene solo lo necesario para ejecutar la aplicación):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas usan bases temporales, no la base de trabajo. En la verificación del
18 de noviembre de 2026 se obtuvo **368 aprobadas y 1 omitida** (la omitida es la
prueba de red opt-in). Los resultados futuros dependen del entorno y de los
cambios posteriores. Las pruebas automatizadas del frontend comprueban la entrega
de archivos y algunos comportamientos, no toda la interacción visual en un navegador.

## Calidad y seguridad

Ruff, Bandit, pip-audit y el flujo de GitHub Actions están descritos en
[la guía de herramientas de calidad](docs/herramientas-calidad-seguridad.md).

## Demostración académica

Para practicar o exponer sin tocar tus datos, creá una base nueva con datos
ficticios y arrancá el servidor con ella:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_demo.py
```

El script imprime la ruta de la base creada y el comando para iniciar el servidor.
Cada ejecución crea un archivo nuevo, nunca reutiliza uno existente y nunca usa
`data/mmg.sqlite3`. La respuesta DNS de las capturas es simulada; ver
[la guía de demostración](docs/demo-presentacion.md).

Para una demostración personal, `scripts/preparar_demo_personal.py` lee un
`perfil.json` local con los campos `nombre`, `correo`, `usuario_github`,
`perfil_github` y `sitio_web`. El perfil y la base SQLite se guardan por
defecto fuera del repositorio, en `%LOCALAPPDATA%\MiniMaltego\demo-personal`;
el script no sobrescribe una base existente y rechaza rutas dentro del proyecto.
No se versionan el archivo de perfil, la base ni capturas con datos personales.
La consulta DNS requiere red salvo que se intercepte en el navegador para una
simulación identificada como tal; la incorporación resultante se guarda en la
base local mediante la API real.

## Documentación

- [Manual de usuario](docs/manual-usuario.md): instalación en Windows con VS Code,
  uso de cada sección, capturas y errores frecuentes.
- [Arquitectura, modelo, algoritmos, pruebas y defensa](docs/mvp-academico.md).
- [Interfaz](docs/frontend.md).
- [Herramientas de calidad y seguridad](docs/herramientas-calidad-seguridad.md).
- [Estado del proyecto](docs/estado-proyecto.md).
