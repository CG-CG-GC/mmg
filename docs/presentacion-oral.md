# Guion de presentación oral

Guion para una exposición de **10 a 15 minutos**. Cada sección indica el tiempo
aproximado, lo que se muestra en pantalla y lo que se explica en voz alta. La
demostración en vivo está en [demo-presentacion.md](demo-presentacion.md) y la
referencia de uso en [manual-usuario.md](manual-usuario.md).

## Índice de la presentación

| # | Sección | Tiempo | Pantalla |
| --- | --- | --- | --- |
| 1 | Problema que resuelve | 1 min | Diapositiva o pantalla principal |
| 2 | Por qué un grafo | 1 min | Grafo de la demo |
| 3 | Estructuras de datos y grafo dirigido | 1,5 min | Diagrama o código de `Graph` |
| 4 | BFS, DFS y camino más corto | 2 min | Resultados de algoritmos |
| 5 | Complejidad | 1 min | Tabla de complejidad |
| 6 | Arquitectura, tecnologías y persistencia | 1,5 min | Diagrama de capas |
| 7 | Demostración de CRUD y grafo | 2 min | Crear, relacionar, editar, layouts |
| 8 | Demostración de OSINT DNS | 1,5 min | Consulta, revisión y confirmación |
| 9 | Calidad, seguridad y pruebas | 1 min | Terminal con pytest |
| 10 | Limitaciones y mejoras | 1 min | Lista de limitaciones |
| 11 | Conclusión | 0,5 min | Diapositiva final |

Tiempo total: unos 14 minutos, con margen para preguntas.

---

## 1. Problema que resuelve (1 minuto)

**En pantalla:** la pantalla principal de la aplicación, con el grafo de la demo.

**Qué explicar:**

"Mini-Maltego académico resuelve un problema de modelado: registrar entidades,
como personas, organizaciones o dominios, y las relaciones entre ellas, y luego
explorar esa red. El sistema responde preguntas como: qué elementos están conectados
con este, a cuántos pasos está otro, o cuál es la forma más corta de llegar desde
uno hasta otro.

El proyecto es académico. No busca reemplazar una herramienta OSINT profesional ni
recopila información por sí solo: la consulta DNS ocurre solo cuando el usuario la pide,
y no guarda nada hasta que confirma."

## 2. Por qué representar la información como un grafo (1 minuto)

**En pantalla:** el grafo de la demo, con flechas visibles.

**Qué explicar:**

"Las relaciones son el dato central. Una tabla de relaciones permite guardarlas, pero
responder 'cómo se llega de A a B' exige recorrer conexiones, y eso es exactamente lo
que modela un grafo. Usamos un grafo **dirigido** porque la dirección tiene significado:
'Ana trabaja en el laboratorio' no es lo mismo que 'el laboratorio trabaja en Ana'."

## 3. Estructuras de datos y grafo dirigido (1,5 minutos)

**En pantalla:** diagrama con los nodos, las aristas y las evidencias.

**Qué explicar:**

- **Nodo:** una `Entidad`, con identificador, tipo, valor, valor normalizado,
  descripción y metadatos.
- **Arista:** una `Relacion` saliente, con origen, destino, tipo, descripción y fecha.
- **Evidencia:** un registro de la fuente de una relación. Se guarda asociada a una
  relación y no es un nodo.

"En memoria, `Graph` usa un diccionario de entidades por identificador y un
diccionario de **lista de adyacencia**: cada origen tiene una lista de sus relaciones
salientes. Así, recorrer los vecinos de un nodo cuesta lo que tiene de relaciones y no
el total del grafo. Los nodos sin relaciones tienen una lista vacía."

"Para los algoritmos, usamos además una **cola FIFO** (`deque`) en BFS, un conjunto de
**visitados** en BFS y DFS, un diccionario de **niveles** y de **predecesores**, y la
**recursión** en DFS. Son estructuras que vimos en la materia y están implementadas a
mano, no con bibliotecas de grafos."

**Dirección:** "Si existe una relación de A a B, B no puede avanzar hacia A por esa arista.
Por eso, un camino 'de A a B' no implica un camino 'de B a A'."

## 4. BFS, DFS y camino más corto (2 minutos)

