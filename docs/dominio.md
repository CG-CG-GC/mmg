# **Diseño de Dominio y Motor del Grafo — v1.0**

**Proyecto:** Mini-Maltego académico  
**Materia:** Algoritmos y Estructuras de Datos 3  
**Estado:** Diseño técnico previo a implementación  
**Alcance:** Modelo de dominio, motor del grafo, algoritmos y persistencia  
**Tecnología:** todavía no definida

---

## **0\. Criterio de diseño**

Este documento baja la arquitectura v1.1 un nivel de abstracción.

La intención no es definir todavía cómo se programará, sino establecer **qué debe existir, qué responsabilidades tendrá cada componente y qué contratos deberá respetar la futura implementación**.

Se mantienen las decisiones confirmadas de la arquitectura v1.1 salvo una precisión conceptual:

> **Referencia y Evidencia se consolidan para el MVP en un único concepto `Evidencia`.**

La razón es evitar crear dos objetos separados para información que, en esta etapa, cumple una misma finalidad: documentar de dónde surge una relación y qué información la respalda.

El material de AED3 proporcionado establece grafos como estructuras no lineales compuestas por vértices y aristas, contempla grafos dirigidos y la representación mediante lista de adyacencia. También incluye colas, pilas, recursividad y análisis de complejidad.

---

# **1\. Modelo de dominio**

El dominio mínimo queda compuesto por:

Entidad  
   │  
   ├───────────────┐  
   │               │  
   ▼               ▼  
TipoEntidad     Relacion  
                    │  
                    ├── TipoRelacion  
                    │  
                    └── Evidencia

Los conceptos principales son:

1. **Entidad**  
2. **TipoEntidad**  
3. **Relación**  
4. **TipoRelacion**  
5. **Evidencia**  
6. **Grafo**

No se agregan otras entidades de dominio en esta etapa.

---

# **2\. Entidad**

## **2.1 Propósito**

`Entidad` representa cualquier objeto de información que pueda convertirse en un vértice del grafo.

Ejemplos:

PERSONA  
    Juan Pérez

EMAIL  
    juan@gmail.com

ORGANIZACION  
    Empresa X

DOMINIO  
    empresa.com

La decisión de utilizar una entidad genérica se mantiene.

### **Motivo**

No necesitamos construir una jerarquía:

Entidad  
 ├── Persona  
 ├── Email  
 ├── IP  
 ├── Dominio  
 └── Organización

para resolver el problema actual.

El grafo solamente necesita conocer que existe una entidad con:

* identificador;  
* tipo;  
* valor;  
* información descriptiva.

Crear siete clases especializadas introduciría complejidad sin aportar una ventaja clara al MVP.

---

## **2.2 Atributos**

La entidad tendrá conceptualmente:

| Atributo | Propósito |
| ----- | ----- |
| `id` | Identificador único |
| `tipo` | Tipo de entidad |
| `valor` | Valor principal que identifica o describe la entidad |
| `descripcion` | Información adicional opcional |
| `metadata` | Información adicional no estructural |

### **Ejemplo**

Entidad  
\-------------------------  
id: 15  
tipo: EMAIL  
valor: juan@gmail.com  
descripcion: Correo laboral  
metadata: ...  
---

## **2.3 Identificador**

El `id` será único dentro del sistema.

La identidad de una entidad **no debe depender exclusivamente del texto de `valor`**, porque dos entidades podrían compartir valores en determinados contextos o porque el valor podría cambiar.

Por ejemplo:

Entidad \#15  
EMAIL  
juan@gmail.com

mantiene su identidad aunque posteriormente se modifique la descripción.

---

# **3\. Unicidad de entidades**

Para el MVP se propone una regla de unicidad basada en:

tipo \+ valor normalizado

Por ejemplo:

EMAIL \+ juan@gmail.com

no debería generar dos entidades independientes.

Esto evita:

EMAIL → juan@gmail.com  
EMAIL → juan@gmail.com

como dos vértices distintos cuando representan exactamente el mismo dato.

### **Importante**

La normalización deberá ser específica por tipo.

No se debe asumir que todos los valores pueden transformarse de la misma manera.

Por ejemplo:

* un email puede normalizarse a minúsculas;  
* un dominio puede normalizarse a minúsculas;  
* una descripción de persona no debería tratarse igual.

La implementación concreta de estas normalizaciones queda pendiente de la tecnología.

---

# **4\. Validaciones de Entidad**

Como mínimo:

1. `id` debe ser válido cuando la entidad ya existe.  
2. `tipo` es obligatorio.  
3. `valor` es obligatorio.  
4. `valor` no debe estar vacío.  
5. El tipo debe pertenecer al catálogo de tipos permitidos.  
6. No puede existir otra entidad con la misma combinación `tipo + valor normalizado`.

La `descripcion` es opcional.

`metadata` también será opcional.

---

# **5\. Metadata**

`metadata` debe considerarse una extensión y no el lugar donde almacenar información estructural fundamental.

Por ejemplo, sería razonable:

metadata:  
{  
    "fuente\_original": "registro manual",  
    "observacion\_extra": "dato encontrado durante análisis"  
}

Pero no debería utilizarse para almacenar:

tipo  
id  
origen  
destino

porque esos datos pertenecen al modelo principal.

### **Decisión**

`metadata` queda **permitida pero secundaria**.

No debe convertirse en una estructura paralela que termine reemplazando el modelo de dominio.

---

# **6\. TipoEntidad**

Los tipos iniciales serán:

PERSONA  
ORGANIZACION  
EMAIL  
USUARIO  
DOMINIO  
SITIO\_WEB  
IP

No se agregan más tipos al MVP salvo que una necesidad concreta aparezca durante el análisis.

---

## **6.1 ¿Enum, tabla o clase?**

La decisión debe diferenciar dos contextos.

### **En el dominio/aplicación**

Conceptualmente se comportan como un **conjunto controlado de valores**.

No necesitan convertirse en objetos complejos.

### **En la base de datos**

Se propone una tabla:

TIPO\_ENTIDAD

Esto permite:

