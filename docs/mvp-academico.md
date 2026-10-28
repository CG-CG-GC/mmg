# Guía técnica y defensa del MVP

Esta guía describe el código presente en el workspace, incluidos los cambios
todavía no confirmados en Git. Las referencias a pruebas indican qué cubren,
no una garantía de que cubran todos los casos. Las propuestas históricas se
conservan separadas de esta descripción.

## Arquitectura y flujo

| Capa | Implementación y responsabilidad |
| --- | --- |
| Dominio | `app/domain`: `Entidad`, `Relacion`, `Evidencia`, tipos y `Graph`. Valida objetos y ejecuta algoritmos sin depender de la API o SQLite. |
| Persistencia | `app/persistence`: modelos SQLAlchemy, sesiones, repositorios, conversión y carga del grafo desde SQLite. |
| Aplicación | `GraphApplicationService` coordina escrituras y reconstrucción de la proyección en memoria. |
| API | `app/api`: FastAPI valida solicitudes, expone rutas y traduce errores a HTTP; las consultas de registros y `/grafo` leen repositorios. |
| Frontend | HTML, CSS y JavaScript servido por FastAPI; consulta la API y usa Cytoscape.js para visualizar, no para calcular los algoritmos. |

Ejemplo de creación: el formulario envía `POST /api/v1/entidades`; Pydantic
valida la solicitud, la ruta llama al servicio y el repositorio inserta y
confirma la entidad en SQLite. El servicio carga todas las entidades y
relaciones en un `Graph` nuevo y solo lo publica al terminar la reconstrucción.
El navegador actualiza sus datos desde los endpoints y dibuja el grafo. Los
algoritmos consultan la proyección en memoria; `GET /grafo` construye la
respuesta visual directamente desde los repositorios.

Las transacciones del repositorio y la reconstrucción **no son atómicas entre
sí**: si falla la carga después del commit, la escritura puede existir pese al
error HTTP; el servicio invalida el grafo y bloquea escrituras y algoritmos con
503. Consultá los datos antes de reintentar. No existe endpoint de recuperación:
`reconstruir_grafo()` es un método interno; reiniciar el proceso intenta
reconstruir desde SQLite, siempre que los datos y la base sean válidos.

## Modelo de datos real

El esquema está en `app/persistence/schema.py`. Todas las tablas tienen `id`
entero autogenerado como clave primaria:

| Tabla | Columnas además de `id` | Restricciones |
| --- | --- | --- |
| `tipo_entidad` | `codigo`, `nombre`, `descripcion` | `codigo` único; código y nombre no nulos. |
| `entidad` | `tipo_entidad_id`, `valor`, `valor_normalizado`, `descripcion`, `metadata` | Tipo, valor y valor normalizado no nulos; único `(tipo_entidad_id, valor_normalizado)`; FK a tipo con `RESTRICT`. |
| `tipo_relacion` | `codigo`, `nombre`, `descripcion` | `codigo` único; código y nombre no nulos. |
| `relacion` | `origen_id`, `destino_id`, `tipo_relacion_id`, `descripcion`, `fecha` | Extremos y tipo no nulos; único `(origen_id, destino_id, tipo_relacion_id)`; extremos referencian `entidad` con `CASCADE`, tipo con `RESTRICT`. |
| `evidencia` | `relacion_id`, `fuente`, `descripcion`, `fecha` | Relación y fuente no nulas; FK a relación con `CASCADE`. |

SQLite tiene claves foráneas habilitadas por conexión. Eliminar una entidad
elimina sus relaciones entrantes y salientes y, a su vez, las evidencias de
esas relaciones. Se permiten bucles y relaciones entre los mismos extremos con
tipos distintos; no se permite repetir la misma terna. Las restricciones
indicadas son las del esquema: los objetos del dominio y la API agregan
validaciones, pero no todas son restricciones SQL.

Los catálogos iniciales provienen de los enums del dominio:

- Entidades: `PERSONA`, `ORGANIZACION`, `EMAIL`, `USUARIO`, `DOMINIO`,
  `SITIO_WEB`, `IP`.