**En pantalla:** resultados de BFS, DFS y camino desde Ana Demo (ver demo-presentacion.md).

**BFS (recorrido en anchura):**

"Empieza en la entidad inicial, la pone en la cola y la visita. Cada vez que saca un
nodo de la cola, agrega a la cola sus vecinos todavía no visitados, con nivel igual al
del nodo más uno. Así visita primero los nodos a una relación, luego a dos, y así
sucesivamente. El nivel es la cantidad mínima de relaciones desde el inicio, siguiendo
la dirección."

**DFS (recorrido en profundidad):**

"Entra por un vecino y sigue por ese camino tanto como puede antes de retroceder. Acá
se implementa recursivamente: al entrar en un nodo lo marca como visitado y llama a
cada vecino no visitado. Devuelve el orden de visita. A diferencia de BFS, no devuelve
niveles."

**Camino más corto:**

"Usa BFS completo desde el origen, guarda para cada nodo su predecesor, y reconstruye el
camino desde el destino hacia atrás. Garantiza la **menor cantidad de relaciones**. No
considera pesos: si las relaciones tuvieran costos distintos, BFS no sería suficiente, y
haría falta Dijkstra. Esto lo decimos explícitamente porque es una limitación del
alcance, no un error."

**Diferencias para preguntas:** BFS usa cola y da niveles; DFS usa pila (implícita por
recursión) y da orden de visita; ambos visitan lo alcanzable en O(V + E).

## 5. Complejidad temporal y espacial (1 minuto)