* mantener integridad referencial;  
* evitar valores arbitrarios;  
* agregar tipos posteriormente;  
* no depender de valores escritos manualmente en muchas tablas.

No es necesario crear una clase de negocio compleja para `TipoEntidad`.

---

# **7\. Relación**

## **7.1 Propósito**

Una `Relacion` representa una conexión semántica y dirigida entre dos entidades.

Formalmente:

Entidad origen  
      │  
      │ TipoRelacion  
      ▼  
Entidad destino

Ejemplo:

Juan  
 │  
 │ TRABAJA\_EN  
 ▼  
Empresa X

La relación tiene dirección.

---

# **8\. Atributos de Relación**

La propuesta queda:

| Atributo | Obligatorio | Propósito |
| ----- | ----- | ----- |
| `id` | Sí | Identificador |
| `origen` | Sí | Entidad origen |
| `destino` | Sí | Entidad destino |
| `tipo` | Sí | Tipo de relación |
| `descripcion` | No | Explicación |
| `fecha` | No | Fecha asociada |
| `evidencias` | No | Información que respalda la relación |

No se incorpora:

* peso;  
* nivel de confianza;  
* estado;  
* prioridad;  
* puntuación;  
* otros metadatos.

No son necesarios para el MVP.

---

# **9\. ¿Puede una entidad relacionarse consigo misma?**

Sí, técnicamente el modelo de grafo debe permitir un **bucle**:

A ──RELACION──\> A

El material de AED3 contempla los bucles como una propiedad de los grafos.

Sin embargo, las relaciones utilizadas por el dominio normal probablemente no necesitarán bucles.

### **Decisión**

No se prohíben a nivel del motor.

Esto hace que `Grafo` sea un motor de grafos general y evita introducir una restricción artificial.

La aplicación podría impedir determinados tipos de relación reflexiva si posteriormente aparece una regla de negocio que lo requiera.

---

# **10\. Relaciones duplicadas**

Debe distinguirse:

A ──POSEE──\> B

de:

A ──TRABAJA\_EN──\> B

Aunque tengan los mismos extremos, **no son la misma relación**.

Por lo tanto:

### **Permitido**

A ──POSEE──\> B  
A ──TRABAJA\_EN──\> B

### **No permitido como duplicado**

A ──POSEE──\> B  
A ──POSEE──\> B

Para el MVP se define como identidad lógica de la relación:

origen \+ destino \+ tipo

Por lo tanto:

> No pueden existir dos relaciones con el mismo origen, destino y tipo.

Esto no impide relaciones paralelas de tipos diferentes.

---

# **11\. Eliminación de una entidad**

Si se elimina:

Entidad A

también deben eliminarse todas las relaciones que:

* salen de A;  
* llegan a A.

Por ejemplo:

B ──\> A  
A ──\> C  
A ──\> D

Al eliminar A:

B

C

D

deben quedar sin esas relaciones.

Esto se conoce conceptualmente como eliminación de relaciones incidentes.

La operación debe ser **atómica desde la perspectiva del sistema**:

> no debe quedar una relación apuntando a una entidad inexistente.

---

# **12\. Modificación de una relación**

Una relación puede modificarse sin modificar las entidades.

Por ejemplo:

A ──TRABAJA\_EN──\> B

puede cambiar su:

descripcion  
fecha  
evidencias

sin modificar A ni B.

Si se modifica:

origen  
destino  
tipo

la identidad lógica de la relación cambia.

La implementación deberá tratarlo conceptualmente como una modificación controlada o como eliminación \+ creación, pero nunca debe producir temporalmente una relación inválida.

---

# **13\. Evidencia**

## **13.1 Decisión importante**

No se crean dos conceptos:

Referencia  
Evidencia

para el MVP.

Se utilizará:

> **Evidencia**

como concepto único.

Una evidencia puede contener la referencia a la fuente y la información que explica qué respalda.

---

## **13.2 Atributos**

Conceptualmente:

Evidencia  
\-------------------------  
id  
fuente  
descripcion  
fecha

Donde `fuente` puede representar, según el caso:

* URL;  
* documento;  
* referencia textual;  
* fuente manual;  
* otra identificación de procedencia.

No se obliga a que todas las evidencias sean URLs.

---

# **14\. Cardinalidad de Evidencias**

Una relación puede tener:

0..N evidencias

Por ejemplo:

Juan ──TRABAJA\_EN──\> Empresa X  
        │  
        ├── Evidencia 1  
        ├── Evidencia 2  
        └── Evidencia 3

Esto es preferible a almacenar una única fuente dentro de la relación.

La misma relación puede estar respaldada por varias observaciones.

---

# **15\. TipoRelacion**

Los tipos iniciales serán:

POSEE  
UTILIZA  
TRABAJA\_EN  
ADMINISTRA  
PERTENECE\_A  
APUNTA\_A

No se agregan más relaciones inicialmente.

---

# **16\. Semántica de los tipos**

| Tipo | Ejemplo |
| ----- | ----- |
| `POSEE` | Persona → Email |
| `UTILIZA` | Persona → Usuario |
| `TRABAJA_EN` | Persona → Organización |
| `ADMINISTRA` | Persona → Sitio Web |
| `PERTENECE_A` | Sitio Web → Organización |
| `APUNTA_A` | Dominio → IP |

Estas relaciones representan ejemplos de semántica, no una restricción universal de todos los datos futuros.

---

# **17\. ¿Debe el sistema impedir relaciones semánticamente incorrectas?**

Aquí aparece una decisión interesante.

Podríamos construir:

TipoRelacion  
      ↓  
tipos permitidos de origen/destino

por ejemplo:

TRABAJA\_EN  
PERSONA → ORGANIZACION

Pero eso requeriría una estructura adicional de reglas.

Para un MVP de 1,5 meses considero innecesario construir un subsistema completo de restricciones semánticas.

### **Decisión**

El sistema deberá validar:

* existencia de origen;  
* existencia de destino;  
* existencia del tipo de relación.

Pero **no implementará inicialmente un motor genérico de compatibilidad de tipos**.