- Relaciones: `POSEE`, `UTILIZA`, `TRABAJA_EN`, `ADMINISTRA`, `PERTENECE_A`,
  `APUNTA_A`.

El cliente suministra `valor_normalizado`: todavía no hay una política de
normalización automática. La unicidad compara el valor suministrado junto al
tipo; la respuesta de entidad no incluye ese campo. La metadata es un
diccionario serializado como texto JSON; las fechas opcionales se guardan como
texto ISO. El dominio exige `valor` y `fuente` no blancos, IDs positivos y tipos
válidos; la API verifica longitud mínima también para `valor_normalizado`,
pero no define una normalización ni rechaza por sí sola el texto solo con
espacios en ese campo.

## Grafo y algoritmos

`Graph` mantiene un diccionario de entidades por ID y otro de adyacencia:
cada origen apunta a una lista de objetos `Relacion` **salientes**. Así se
conservan el sentido, el tipo y el ID de cada arista; los nodos aislados tienen
lista vacía. Se admiten varias aristas hacia un mismo destino si cambia el
tipo. `obtener_vecinos` elimina destinos repetidos, pero BFS y DFS iteran las
relaciones salientes directamente y controlan los destinos con `visitados`.

- **BFS:** usa `deque` FIFO; marca cada ID al encolarlo, registra orden,
  nivel y predecesor. Visita por niveles solo los nodos alcanzables siguiendo
  la dirección. El inicial tiene nivel 0 y predecesor `None`.
- **DFS:** función recursiva, marca el nodo al entrar y luego visita sus
  destinos no visitados. Devuelve el orden de visita; no devuelve niveles ni
  predecesores.
- **Camino:** ejecuta BFS completo desde el origen, sigue predecesores desde
  el destino e invierte la lista. Luego busca en la adyacencia de cada origen
  del camino la primera relación que conduce al siguiente nodo. BFS garantiza
  mínimo número de aristas, no menor costo o peso. Con aristas paralelas se
  devuelve la primera relación coincidente en el orden de la lista.

Un ID inicial o extremo inexistente produce error de dominio y 404 en la API.
Origen igual a destino devuelve un nodo y ninguna arista; destino inalcanzable
devuelve `encontrado: false` y listas vacías. Los ciclos y bucles terminan
gracias a `visitados`. El orden depende del orden de las listas; el cargador
lee relaciones por ID y conserva ese orden, no hay ordenamiento adicional por
tipo o valor.

### Complejidad

Sea `Vr` la cantidad de vértices alcanzables desde el origen y `Er` la de
relaciones salientes examinadas desde ellos, incluidas paralelas y bucles. En
el modelo usual de operaciones promedio O(1) de diccionarios y conjuntos:

| Operación en un `Graph` ya construido | Tiempo | Espacio auxiliar y resultado |
| --- | --- | --- |
| BFS | O(Vr + Er): cada nodo se encola una vez y se examinan sus listas salientes. | O(Vr): cola, visitados, orden, niveles y predecesores. |
| DFS | O(Vr + Er): cada nodo se visita una vez y se examinan sus relaciones. | O(Vr): visitados, resultado y pila recursiva en el peor caso. |
| Camino | O(Vr + Er): BFS completo, cadena de predecesores y búsqueda de aristas en las listas de los nodos del camino. Estos nodos son distintos, por lo que la suma de esas búsquedas es a lo sumo Er. | O(Vr), incluyendo resultado de BFS y camino. |

En el peor caso `Vr <= V` y `Er <= E`, de modo que las cotas temporales
también son O(V + E). El propio grafo ocupa O(V + E), sin contar el tamaño de
los textos, metadata y evidencias asociadas. DFS recursivo puede superar el
límite de recursión de Python en cadenas largas.

Estas cotas no describen una solicitud completa ni la reconstrucción tras
escrituras: el cargador consulta y mapea la base, y `agregar_relacion` busca
IDs existentes recorriendo la adyacencia y verifica duplicados por origen.
Por ello, construir el grafo puede requerir hasta O(E(V + E)) trabajo de
verificación en memoria, además de consultas, ordenación y datos asociados;
no debe afirmarse que esa reconstrucción es O(V + E).

