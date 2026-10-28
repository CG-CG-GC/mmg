# Interfaz de Mini-Maltego

La interfaz se sirve desde la misma aplicación FastAPI que la API, sin servidor
de desarrollo adicional ni compilación. Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/`. Las dependencias Python del proyecto se
instalan desde `requirements.txt`. Por defecto se utiliza `data/mmg.sqlite3`;
para ejecutar una demostración aislada se puede definir `MMG_DATABASE_PATH`
antes de iniciar el servidor:

```powershell
$env:MMG_DATABASE_PATH = "C:\ruta\demo.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

La interfaz consulta `/api/v1/grafo`, `/api/v1/entidades` y
`/api/v1/relaciones`; crea entidades y relaciones con los POST correspondientes
y ejecuta `/api/v1/algoritmos/bfs`, `/api/v1/algoritmos/dfs` y
`/api/v1/algoritmos/camino`. El valor normalizado se ingresa explícitamente:
la API todavía no define una política de normalización. Un fallo de escritura
puede producirse después de persistir los datos; antes de reintentar, actualizar
la vista.

Cytoscape.js 3.30.4 está incluido localmente en `app/frontend/vendor`, junto
con su licencia MIT, para permitir el uso sin conexión. Solo se usa para la
visualización: los algoritmos se ejecutan en el dominio del servidor. BFS y DFS
resaltan los nodos visitados; solo el camino resalta aristas, porque su respuesta
identifica las relaciones concretas. La lista de elementos permite consultar
el grafo también con teclado.