La coherencia semántica será responsabilidad de la capa de aplicación y de los datos que se carguen.

Esto mantiene el dominio simple.

---

# **18\. Modelo de objetos**

El conjunto conceptual queda:

┌───────────────────┐  
│     Entidad       │  
├───────────────────┤  
│ id                │  
│ tipo              │  
│ valor             │  
│ descripcion       │  
│ metadata          │  
└─────────┬─────────┘  
          │  
          │ origen / destino  
          ▼  
┌───────────────────┐  
│     Relacion      │  
├───────────────────┤  
│ id                │  
│ origen            │  
│ destino           │  
│ tipo              │  
│ descripcion       │  
│ fecha             │  
└─────────┬─────────┘  
          │  
          │ 0..N  
          ▼  
┌───────────────────┐  
│     Evidencia     │  
├───────────────────┤  
│ id                │  
│ fuente            │  
│ descripcion       │  
│ fecha             │  
└───────────────────┘

TipoEntidad ── catálogo  
TipoRelacion ─ catálogo  
---

# **19\. Responsabilidad de cada clase**

## **Entidad**

Responsable de representar un vértice del dominio.

No debe:

* ejecutar BFS;  
* consultar SQL;  
* dibujar el grafo;  
* comunicarse con APIs.

---

## **Relacion**

Representa una arista dirigida.

Debe conocer:

origen  
destino  
tipo

y sus metadatos.

No debe ejecutar algoritmos de recorrido.

---

## **Evidencia**

Representa información que respalda una relación.

No debe decidir si una relación es válida.

---

## **TipoEntidad**

Representa el tipo controlado de una entidad.

No necesita lógica compleja.

---

## **TipoRelacion**

Representa el tipo controlado de una relación.

No necesita lógica compleja.

---

# **20\. Grafo**

El `Grafo` es una pieza diferente.

No representa una entidad del dominio.

Es la **estructura de datos que organiza entidades y relaciones en memoria**.

Esta distinción es fundamental:

Entidad  
\= dato del dominio

Grafo  
\= estructura de datos  
---

# **21\. Estructura interna del Grafo**

Se propone conceptualmente:

Grafo  
│  
├── entidades  
│      └── id → Entidad  
│  
└── listaAdyacencia  
       ├── idA → \[Relacion, Relacion\]  
       ├── idB → \[Relacion\]  
       └── idC → \[\]

Esto utiliza dos estructuras complementarias.

### **Estructura principal**

Lista de adyacencia

### **Estructura auxiliar**

Tabla hash / diccionario  
---

# **22\. ¿Por qué guardar Relaciones y no solamente Entidades?**

La lista de adyacencia podría ser:

A → \[B, C\]

pero perderíamos información sobre las relaciones.

El proyecto necesita conocer:

A ──POSEE──\> B

no simplemente:

A → B

Por eso la propuesta es:

A → \[Relacion1, Relacion2\]

Cada `Relacion` contiene:

origen  
destino  
tipo  
...

Esto permite que el algoritmo recorra el grafo y que la interfaz posteriormente pueda mostrar la semántica de cada conexión.

---

# **23\. ¿Por qué utilizar IDs internamente?**

Aunque una relación conceptualmente referencia objetos `Entidad`, la estructura de adyacencia puede trabajar con identificadores.

Ejemplo:

15 → \[Relacion 21, Relacion 25\]

y:

entidades\[15\] → Entidad

Esto evita duplicar objetos y facilita la persistencia.

La implementación concreta podrá utilizar referencias/objetos internamente, pero el contrato conceptual se mantiene basado en identificadores.

---

# **24\. Interfaz pública del Grafo**

La interfaz mínima propuesta es:

agregarEntidad(entidad)  
eliminarEntidad(id)  
buscarEntidad(id)  
existeEntidad(id)

agregarRelacion(relacion)  
eliminarRelacion(id)  
buscarRelacion(id)  
existeRelacion(id)

obtenerVecinos(id)

bfs(idInicial)  
dfs(idInicial)

buscarCamino(idOrigen, idDestino)

No se agrega una enorme cantidad de operaciones.

---

# **25\. `agregarEntidad`**

### **Propósito**

Agregar un vértice al grafo.

### **Entrada**

Entidad

### **Resultado**

Confirmación de incorporación.

### **Precondiciones**

* entidad válida;  
* ID disponible;  
* tipo válido;  
* valor válido.

### **Errores**

* entidad duplicada;  
* entidad inválida.

### **Complejidad esperada**

Con tabla hash:

O(1)

promedio para la inserción/búsqueda por ID.

---

# **26\. `eliminarEntidad`**

### **Propósito**

Eliminar una entidad y sus relaciones incidentes.

### **Entrada**

idEntidad

### **Resultado**

Entidad eliminada.

### **Precondición**

La entidad debe existir.

### **Complejidad**

Si se utiliza solamente la lista de adyacencia:

O(V \+ E)

porque es necesario identificar relaciones entrantes y salientes.

No se agrega inicialmente una segunda estructura de índice inverso solamente para optimizar esta operación.

---

# **27\. `buscarEntidad`**

### **Propósito**

Obtener una entidad por ID.

### **Complejidad**

Con tabla hash auxiliar:

O(1)

promedio.

---

# **28\. `agregarRelacion`**

### **Propósito**

Agregar una arista dirigida.

### **Entrada**

Relacion

### **Precondiciones**

* origen existe;  
* destino existe;  
* tipo válido;  
* relación no duplicada.

### **Resultado**

Relación incorporada.

### **Complejidad**

Con acceso directo a la lista del origen:

O(grado\_salida(origen))

si se verifica duplicación recorriendo las relaciones salientes.

Para el MVP esto es suficiente.

---

# **29\. `eliminarRelacion`**

### **Propósito**

Eliminar una relación existente.

### **Entrada**

idRelacion

### **Resultado**

Relación eliminada.

### **Complejidad**

Si solamente se mantiene la lista de adyacencia:

O(V \+ E)

en el peor caso para localizarla.

Podría incorporarse un índice:

idRelacion → Relacion

pero no es necesario inicialmente.