## API y uso

Todas las rutas de datos usan el prefijo `/api/v1`:

| Método y ruta | Operación |
| --- | --- |
| `GET`, `POST /entidades` | Listar y crear entidades. |
| `GET`, `DELETE /entidades/{id}` | Consultar y eliminar entidad. |
| `GET`, `POST /relaciones` | Listar y crear relaciones. |
| `GET`, `DELETE /relaciones/{id}` | Consultar y eliminar relación. |
| `POST /relaciones/{id}/evidencias` | Crear evidencia; se lee dentro de la respuesta de relación. No hay endpoints de edición o eliminación de evidencias. |
| `GET /grafo` | Listas `nodes` y `edges` con campos `data` para visualización. |
| `POST /algoritmos/bfs`, `/algoritmos/dfs` | Solicitud `{"id_inicial": 1}`; resultados de recorrido. |
| `POST /algoritmos/camino` | Solicitud `{"id_origen": 1, "id_destino": 2}`; resultado con entidades y relaciones. |

La API devuelve 201 al crear, 204 al eliminar, 404 para recursos inexistentes,
409 para conflictos de integridad, 422 para validación, 500 ante ciertos errores
de persistencia o reconstrucción y 503 si la proyección quedó invalidada.
`/docs` permite probar solicitudes con los IDs reales devueltos; no se deben
suponer IDs fijos en una base existente.

## Trazabilidad a pruebas

Las rutas de la tabla son relativas a la raíz. «Implementado» describe el
código inspeccionado; la columna de pruebas identifica evidencia concreta, no
afirma cobertura completa.

| Funcionalidad | Módulo responsable | Concepto AED3 | Evidencia automatizada | Estado |
| --- | --- | --- | --- | --- |
| Entidades, metadatos y unicidad | `domain/entidad.py`, `persistence/repositories.py`, `api/routes.py` | Identidad, diccionario | `tests/domain/test_entidad.py`, `tests/persistence/test_entidad_repository.py`, `tests/api/test_api.py` | Implementado; sin edición |
| Relaciones dirigidas, paralelas y duplicados | `domain/grafo.py`, `persistence/repositories.py` | Aristas, lista de adyacencia | `tests/domain/test_grafo_operaciones.py`, `tests/persistence/test_relacion_repository.py`, `tests/api/test_api.py` | Implementado; sin edición |
| Evidencia y cascadas | `persistence/schema.py`, `persistence/repositories.py`, `api/routes.py` | Asociación relación-evidencia | `tests/persistence/test_evidencia_repository.py`, `tests/persistence/test_integridad_referencial.py`, `tests/api/test_api.py` | Creación y consulta por relación; sin gestión completa en API o interfaz |
| BFS, ciclos y niveles | `domain/grafo.py` | Cola FIFO, visitados, predecesores | `tests/domain/test_grafo_bfs.py`, `tests/api/test_api.py` | Implementado |
| DFS | `domain/grafo.py` | Recursión, visitados | `tests/domain/test_grafo_dfs.py`, `tests/api/test_api.py` | Implementado |
| Camino mínimo en aristas | `domain/grafo.py` | BFS, predecesores | `tests/domain/test_grafo_camino.py`, `tests/api/test_api.py` | Implementado, no ponderado |
| Reconstrucción y fallo posterior al commit | `application/service.py`, `persistence/graph_loader.py` | Proyección de adyacencia | `tests/application/test_service.py`, `tests/persistence/test_graph_loader.py`, `tests/api/test_api.py` | Implementado con limitación de atomicidad |
| Entrega de interfaz y recursos | `api/main.py`, `frontend/` | Visualización de grafo | `tests/api/test_frontend.py` | Recursos verificados; test automatizado no prueba interacción de navegador |

La ejecución local `python -m pytest -q` en el entorno existente dio
**61 aprobadas, 0 fallidas y 0 omitidas**. Se informó una demostración previa
en navegador real; ese dato no sustituye pruebas automatizadas de interacción
y no se reproduce como una nueva medición en esta guía.

