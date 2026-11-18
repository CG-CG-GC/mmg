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
`/api/v1/relaciones`; crea entidades y relaciones con los POST correspondientes,
las edita con `PUT` desde el inspector y ejecuta `/api/v1/algoritmos/bfs`,
`/api/v1/algoritmos/dfs` y `/api/v1/algoritmos/camino`. Antes de cada escritura
pide confirmación con el mensaje "Esta acción guardará datos en el proyecto. ¿Continuar?".
No ofrece eliminación ni creación de evidencias, y no tiene buscador por texto.
El valor normalizado se ingresa explícitamente: la API todavía no define una
política de normalización. Un fallo de escritura puede producirse después de
persistir los datos; antes de reintentar, actualizar la vista.

Las llamadas usan rutas relativas (`/api/v1/...`): la interfaz solo funciona
cuando se abre desde el servidor de FastAPI, no con Live Server ni otro puerto.
El procedimiento para usuarios está en [manual-usuario.md](manual-usuario.md).

La lectura de diseño es una herramienta académica de análisis, con un ritmo
moderado y movimiento mínimo: ENERGY 1, RHYTHM 2, MOTION 1. La edición aparece
dentro del inspector para mantener el grafo y la entidad seleccionada a la
vista, sin interrumpir el análisis con un diálogo modal.

Cytoscape.js 3.30.4 está incluido localmente en `app/frontend/vendor`, junto
con su licencia MIT, para permitir el uso sin conexión. Solo se usa para la
visualización: los algoritmos se ejecutan en el dominio del servidor. BFS y DFS
resaltan los nodos visitados; solo el camino resalta aristas, porque su respuesta
identifica las relaciones concretas. La lista de elementos permite consultar
el grafo también con teclado.

El selector **Distribución** reutiliza los layouts incluidos en Cytoscape.js
(fuerzas, jerárquica, concéntrica, círculo y cuadrícula). Solo cambia la posición
de los nodos: no escribe datos ni altera la selección. La última opción se
guarda en `localStorage` (clave `mmg.layout`); si el navegador no la permite o
el valor guardado no es válido, se usa Fuerzas. Los indicadores de entidades y
relaciones por tipo se calculan en el cliente con las mismas listas que ya
consulta la interfaz y se recalculan en cada actualización. Con grafos muy
grandes, la distribución jerárquica o en círculo puede requerir acercar la vista
para leer las etiquetas.

## OSINT DNS (vista previa)

La sección **06 / OSINT DNS** (`osint.js`, `osint.css`) consulta
`POST /api/v1/osint/dns` y muestra una vista previa agrupada por tipo (A, AAAA,
CNAME, MX, NS) con estado, fuente, fecha de consulta y registros descartados.
El navegador nunca llama a Google DNS. La consulta no crea entidades, relaciones
ni evidencias: solo la incorporación explícita, descrita abajo, escribe en el
grafo.

- Toda la respuesta se trata como no confiable: se valida su forma y se escribe
  solo con `textContent`.
- Los duplicados se detectan contra las entidades cargadas (A y AAAA con IP;
  CNAME, MX, NS y el dominio con Dominio), sin distinguir mayúsculas ni punto
  final. Es una heurística: la política de normalización sigue sin definirse.
- La vista previa, los registros marcados como revisados, los seleccionados para
  incorporar y los ya incorporados se guardan en `sessionStorage` (clave
  `mmg.osint.preview`), por pestaña. Una consulta nueva descarta la selección.
- Las consultas son secuenciales en el backend; el peor caso ronda los 25 s y el
  cliente corta a los 40 s.
- Un dominio con `ß`, separadores ideográficos, ligaduras u otras
  transformaciones IDNA 2003 que cambiarían el nombre, o con una etiqueta `xn--`
  malformada, se rechaza con 422 antes de consultar la red o escribir en la base.
  El mensaje indica usar la forma `xn--`. Una `xn--` válida se consulta tal cual, en
  minúsculas, y no es soporte de IDNA 2008. Ver D-20 y P-06.

### Incorporación al grafo (A y AAAA)

- **Revisado** y **Incorporar al grafo** son controles distintos. Solo A y AAAA
  tienen el segundo; CNAME, MX y NS se muestran con una nota de que no son
  incorporables todavía. "Incorporar al grafo" se habilita únicamente si el
  registro está revisado; al quitar "Revisado" se quita también la selección.
- **Revisar incorporación** abre un panel en línea con el dominio de origen, la
  cantidad de registros, cada IP con su tipo, la aclaración de que se crearán o
  reutilizarán entidades y relaciones, y la procedencia declarada por el cliente.
  Nada se envía hasta **Confirmar incorporación**. El foco va al título del panel;
  **Cancelar** o Escape cierran el panel y devuelven el foco a
  "Revisar incorporación".
- El lote se arma con `dominio` y, por registro, `tipo`, `valor`, `fuente` y
  `consultado_en` tal como llegaron de la consulta. No se envían CNAME, MX ni NS,
  no se envía un lote vacío y la interfaz no normaliza nada: la canonicalización
  queda en el backend.
- Durante el envío se bloquean la consulta, la selección y "Limpiar vista previa",
  y el botón cambia a "Incorporando…": no hay envíos duplicados.
- **Éxito:** el resultado muestra cuántos elementos se crearon y cuántos se
  reutilizaron (dominio, entidades IP, relaciones APUNTA_A y evidencias), y la
  procedencia como declarada por el cliente. Luego se llama a la misma
  actualización que usa el botón **Actualizar**: el grafo se redibuja con los datos
  persistidos, conserva la distribución elegida y la selección del inspector.
  Los registros incorporados quedan marcados como "Incorporado".
- **Errores:**
  - 422: el lote fue rechazado; no se incorporó nada y la selección se conserva.
  - 409: existe un conflicto o una ambigüedad con entidades del grafo; el lote no se
    incorporó.
  - 503 por bloqueo de SQLite: el lote no se incorporó; se puede reintentar.
  - 503 con `persistencia: confirmada`: los datos se guardaron, pero el grafo no se
    pudo reconstruir. La interfaz no habla de cancelación, no pide reincorporar y
    ofrece **Actualizar grafo**.
  - Red, timeout (30 s) o respuesta malformada, y cualquier otro código: el
    resultado es incierto. La interfaz no afirma que el lote se guardó ni que se
    revirtió. Ofrece **Actualizar grafo**, y no permite otro envío hasta que el
    grafo se actualice. Después, los registros que ya estén en el grafo aparecen
    como posible duplicado.
- Un fallo de actualización del grafo tras un éxito deja el mismo estado de
  recuperación: los datos ya están guardados.