---

# **30\. `obtenerVecinos`**

### **Propósito**

Obtener los vértices alcanzables directamente desde una entidad.

Para:

A → B  
A → C

los vecinos salientes de A son:

B, C

### **Complejidad**

O(grado\_salida(A))  
---

# **31\. Dirección del recorrido**

Como el grafo es dirigido:

A → B

BFS o DFS desde A puede llegar a B.

Pero BFS o DFS desde B **no puede volver automáticamente a A**.

Esto es una consecuencia directa de la decisión de utilizar un digrafo.

---

# **32\. BFS — contrato**

## **Entrada**

idInicial

## **Salida propuesta**

No devolver simplemente una lista.

Se propone que el resultado conceptual contenga:

ResultadoBFS  
├── ordenRecorrido  
├── niveles  
└── predecesores

Esto proporciona información útil tanto para análisis como para futuras operaciones de caminos.

---

# **33\. Orden de recorrido**

Ejemplo:

A  
├── B  
├── C  
└── D

BFS podría devolver:

\[A, B, C, D\]

El orden exacto entre vecinos dependerá del orden en la lista de adyacencia.

No debe asumirse un orden alfabético salvo que posteriormente se establezca explícitamente.

---

# **34\. Niveles**

BFS naturalmente permite conocer la distancia en cantidad de aristas desde el origen.

Ejemplo:

A → B → D  
A → C

Resultado:

A \= nivel 0  
B \= nivel 1  
C \= nivel 1  
D \= nivel 2

Esto es útil para visualizar el grafo posteriormente.

---

# **35\. Cola de BFS**

BFS utilizará una **cola FIFO**.

El material de AED3 define las colas como estructuras FIFO, con inserción por el final y extracción por el principio.

Conceptualmente:

encolar(A)

desencolar(A)  
encolar(B)  
encolar(C)

desencolar(B)  
...  
---

# **36\. Visitados**

BFS deberá mantener un conjunto:

visitados

Esto evita recorrer repetidamente un vértice.

Es imprescindible cuando existen ciclos:

A → B  
B → C  
C → A

Sin `visitados`, el algoritmo podría recorrer indefinidamente el ciclo.

---

# **37\. Pseudocódigo conceptual BFS**

BFS(origen):

    si origen no existe:  
        error

    crear cola  
    crear conjunto visitados  
    crear predecesores  
    crear niveles  
    crear ordenRecorrido

    marcar origen como visitado  
    nivel\[origen\] \= 0  
    encolar origen

    mientras cola no esté vacía:

        actual \= desencolar()

        agregar actual a ordenRecorrido

        para cada relación saliente de actual:

            vecino \= destino de relación

            si vecino no está visitado:

                marcar vecino como visitado  
                predecesor\[vecino\] \= actual  
                nivel\[vecino\] \= nivel\[actual\] \+ 1

                encolar vecino

    devolver resultado  
---

# **38\. Complejidad de BFS**

Con lista de adyacencia:

### **Tiempo**

O(V \+ E)

porque cada vértice y cada arista relevante se procesa como parte del recorrido.

### **Espacio auxiliar**

O(V)

por:

* visitados;  
* cola;  
* niveles;  
* predecesores;  
* resultado.

La complejidad algorítmica y la diferencia entre complejidad temporal y espacial forman parte del material de AED3.

---

# **39\. DFS**

DFS realizará una exploración en profundidad.

Se propone utilizar:

> **DFS recursivo**

como implementación académica principal.

---

# **40\. ¿Por qué DFS recursivo?**

El material de AED3 incluye específicamente la recursividad como técnica y señala los recorridos como una de sus aplicaciones.

El grafo proporciona un caso real donde puede demostrarse:

DFS  
\+  
Recursividad  
\+  
Conjunto de visitados

Esto hace que la elección sea defendible académicamente.

---

# **41\. DFS mediante pila vs recursivo**

### **Recursivo**

Ventajas:

* más directo conceptualmente;  
* menor cantidad de estructuras explícitas;  
* demuestra recursividad;  
* código futuro más sencillo.

Desventaja:

* depende de la profundidad de llamadas.

### **Mediante pila**

Ventajas:

* controla explícitamente la estructura;  
* evita depender de la pila de llamadas;  
* puede ser más robusto ante grafos extremadamente profundos.

Desventaja:

* requiere administrar explícitamente una pila.

El material de AED3 contempla pilas como estructuras LIFO y menciona la pila de llamadas como uno de sus usos.

### **Decisión**

Para este proyecto:

> **DFS recursivo será la implementación principal.**

No se espera trabajar con grafos de profundidad suficiente como para convertir la pila de llamadas en un problema real del MVP.

La versión iterativa queda como posible alternativa futura, no como requisito.

---

# **42\. Contrato DFS**

## **Entrada**

idInicial

## **Salida**

ResultadoDFS  
├── ordenRecorrido  
└── predecesores

No necesita niveles como requisito principal.

---

# **43\. Pseudocódigo conceptual DFS**

DFS(origen):

    si origen no existe:  
        error

    crear conjunto visitados  
    crear lista recorrido  
    crear mapa predecesores

    visitar(origen)

    devolver resultado

Y conceptualmente:

visitar(actual):

    marcar actual como visitado  
    agregar actual al recorrido

    para cada relación saliente:

        vecino \= destino

        si vecino no está visitado:

            predecesor\[vecino\] \= actual

            visitar(vecino)

El caso base implícito es:

si el vecino ya fue visitado:  
    no continuar por ese camino

La recursividad requiere una condición de terminación para evitar desbordamientos de pila; este principio está contemplado en el material de AED3.

---

# **44\. Complejidad DFS**

Con lista de adyacencia:

### **Tiempo**

O(V \+ E)

### **Espacio auxiliar**

O(V)

considerando:

* visitados;  
* predecesores;  
* recorrido;  
* profundidad de la recursión.

---

# **45\. Búsqueda de caminos**

Se define:

buscarCamino(origen, destino)

La operación devolverá:

> **un camino**, concretamente un camino mínimo en cantidad de aristas cuando se utiliza BFS.