## Guion de demostración y defensa

Usá una base aislada como indica el [README](../README.md#instalación-y-ejecución).
El recorrido propuesto supone una base nueva:

1. **Problema y alcance:** «Queremos registrar relaciones conocidas y
   explorarlas como grafo dirigido. No buscamos recolectar datos OSINT».
2. **Arquitectura:** mostrás navegador, API, servicio, dominio y SQLite;
   explicás que SQLite persiste y `Graph` es una proyección en memoria.
3. **Datos:** creá desde la interfaz tres entidades, por ejemplo `PERSONA Ana`
   (valor normalizado `ana`), `ORGANIZACION Laboratorio` (`laboratorio`) y
   `SITIO_WEB ejemplo.test` (`ejemplo.test`). Confirmá cada escritura.
4. **Relaciones:** creá `Ana TRABAJA_EN Laboratorio` y `Laboratorio UTILIZA
   ejemplo.test`. Mostrá las flechas y seleccioná nodos y aristas.
5. **Algoritmos:** ejecutá BFS y DFS desde Ana; para este grafo lineal ambos
   recorren Ana, Laboratorio y sitio. Ejecutá camino de Ana al sitio: devuelve
   dos relaciones. Invertí los extremos: no existe camino dirigido.
6. **Persistencia:** reiniciá el servidor con la misma ruta de base y actualizá
   la página: los elementos deben seguir presentes. Para evidencias, usá
   `/docs`, creá una sobre una relación y consultá esa relación.
7. **Cierre:** mostrás la suite, explicás la limitación del commit y la
   reconstrucción, y distinguís los trabajos futuros del MVP.

### Preguntas probables

**¿Por qué lista de adyacencia y no matriz?** Permite recorrer directamente
las relaciones salientes y almacenar los objetos de arista, incluso paralelas,
sin reservar una celda por cada par posible. No es una medición comparativa de
rendimiento del proyecto.

**¿Por qué BFS encuentra el camino mínimo?** La cola explora por niveles;
la primera vez que se descubre un nodo se registra un predecesor a distancia
mínima en cantidad de aristas. No sirve para optimizar pesos arbitrarios.

**¿Por qué visitados?** Evita repetir nodos y entrar en ciclos, incluso con
bucles y relaciones paralelas.

**¿Puede cambiar el orden del recorrido?** Sí, depende del orden de las
relaciones en la adyacencia. Tras carga desde la base se insertan por ID.

**¿Qué pasa al borrar una entidad?** SQLite elimina en cascada relaciones
incidentes y sus evidencias; el servicio reconstruye la proyección.

**¿SQLite y el grafo siempre cambian juntos?** No: el commit precede a la
reconstrucción. Un fallo posterior invalida la proyección, pero no deshace la
escritura. Antes de reintentar hay que consultar lo persistido.

**¿Por qué no usar Cytoscape para BFS?** Su función aquí es visual; los
algoritmos propios del dominio hacen explícitas las estructuras estudiadas y
se prueban independientemente.

## Limitaciones y posibles mejoras

**Actuales:** no hay autenticación ni control de acceso; se recomienda uso
local, no exposición directa a Internet. No hay edición, importación masiva,
scraping ni integraciones OSINT. La interfaz no elimina registros ni crea
evidencias. No existe normalización automática ni migraciones de esquema
implementadas; `create_all` no migra tablas existentes. La proyección se
reconstruye por proceso y tras cada escritura: cambios externos a SQLite o
varios procesos no se sincronizan automáticamente. La API puede fallar después
de confirmar una escritura, y DFS tiene límite práctico de recursión.

**Posibles mejoras, no implementadas:** definir normalización por tipo,
incorporar migraciones, mejorar atomicidad y recuperación, sincronizar
proyecciones entre procesos, agregar pruebas automatizadas en navegador y,
si el alcance futuro lo requiere, ampliar la gestión de datos y el control
de acceso. No son requisitos docentes confirmados.