**En pantalla:** la tabla de complejidad del manual técnico ([mvp-academico.md](mvp-academico.md#complejidad)).

**Qué explicar:**

- **BFS:** O(Vr + Er) en tiempo, donde Vr son los vértices alcanzables y Er las relaciones
  salientes examinadas. Espacio O(Vr) para la cola, los visitados, los niveles y los predecesores.
- **DFS:** O(Vr + Er) en tiempo. Espacio O(Vr) entre visitados, resultado y pila recursiva.
- **Camino más corto:** BFS completo más la reconstrucción. La reconstrucción busca la
  relación entre dos nodos recorriendo la lista del origen, y esas búsquedas suman a lo sumo
  Er. Espacio O(Vr).
- En el peor caso, Vr ≤ V y Er ≤ E, así que las cotas son O(V + E).

"Importante: estas cotas describen los algoritmos sobre el grafo ya cargado. La
reconstrucción del grafo desde la base, y la verificación de duplicados al agregar una
relación, cuestan más: recorrer la lista de adyacencia para cada verificación puede
llevar a O(E(V + E)) en la carga. No decimos que la reconstrucción sea O(V + E)."

## 6. Arquitectura, tecnologías y persistencia (1,5 minutos)

**En pantalla:** diagrama de capas y el flujo de una creación.

| Capa | Carpeta | Responsabilidad |
| --- | --- | --- |
| Dominio | `app/domain` | Entidades, relaciones, grafo y algoritmos. No depende de la base ni de la API. |
| Aplicación | `app/application` | Coordina escrituras y reconstrucción del grafo; consulta DNS e incorporación. |
| Persistencia | `app/persistence` | SQLAlchemy, esquema SQLite, repositorios y transacciones. |
| API | `app/api` | Rutas FastAPI, validación con Pydantic y traducción de errores a HTTP. |
| Frontend | `app/frontend` | HTML, CSS y JavaScript sin compilación. Cytoscape.js solo dibuja. |
| Integraciones | `app/integrations` | Adaptador de Google Public DNS. |

**Qué explicar:**

"Elegimos **FastAPI** porque valida las solicitudes con tipos y genera la documentación
(`/docs`) sin escribirla a mano. **SQLite** porque es un archivo local, no requiere
servidor y alcanza para un proyecto de un usuario; SQLAlchemy nos aísla del motor. Para
la visualización, **Cytoscape.js** dibuja el grafo, pero no calcula nada: los
algoritmos corren en el servidor, sobre nuestro dominio.

Un ejemplo: al crear una entidad, la API valida, el servicio llama al repositorio, el
repositorio confirma en SQLite, y luego el servicio carga el grafo completo en una
instancia nueva y la publica solo si la carga terminó bien."

**Persistencia e integridad:** "La base tiene restricciones: una entidad es única por tipo
y valor normalizado, y una relación es única por origen, destino y tipo. Las claves
foráneas están activadas en cada conexión, y borrar una entidad borra sus relaciones y
sus evidencias en cascada."

## 7. Demostración de CRUD y grafo (2 minutos)

**En pantalla:** la aplicación, siguiendo los pasos 3 a 6 de la demo.

**Qué mostrar y explicar:**

1. Crear `Carla Demo`: "El valor normalizado lo ingresa el usuario. No hay una política
   automática todavía."
2. Crear la relación `Carla → Pertenece a → Universidad Demo`: "La flecha tiene sentido."
3. Editar la descripción: "La edición conserva el identificador y las relaciones."
4. Cambiar la distribución: "El layout solo mueve los nodos. Los datos no cambian."

"Si intento crear un dominio que ya existe, la base lo rechaza y la API responde 409.
La eliminación existe en la API, pero la interfaz todavía no la ofrece."

## 8. Demostración de OSINT DNS (1,5 minutos)

**En pantalla:** la sección 06 y el panel de confirmación.

**Qué explicar:**

"La consulta va al servidor, que consulta Google Public DNS para A, AAAA, CNAME, MX y
NS. El resultado es una **vista previa**: no crea nada. Después, el usuario revisa cada
registro, marca los A y AAAA que quiere incorporar, y confirma un lote.

La incorporación ocurre en **una sola transacción**: crea o reutiliza el dominio, las
direcciones IP, las relaciones `APUNTA_A` y las evidencias. Si algo falla, se revierte
todo. Si el dominio tiene dos entidades equivalentes en conflicto, la respuesta es 409 y
no se escribe nada.

Y la procedencia: la fuente y la fecha las declara el cliente. El servidor no vuelve a
consultar el DNS, así que la evidencia dice 'declarada por el cliente'. No la presentamos
como verificada."

## 9. Calidad, seguridad y pruebas (1 minuto)

**En pantalla:** terminal con `pytest -q`.

**Qué explicar:**

- **Pruebas:** 368 aprobadas y 1 omitida. La omitida es la prueba de red, que solo corre si
  se habilita. Las pruebas usan bases temporales y no tocan la base de trabajo.
- **Calidad:** Ruff para estilo y errores; Bandit para problemas de seguridad en el código.
  pip-audit revisa vulnerabilidades en dependencias; está configurado en CI, pero no lo
  ejecutamos en esta entrega.
- **Seguridad:**   Con el comando documentado, el servidor escucha solo en `127.0.0.1`. No tiene
  autenticación y está pensado para uso local. Las respuestas DNS se tratan como no confiables: se validan y se muestran
  como texto.

## 10. Limitaciones y futuras mejoras (1 minuto)

**En pantalla:** la lista de limitaciones del manual (sección 27).

**Decir, sin ocultarlas:**

- **IDNA 2008 no está implementado completamente.** Aplicamos una política propia y
  limitada para nombres internacionales.
- **Los CRUD manuales pueden aceptar representaciones equivalentes de un dominio**, por
  ejemplo en Unicode y en punycode. La incorporación DNS sí lo detecta.
- **La incorporación DNS responde 409 ante entidades ambiguas, sin escrituras parciales.**
- **La sincronización del grafo en memoria se garantiza para un solo proceso.** Con varios
  procesos, cada uno tiene su copia.
- **CNAME, MX y NS todavía no se incorporan**: se muestran solamente.
- **Las evidencias de procedencia declaradas por el cliente no equivalen a una verificación
  independiente.**
- **DFS es recursivo**: en cadenas de más de unos mil nodos puede fallar por el límite de
  recursión de Python. Lo medimos: 900 nodos funcionaron y 1200 no.

"Como mejoras futuras: eliminar desde la interfaz, buscar por texto, implementar IDNA 2008,
hacer DFS iterativo, sincronizar procesos y agregar incorporación de otros tipos de registro."

## 11. Conclusión (30 segundos)

"Modelamos relaciones como un grafo dirigido, implementamos BFS, DFS y el camino más
corto con nuestras propias estructuras, y los conectamos con una base SQLite y una
interfaz. La parte de DNS muestra la diferencia entre consultar, revisar y guardar, con
trazabilidad y con las limitaciones declaradas."

---

## Preparación para preguntas del profesor

### Preguntas probables y respuestas

**¿Por qué lista de adyacencia y no matriz de adyacencia?**
Porque guardamos objetos de relación, con tipo, descripción y fecha, y porque puede haber
varias relaciones entre los mismos nodos si cambia el tipo. Una matriz reserva V² celdas y
complica eso. Con lista, recorrer las salientes de un nodo cuesta lo que tiene. No medimos
rendimiento comparativo.

**¿Por qué BFS encuentra el camino más corto?**
Porque explora por niveles: la primera vez que llega a un nodo, lo hace por el camino con
menos relaciones, y guardamos su predecesor. Eso garantiza mínimo en cantidad de aristas,
no en costo.

**¿Qué pasa con los ciclos?**
Los visitados impiden repetir nodos. Un bucle (origen igual a destino) se admite y no
produce un recorrido infinito.

**¿Por qué DFS es recursivo y qué riesgo tiene?**
Es la forma más directa de expresarlo. El riesgo es que la profundidad de la recursión
está limitada por Python (1000 por defecto). Lo verificamos: falla en cadenas de 1200
nodos y funciona en 900. Una versión iterativa con pila explícita lo resolvería; es una
mejora pendiente.

**¿El orden de DFS es siempre el mismo?**
Depende del orden de las relaciones en la lista de adyacencia, que sigue el orden en que
se cargan desde la base, por identificador. Es determinista para una base dada, pero no
es un orden de negocio.

**¿Por qué el camino de A a B no implica el camino de B a A?**
Porque las relaciones son dirigidas. Solo seguimos aristas en su sentido. Lo mostramos
invirtiendo origen y destino en la demostración.

**¿Qué pasa si hay dos relaciones entre los mismos nodos?**
Si cambia el tipo, se permiten las dos. Para el camino, se devuelve la primera coincidente
en el orden de la lista; no se distingue por tipo ni por costo.

**¿Por qué SQLite y no un servidor de bases de datos?**
Porque el sistema es de un usuario, local, y SQLite es un archivo sin instalación ni
administración. Tiene claves foráneas, restricciones y transacciones. Sus límites aparecen
con varios procesos escribiendo: por eso lo documentamos.

**¿Por qué FastAPI?**
Valida tipos con Pydantic, genera la documentación OpenAPI y permite probar la API desde
`/docs`. Lo mismo sirve la interfaz, sin un servidor adicional.

**¿Qué es Cytoscape.js y qué hace en el proyecto?**
Es una biblioteca de visualización de grafos. Acá solo dibuja los nodos y las flechas, y
permite seleccionar y resaltar. No calcula los algoritmos. Lo incluimos localmente para no
depender de una CDN.

**¿Cómo garantizan la integridad de los datos?**
Con restricciones SQL (unicidad, claves foráneas con cascada), validaciones en el dominio y
la API, y transacciones en la incorporación DNS.

**¿Qué es una transacción y para qué la usan?**
Un conjunto de operaciones que se confirman juntas o se revierten juntas. En la incorporación,
`BEGIN IMMEDIATE` reserva la escritura desde el inicio: el lote completo queda guardado o
nada. Si falla algo, se hace rollback.

**¿La escritura y la reconstrucción del grafo son atómicas?**
No. Primero se confirma la escritura y después se reconstruye el grafo. Si la reconstrucción
falla, la escritura ya existe; el servicio invalida el grafo y responde 503. Por eso
recomendamos consultar los datos antes de reintentar. Lo documentamos como limitación.

**¿Qué son los límites del OSINT en este proyecto?**
Consultamos solo registros DNS públicos, de cinco tipos, un dominio por vez y bajo pedido.
No hacemos escaneo de puertos ni de redes, ni consultas masivas. No hay autenticación; el
uso previsto es local.

**¿Qué es IDNA?**
Son las convenciones para usar nombres de dominio con caracteres no ASCII, como `münchen.de`.
Esos nombres se convierten a una forma ASCII con prefijo `xn--`, llamada punycode o A-label.
Python implementa IDNA 2003, con diferencias respecto de IDNA 2008 en algunos caracteres
(por ejemplo `ß`). Por eso aplicamos una política propia que rechaza esos casos.

**¿Qué significa que una fuente esté declarada y no verificada?**
Que el cliente la informa, por ejemplo la fecha y el nombre del proveedor, y el servidor la
guarda tal cual. No vuelve a consultar el DNS ni comprueba que sea correcta. La evidencia lo
indica con el prefijo `declarada por el cliente: `.

**¿Por qué no usaron una biblioteca de grafos?**
Porque el objetivo es estudiar y defender los algoritmos. Por eso BFS, DFS y el camino están
implementados a mano, con pruebas.

**¿Qué pasa si se cae el servidor a mitad de una operación?**
Si cayó antes de confirmar, la operación no existe. Si cayó después de confirmar, los datos
están en SQLite y el grafo se reconstruye al iniciar. Por eso, ante un error de red, lo
recomendable es actualizar y comprobar antes de reintentar.

**¿Se puede usar con varios usuarios o con varios procesos?**
Con un solo proceso y una sola instancia sí. Con varios procesos, cada uno tiene su copia del
grafo y no se sincronizan. Lo documentamos como limitación.

### Definiciones para repasar

- **Grafo dirigido:** conjunto de nodos y aristas con sentido.
- **Grado de salida:** cantidad de aristas que salen de un nodo; es lo que recorre BFS o DFS desde él.
- **Lista de adyacencia:** para cada nodo, la lista de sus aristas salientes.
- **Cola FIFO:** estructura en la que sale primero lo que entró primero; base de BFS.
- **Pila:** estructura LIFO; en DFS recursivo la pila es la de llamadas.
- **Visitados:** conjunto que evita repetir nodos.
- **Predecesor:** para cada nodo alcanzado, el nodo desde el que se llegó.
- **Camino dirigido:** secuencia de aristas que siguen su sentido.
- **Clave foránea:** columna que referencia una fila de otra tabla; con `CASCADE`, al borrar la
  referenciada se borran las dependientes.
- **Restricción de unicidad:** impide dos filas con la misma combinación de valores.
- **Transacción:** operaciones confirmadas en conjunto o revertidas en conjunto.
- **Rollback:** deshacer una transacción no confirmada.
- **IDNA / punycode:** convenciones para nombres internacionales y su forma ASCII `xn--`.

### Diferencias entre BFS y DFS

| Aspecto | BFS | DFS |
| --- | --- | --- |
| Estructura principal | Cola FIFO | Recursión (pila de llamadas) |
| Orden de visita | Por niveles | Por ramas en profundidad |
| Resultado en el proyecto | Orden, nivel y predecesor (API) | Orden de visita |
| Caminos mínimos en aristas | Sí, por construcción | No es su propósito |
| Riesgo práctico | Memoria de la cola | Límite de recursión en cadenas largas |

### Interpretar caminos y dirección

Un camino se lee siguiendo las flechas. En la demo, `Ana → Trabaja en → Laboratorio → Posee →
portal → Apunta a → example.com` es un camino de 3 relaciones. Desde `example.com` no hay
camino hacia Ana: el sistema responde `encontrado: false` y listas vacías.

### Esquema sugerido de diapositivas (10 diapositivas)

1. **Título:** Mini-Maltego académico. Grafo dirigido, algoritmos y persistencia.
2. **Problema:** qué relaciones se modelan y qué preguntas responde el sistema.
3. **Modelo:** entidades, relaciones y evidencias; ejemplo con la base de demo.
4. **Estructuras de datos:** diccionarios, lista de adyacencia, cola, visitados, niveles y predecesores.
5. **BFS, DFS y camino:** explicación con un ejemplo y tabla de diferencias.
6. **Complejidad:** tablas de tiempo y espacio, con la nota sobre la reconstrucción.
7. **Arquitectura:** capas, FastAPI, SQLite y Cytoscape.
8. **Integridad y transacciones:** restricciones, cascadas, `BEGIN IMMEDIATE` y reconstrucción.
9. **OSINT DNS:** consulta, revisión, confirmación, procedencia declarada.
10. **Calidad y limitaciones:** pruebas, Ruff, Bandit, lista de limitaciones y mejoras.

Si hay espacio, agregá una diapositiva con la demostración (capturas de
[manual-usuario.md](manual-usuario.md)) y otra con la conclusión.