No se buscarán todos los caminos.

---

# **46\. ¿Por qué un solo camino?**

Buscar todos los caminos puede aumentar considerablemente la complejidad y no es necesario para el MVP.

La necesidad del proyecto es responder:

> "¿Existe una conexión entre estas dos entidades y cuál es un camino posible?"

Por ejemplo:

Juan  
 ↓  
Empresa  
 ↓  
Dominio  
 ↓  
IP

Eso es suficiente para demostrar el concepto.

---

# **47\. Algoritmo para caminos**

Se utilizará:

> **BFS \+ predecesores**

porque BFS permite encontrar el camino con menor cantidad de aristas en un grafo no ponderado.

No se utilizará Dijkstra porque:

* no existen pesos;  
* los pesos fueron descartados del MVP;  
* agregarlo sería innecesario.

---

# **48\. Reconstrucción del camino**

Supongamos:

A → B → C → D

Durante BFS:

predecesor\[B\] \= A  
predecesor\[C\] \= B  
predecesor\[D\] \= C

Para reconstruir:

D  
↑  
C  
↑  
B  
↑  
A

Luego se invierte el resultado:

A → B → C → D  
---

# **49\. ¿El camino debe incluir las relaciones?**

Sí.

La salida no debería limitarse a:

\[A, B, C, D\]

El resultado conceptual deberá permitir conocer:

A  
 │  
 ├── relacion\_AB  
 ▼  
B  
 │  
 ├── relacion\_BC  
 ▼  
C  
 │  
 ├── relacion\_CD  
 ▼  
D

Esto será importante para la futura visualización.

Por lo tanto, el resultado de camino conceptualmente será:

Camino  
├── entidades  
└── relaciones  
---

# **50\. Casos de búsqueda de camino**

### **Origen inexistente**

Error de entrada.

### **Destino inexistente**

Error de entrada.

### **No existe camino**

Resultado:

sinCamino

No es un error técnico; es un resultado válido del análisis.

### **Origen \= destino**

Resultado:

camino \= \[origen\]

con cero relaciones.

Esto evita considerar el caso como error.

---

# **51\. Complejidad de buscarCamino**

Como utiliza BFS:

O(V \+ E)

en el peor caso.

Espacio auxiliar:

O(V)  
---

# **52\. Casos límite del motor**

| Caso | Comportamiento |
| ----- | ----- |
| Grafo vacío | Operaciones de búsqueda devuelven vacío/no encontrado |
| Entidad inexistente | Error controlado |
| Entidad duplicada | Rechazo |
| Relación a entidad inexistente | Rechazo |
| Relación duplicada | Rechazo |
| Relación diferente entre mismos extremos | Permitida |
| Bucle A→A | Permitido por el motor |
| Ciclo | Permitido |
| Múltiples caminos | BFS devuelve uno mínimo |
| Ningún camino | Resultado sin camino |
| Origen \= destino | Camino trivial |
| Entidad aislada | BFS/DFS devuelve solamente esa entidad |
| Eliminación de entidad | Elimina relaciones incidentes |
| Eliminación de relación inexistente | Error controlado |
| Grafo vacío \+ BFS | Resultado vacío/error según contrato de entrada |
| Grafo vacío \+ DFS | Resultado vacío/error según contrato de entrada |

---

# **53\. Modelo relacional**

Se propone el siguiente modelo:

TIPO\_ENTIDAD  
      │  
      │  
      ▼  
  ENTIDAD  
      │  
      │  
      ├───────────────┐  
      │               │  
      ▼               ▼  
 RELACION         EVIDENCIA  
      │  
      │  
      ▼  
TIPO\_RELACION  
---

# **54\. Tabla TIPO\_ENTIDAD**

TIPO\_ENTIDAD  
\-------------------------  
id PK  
codigo UNIQUE  
nombre  
descripcion

Ejemplo:

1 | PERSONA | Persona  
2 | EMAIL | Correo electrónico  
3 | IP | Dirección IP  
---

# **55\. Tabla ENTIDAD**

ENTIDAD  
\-------------------------  
id PK  
tipo\_entidad\_id FK  
valor  
descripcion  
metadata

Restricción conceptual:

UNIQUE(tipo\_entidad\_id, valor\_normalizado)

Si se requiere conservar el valor original y el normalizado, puede incorporarse:

valor\_original  
valor\_normalizado

La necesidad exacta de esta separación queda pendiente de la tecnología elegida.

---

# **56\. Tabla TIPO\_RELACION**

TIPO\_RELACION  
\-------------------------  
id PK  
codigo UNIQUE  
nombre  
descripcion

Ejemplo:

1 | POSEE  
2 | UTILIZA  
3 | TRABAJA\_EN  
4 | ADMINISTRA  
5 | PERTENECE\_A  
6 | APUNTA\_A  
---

# **57\. Tabla RELACION**

RELACION  
\-------------------------  
id PK  
origen\_id FK → ENTIDAD  
destino\_id FK → ENTIDAD  
tipo\_relacion\_id FK → TIPO\_RELACION  
descripcion  
fecha

Restricción:

UNIQUE(  
    origen\_id,  
    destino\_id,  
    tipo\_relacion\_id  
)

Esto representa directamente una relación dirigida.

Por ejemplo:

origen\_id \= 10  
destino\_id \= 25  
tipo \= TRABAJA\_EN

significa:

10 ──TRABAJA\_EN──\> 25

No se crea automáticamente:

25 ──TRABAJA\_EN──\> 10  
---

# **58\. Tabla EVIDENCIA**

EVIDENCIA  
\-------------------------  
id PK  
relacion\_id FK  
fuente  
descripcion  
fecha

Cardinalidad:

RELACION 1 ───── 0..N EVIDENCIAS

Esto permite:

Relacion \#50  
   ├── Evidencia \#1  
   ├── Evidencia \#2  
   └── Evidencia \#3  
---

# **59\. ¿Por qué no crear una tabla separada REFERENCIA?**

Porque en el MVP no existe una necesidad clara de distinguir:

Referencia

de:

