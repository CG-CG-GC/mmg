# Contexto del proyecto

## Qué es

Mini-Maltego Académico: aplicación web pequeña para modelar entidades y
relaciones como un grafo dirigido, guardarlas y explorarlas con algoritmos
propios. Es el proyecto final de Algoritmos y Estructuras de Datos 3. Su alcance
es académico: no pretende ser una herramienta OSINT profesional ni hacer
actividades intrusivas.

## Stack

- Backend: Python y FastAPI.
- Persistencia: SQLite con SQLAlchemy.
- Frontend: HTML, CSS y JavaScript sin bundler ni framework; Cytoscape.js
  incluido localmente en `app/frontend/vendor`.
- Pruebas: pytest. Calidad: Ruff, Bandit, pip-audit (ver
  [herramientas-calidad-seguridad.md](../herramientas-calidad-seguridad.md)).

## Arquitectura

Monolito modular con capas separadas:

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Dominio | `app/domain` | Entidades, relaciones, evidencias, grafo y algoritmos BFS, DFS y camino. No depende de infraestructura. |
| Aplicación | `app/application` | Servicios que orquestan casos de uso, incluida la consulta DNS. |
| Persistencia | `app/persistence` | Repositorios, mapeos y esquema SQLite. |
| API | `app/api` | Rutas FastAPI, esquemas de entrada y salida, errores HTTP. |
| Interfaz | `app/frontend` | HTML, CSS y JavaScript que consumen la API. |
| Integraciones | `app/integrations` | Cliente del servicio DNS externo. |

La interfaz no reimplementa reglas del dominio: consume la API. Cytoscape.js
solo visualiza; los algoritmos se ejecutan en el servidor.

## Alcance MVP

Crear, consultar, editar y eliminar entidades y relaciones; visualizar el
grafo; ejecutar BFS, DFS y camino más corto. Detalle y trazabilidad en
[mvp-academico.md](../mvp-academico.md). El estado real de las tareas está en
[BACKLOG.md](BACKLOG.md).

## Reglas de trabajo

- No cambiar contratos de API ni el esquema SQLite sin autorización expresa.
- No introducir dependencias innecesarias ni cambiar las principales sin aprobación.
- No hacer commit ni push sin autorización del usuario.
- No agregar `Co-authored-by` ni otros trailers de atribución.
- Preservar los cambios pendientes de otros agentes; no revertirlos ni
  reformatearlos.
- No borrar ni alterar la base local ni sus datos.
- No reemplazar los algoritmos propios por bibliotecas.
- Aplicar las reglas antislop referenciadas en `AGENTS.md` al tocar interfaz,
  textos o comentarios.
- Declarar solo lo que se verificó: no afirmar pruebas que no se ejecutaron.

## Ejecución rápida

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m pytest -q
```

`MMG_DATABASE_PATH` permite usar una base aislada para demostraciones y pruebas
manuales. Más detalle en [frontend.md](../frontend.md).

## Documentos con criterios distintos

Al preparar este sistema se detectaron diferencias con documentos anteriores.
No se modificaron esos documentos; quedan señaladas para decisión del usuario:

- [`protocolo-agentes.md`](../protocolo-agentes.md) (v1.0) establece que los
  agentes proponen y el usuario integra, sin modificar archivos locales. En la
  práctica reciente los agentes editaron el workspace con autorización del
  usuario en cada tarea. Hasta que se decida, rige lo que indique la tarea
  concreta y, ante duda, preguntar.
- [`estado-proyecto.md`](../estado-proyecto.md) numera a los agentes de otra
  forma (05 = API, 06 = Frontend, 07 = QA). Este directorio usa la asignación
  vigente: 03 backend, 04 persistencia, 05 frontend, 06 QA, 07 documentación.
  Ese documento es histórico, según su propia nota de cierre del MVP.