Evidencia

Una evidencia ya puede contener:

fuente \= URL / documento / referencia

y:

descripcion \= qué demuestra

Si en una futura versión se necesita administrar fuentes como objetos independientes reutilizables, podría evolucionarse hacia:

FUENTE  
   │  
   └── EVIDENCIA

pero no se justifica ahora.

---

# **60\. Integridad referencial**

La base de datos debe impedir relaciones hacia entidades inexistentes.

Por lo tanto:

RELACION.origen\_id  
RELACION.destino\_id

deben referenciar entidades válidas.

Al eliminar una entidad, conceptualmente se deben eliminar sus relaciones.

Las evidencias asociadas a esas relaciones también deben eliminarse.

Esto puede resolverse mediante restricciones de integridad referencial apropiadas en la implementación.

---

# **61\. BD y Grafo no son lo mismo**

La separación queda:

                   PERSISTENCIA  
                         │  
                         ▼  
                  Base de datos  
                         │  
                         │ cargar  
                         ▼  
                    ┌─────────┐  
                    │  Grafo  │  
                    └─────────┘  
                         │  
                 Lista de adyacencia  
                         │  
              ┌──────────┼─────────┐  
              ▼          ▼         ▼  
             BFS        DFS      Camino

La base de datos representa el estado persistente.

El grafo representa el estado necesario para ejecutar eficientemente los algoritmos.

---

# **62\. Construcción del Grafo desde BD**

Proceso conceptual:

1\. Crear Grafo vacío.

2\. Leer tipos y entidades.

3\. Crear los vértices.

4\. Registrar cada entidad.

5\. Leer relaciones.

6\. Para cada relación:  
       verificar origen.  
       verificar destino.  
       agregar relación al grafo.

7\. Grafo listo.

Las evidencias no son necesarias para ejecutar BFS/DFS.

Pueden permanecer asociadas a las relaciones almacenadas y recuperarse cuando la interfaz necesite mostrar información detallada.

---

# **63\. ¿Cuándo se carga el Grafo?**

Para el MVP se propone:

> cargar el grafo cuando se inicia el contexto de trabajo y reconstruirlo cuando sea necesario después de modificaciones persistentes.

No es necesario que cada consulta BFS consulte la base de datos.

Esto sería contraproducente para el propósito académico.

---

# **64\. Sincronización BD ↔ Grafo**

Este es un punto importante.

No queremos:

Grafo → SQL

mezclado dentro del motor.

En su lugar:

Servicio de aplicación  
       │  
       ├── Persistencia  
       │  
       └── Grafo

Por ejemplo:

Crear entidad  
      │  
      ├── guardar en BD  
      │  
      └── agregar al Grafo

Y:

Crear relación  
      │  
      ├── guardar en BD  
      │  
      └── agregar al Grafo  
---

# **65\. Consistencia**

Las operaciones que modifiquen simultáneamente BD y grafo deberán mantener una regla:

> No considerar completada una operación si solamente se modificó uno de los dos estados.

Por ejemplo, si:

BD: relación creada  
Grafo: relación no creada

el sistema estaría inconsistente.

La futura capa de aplicación será responsable de coordinar ambas operaciones.

---

# **66\. Responsabilidades por capa**

## **Interfaz**

Responsable de:

* mostrar información;  
* recibir acciones;  
* representar el grafo;  
* mostrar resultados.

No debe implementar BFS.

---

## **Aplicación / Servicios**

Responsable de:

* casos de uso;  
* validaciones de negocio;  
* coordinación;  
* persistencia;  
* actualización del grafo.

---

## **Dominio**

Responsable de:

* Entidad;  
* Relación;  
* Evidencia;  
* tipos;  
* reglas propias del dominio.

---

## **Motor del Grafo**

Responsable de:

* almacenamiento en memoria;  
* lista de adyacencia;  
* recorridos;  
* búsqueda de caminos.

No conoce:

HTML  
SQL  
HTTP  
API externas  
---

## **Persistencia**

Responsable de:

* guardar entidades;  
* recuperar entidades;  
* guardar relaciones;  
* recuperar relaciones;  
* guardar evidencias.

No ejecuta BFS ni DFS.

---

## **Integraciones**

Responsables de:

* comunicarse con APIs externas;  
* transformar resultados externos;  
* producir entidades/relaciones.

No deben ser necesarias para que el grafo funcione.

---

# **67\. Dependencias**

La dependencia conceptual recomendada es:

Interfaz  
   ↓  
Aplicación  
   ↓  
Dominio / Motor  
   ↓  
Persistencia

pero el motor del grafo **no dependerá de persistencia**.

La dirección correcta es:

Persistencia → datos  
Aplicación → coordina  
Grafo → procesa

No:

Grafo → SQL  
---

# **68\. Invariantes del dominio**

Las siguientes reglas deben mantenerse siempre.

### **INV-01**

Toda entidad tiene un identificador único.

### **INV-02**

Toda entidad tiene un tipo válido.

### **INV-03**

Toda entidad tiene un valor no vacío.

### **INV-04**

No existen dos entidades equivalentes según la regla de unicidad.

### **INV-05**

Toda relación tiene origen válido.

### **INV-06**

Toda relación tiene destino válido.

### **INV-07**

Toda relación tiene un tipo válido.

### **INV-08**

Una relación es dirigida.

### **INV-09**

No existen dos relaciones con:

origen \+ destino \+ tipo

idénticos.

### **INV-10**

No existen relaciones persistidas hacia entidades inexistentes.

### **INV-11**

Una evidencia siempre pertenece a una relación existente.

### **INV-12**

El grafo en memoria no debe contener referencias a entidades inexistentes.

---

# **69\. Invariantes vs reglas de implementación**

Es importante no mezclar ambos conceptos.

### **Invariante de dominio**

Una relación debe tener origen y destino.

Es una regla conceptual.

### **Regla de implementación**

Usar un diccionario para localizar entidades.

Es una decisión técnica.

Si mañana se cambiara el diccionario por otra estructura, el dominio seguiría siendo válido.

---

# **70\. Estructuras auxiliares**

El motor utilizará conceptualmente:

| Estructura | Uso |
| ----- | ----- |
| Lista de adyacencia | Estructura principal del grafo |
| Tabla hash/diccionario | Localización de entidades |
| Cola | BFS |
| Conjunto de visitados | BFS/DFS |
| Mapa de predecesores | BFS/DFS/caminos |
| Lista de resultados | Orden de recorrido |
| Pila de llamadas | DFS recursivo |

Cada una tiene una función concreta.

No se agregan listas enlazadas, árboles, ABB, B/B+ u otras estructuras solamente para demostrar contenido.

---

# **71\. ¿Por qué no matriz de adyacencia?**

La alternativa sería:

     A B C D  
A     0 1 0 1  
B     0 0 1 0  
C     0 0 0 1  
D     0 0 0 0

Pero esto requeriría espacio:

O(V²)

y representaría también muchas relaciones inexistentes.

Para el sistema planteado, la lista de adyacencia representa directamente:

A → B, D  
B → C  
C → D  
D → \-

La elección de lista de adyacencia se mantiene como la representación principal y coincide con una de las representaciones de grafos contempladas por AED3.

---

# **72\. Casos límite y pruebas futuras**

Los casos definidos en esta etapa deberán convertirse posteriormente en pruebas.

Por ejemplo:

### **Test de entidad duplicada**

Crear EMAIL juan@gmail.com  
Crear EMAIL juan@gmail.com

Resultado esperado:  
segunda operación rechazada

### **Test de ciclo**

A → B  
B → C  
C → A

BFS(A)

Resultado:  
A, B, C

No debe entrar en ciclo infinito.

### **Test de camino inexistente**

A → B

buscarCamino(A, C)

Resultado:  
sin camino

### **Test de entidad aislada**

A

BFS(A)

Resultado:  
\[A\]  
---

# **73\. Trazabilidad AED3**

| Concepto AED3 | Elemento del sistema | Demostración |
| ----- | ----- | ----- |
| Grafo | `Grafo` | Entidades \+ relaciones |
| Grafo dirigido | Relaciones | Origen → destino |
| Lista de adyacencia | `listaAdyacencia` | Representación principal |
| Estructura no lineal | Grafo | Red de conexiones |
| Cola | BFS | FIFO para exploración |
| Recursividad | DFS | Exploración recursiva |
| Complejidad temporal | BFS/DFS | O(V+E) |
| Complejidad espacial | BFS/DFS | O(V) auxiliar |
| Tabla hash | Índice de entidades | Búsqueda promedio O(1) |
| OOP | Dominio/Grafo | Encapsulamiento y responsabilidades |
| Testing | Motor del grafo | Casos unitarios |
| Refactoring | Evolución | Mejora de diseño sin cambiar comportamiento |

El material proporcionado también contempla principios de POO como encapsulamiento, acoplamiento y cohesión, además de testing y refactoring.

---

# **74\. Qué conceptos de AED3 NO se incorporan**

No se utilizarán deliberadamente:

* árboles;  
* ABB;  
* árboles B;  
* árboles B+;  
* listas enlazadas como estructura principal;  
* matriz de adyacencia;  
* pilas explícitas para DFS;  
* algoritmos de ordenamiento;  
* búsqueda binaria;  
* patrones de diseño innecesarios.

Esto **no representa una carencia del proyecto**.

El criterio es utilizar los conceptos que resuelven problemas reales.

El propio material del proyecto establece evitar el sobre-diseño académico y no intentar utilizar todos los contenidos.

---

# **75\. Modelo completo**

La arquitectura técnica resultante puede resumirse así:

                        ┌─────────────────┐  
                         │     USUARIO     │  
                         └────────┬────────┘  
                                  │  
                                  ▼  
                         ┌─────────────────┐  
                         │    INTERFAZ     │  
                         └────────┬────────┘  
                                  │  
                                  ▼  
                    ┌──────────────────────────┐  
                    │ SERVICIOS / CASOS DE USO │  
                    └───────┬──────────┬───────┘  
                            │          │  
                 ┌──────────┘          └──────────┐  
                 ▼                                ▼  
        ┌─────────────────┐              ┌─────────────────┐  
        │  MOTOR GRAFO    │              │  PERSISTENCIA   │  
        └────────┬────────┘              └────────┬────────┘  
                 │                                │  
                 ▼                                ▼  
       ┌────────────────────┐             ┌─────────────────┐  
       │ Lista adyacencia   │             │ Base de datos   │  
       │                    │             │ relacional      │  
       │ Hash entidades     │             └─────────────────┘  
       │ BFS                │  
       │ DFS                │  
       │ Caminos            │  
       └────────┬───────────┘  
                │  
                ▼  
       ┌────────────────────┐  
       │ DOMINIO            │  
       │                    │  
       │ Entidad            │  
       │ Relacion           │  
       │ Evidencia          │  
       │ TipoEntidad        │  
       │ TipoRelacion       │  
       └────────────────────┘  
---

# **76\. Matriz de decisiones nuevas**

| ID | Decisión | Justificación | Estado |
| ----- | ----- | ----- | ----- |
| DOM-01 | Mantener `Entidad` genérica | Evita jerarquías innecesarias | **Propuesta** |
| DOM-02 | Unicidad por tipo \+ valor normalizado | Evita entidades duplicadas | **Propuesta** |
| DOM-03 | Consolidar Referencia/Evidencia | Reduce complejidad del MVP | **Propuesta** |
| DOM-04 | Una relación admite 0..N evidencias | Permite múltiples fuentes | **Propuesta** |
| REL-01 | Relaciones dirigidas | Mantiene decisión arquitectónica | **Confirmada** |
| REL-02 | Identidad de relación \= origen \+ destino \+ tipo | Evita duplicados exactos | **Propuesta** |
| REL-03 | Relaciones diferentes pueden unir los mismos extremos | Permite semánticas distintas | **Propuesta** |
| REL-04 | Bucles permitidos por el motor | AED3 contempla bucles | **Propuesta** |
| GRA-01 | Lista de adyacencia como estructura principal | Decisión arquitectónica | **Confirmada** |
| GRA-02 | Adyacencia almacena relaciones | Conserva semántica de las aristas | **Propuesta** |
| GRA-03 | Hash auxiliar para entidades | Búsqueda eficiente | **Propuesta** |
| GRA-04 | No índice inverso en MVP | Evita complejidad adicional | **Propuesta** |
| ALG-01 | BFS devuelve recorrido, niveles y predecesores | Reutilización para análisis/caminos | **Propuesta** |
| ALG-02 | DFS recursivo | Demuestra recursividad real | **Propuesta** |
| ALG-03 | Buscar camino devuelve un camino mínimo | Suficiente para MVP | **Propuesta** |
| ALG-04 | Camino incluye entidades y relaciones | Necesario para futura visualización | **Propuesta** |
| BD-01 | BD relacional | Persistencia separada del grafo | **Confirmada** |
| BD-02 | Tipos como tablas de catálogo | Integridad y extensibilidad | **Propuesta** |
| BD-03 | Evidencia como tabla independiente | Permite 0..N evidencias por relación | **Propuesta** |
| ARC-01 | Grafo independiente de persistencia | Testabilidad y bajo acoplamiento | **Propuesta** |
| ARC-02 | Servicios coordinan BD \+ Grafo | Mantiene consistencia | **Propuesta** |
| ARC-03 | APIs externas fuera del núcleo | Reduce dependencia | **Confirmada** |

---

# **77\. Decisiones confirmadas de Arquitectura v1.1**

Estas no se vuelven a abrir en esta etapa:

| ID | Decisión |
| ----- | ----- |
| ARCH-01 | Aplicación web |
| ARCH-02 | Monolito modular |
| ARCH-03 | Base de datos relacional |
| ARCH-04 | Grafo dirigido |
| ARCH-05 | Relaciones tipadas |
| ARCH-06 | Grafo en memoria mediante lista de adyacencia |
| ARCH-07 | BFS |
| ARCH-08 | DFS |
| ARCH-09 | Búsqueda de caminos |
| ARCH-10 | APIs externas solamente como enriquecimiento |
| ARCH-11 | Graph Database fuera del MVP |
| ARCH-12 | Microservicios fuera del MVP |
| ARCH-13 | Scraping masivo fuera del MVP |
| ARCH-14 | Escaneo intrusivo fuera del MVP |

---

# **78\. Decisiones pendientes**

Todavía **no deben resolverse**:

### **TEC-01 — Lenguaje**

Pendiente.

### **TEC-02 — Framework web**

Pendiente.

### **TEC-03 — Motor de visualización del grafo**

Pendiente.

### **TEC-04 — Motor de base de datos concreto**

Pendiente.

### **TEC-05 — Formato definitivo de metadata**

Pendiente.

### **TEC-06 — Estrategia exacta de normalización**

Pendiente.

Estas decisiones deben tomarse posteriormente, una vez que el contrato conceptual esté cerrado.

---

# **79\. Punto especialmente importante: no sobrecargar el Grafo**

El diseño establece una frontera muy importante.

El `Grafo` **no será un "objeto que hace todo"**.

No debería hacer:

Grafo  
 ├── SQL  
 ├── HTTP  
 ├── HTML  
 ├── autenticación  
 ├── APIs externas  
 ├── persistencia  
 └── BFS

Debe hacer esencialmente:

Grafo  
 ├── administrar vértices  
 ├── administrar aristas  
 ├── consultar conexiones  
 ├── BFS  
 ├── DFS  
 └── búsqueda de caminos

Eso hace que el núcleo sea pequeño y altamente testeable.

---

# **80\. Contrato conceptual del Motor del Grafo**

El futuro componente debe poder responder, independientemente de la tecnología:

¿Existe esta entidad?

¿Puedo agregar esta entidad?

¿Puedo eliminar esta entidad?

¿Existe esta relación?

¿Puedo agregar esta relación?

¿Puedo eliminar esta relación?

¿Qué vecinos tiene esta entidad?

¿Qué entidades puedo alcanzar desde aquí mediante BFS?

¿Qué entidades puedo alcanzar mediante DFS?

¿Existe un camino entre A y B?

¿Cuál es un camino mínimo entre A y B?

Y no debería necesitar saber:

¿Estoy funcionando en una página web?  
¿Uso PostgreSQL?  
¿Estoy recibiendo HTTP?  
¿Hay una API externa?  
¿La interfaz es React?

Ese aislamiento es uno de los puntos técnicos más importantes del diseño.

---

# **81\. Conclusión del diseño v1.0**

El diseño técnico resultante mantiene la idea central de la Arquitectura v1.1 pero ahora define con mayor precisión **qué significa cada elemento y cómo se relacionan**.

El núcleo queda reducido a:

ENTIDAD  
   \+  
RELACIÓN  
   \+  
EVIDENCIA  
   ↓  
GRAFO DIRIGIDO  
   ↓  
LISTA DE ADYACENCIA  
   ↓  
┌────────┬────────┬──────────────┐  
│  BFS   │  DFS   │ BUSCAR CAMINO│  
└────────┴────────┴──────────────┘

Y la persistencia queda separada:

                ┌───────────────┐  
                 │ Base de datos │  
                 └───────┬───────┘  
                         │  
                         ▼  
                    ┌─────────┐  
                    │  Grafo  │  
                    └─────────┘

La decisión más importante que se agregó en esta etapa es que **Evidencia será un concepto único, asociado 0..N a una relación**, en lugar de crear por separado `Referencia` y `Evidencia`. Esto conserva la trazabilidad buscada sin introducir una abstracción que todavía no necesitamos.

Con esto ya tenemos un contrato suficientemente definido para que la siguiente etapa pueda abordar **la tecnología y el diseño de backend/frontend sin volver a discutir qué debe hacer el motor del grafo**.

El siguiente nivel natural, todavía sin programar, sería transformar este documento en tres artefactos técnicos: **diagrama de clases conceptual, diagrama entidad-relación y especificación formal de los casos de uso del MVP**.

