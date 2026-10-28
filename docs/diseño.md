# **Diseño de Clases, DER y Casos de Uso del MVP — v1.0**

> **Diseño conceptual histórico.** El esquema y los casos implementados se
> describen en la [guía del MVP](mvp-academico.md), que prevalece para conocer
> el estado actual.

**Proyecto:** Mini-Maltego académico  
**Materia:** Algoritmos y Estructuras de Datos 3  
**Estado:** Diseño conceptual previo a selección de tecnología  
**Dependencias:** Arquitectura v1.1 \+ Diseño de Dominio y Motor del Grafo v1.0

---

# **ARTEFACTO 1**

# **Diagrama de Clases Conceptual — v1.0**

## **1.1 Criterio**

No todo concepto del sistema se convierte automáticamente en una clase.

Se distinguen cuatro categorías:

| Categoría | Elementos |
| ----- | ----- |
| Dominio | Entidad, Relación, Evidencia |
| Catálogos | TipoEntidad, TipoRelacion |
| Estructura de datos | Grafo, ListaAdyacencia |
| Aplicación | Servicios/casos de uso, aún sin clases concretas |

La decisión principal es que **TipoEntidad y TipoRelacion no necesitan objetos de negocio complejos**. Son catálogos de valores controlados.

---

## **1.2 Clases del dominio**

### **Entidad**

**Responsabilidad:** representar un vértice del dominio.

**Atributos conceptuales:**

* id  
* tipo  
* valor  
* descripción  
* metadata

**Operaciones principales:**

* validar datos propios  
* obtener identidad  
* obtener tipo/valor

No conoce al Grafo ni a la base de datos.

---

### **Relación**

**Responsabilidad:** representar una conexión dirigida entre dos entidades.

**Atributos:**

* id  
* origen  
* destino  
* tipo  
* descripción  
* fecha

**Operaciones principales:**

* validar estructura  
* obtener origen  
* obtener destino  
* obtener tipo

Una relación puede contener cero o muchas evidencias.

---

### **Evidencia**

**Responsabilidad:** documentar la procedencia o respaldo de una relación.

**Atributos:**

* id  
* fuente  
* descripción  
* fecha

No determina si una relación es válida.

Una evidencia pertenece a una relación.

---

## **1.3 TipoEntidad**

No se considera una clase de negocio compleja.

Conceptualmente representa un catálogo:

PERSONA  
ORGANIZACION  
EMAIL  
USUARIO  
DOMINIO  
SITIO\_WEB  
IP

En el modelo de objetos puede tratarse como un valor controlado.

En persistencia se representa mediante `TIPO_ENTIDAD`.

---

## **1.4 TipoRelacion**

Mismo criterio.

Valores iniciales:

POSEE  
UTILIZA  
TRABAJA\_EN  
ADMINISTRA  
PERTENECE\_A  
APUNTA\_A

No necesita comportamiento propio.

---

# **1.5 Grafo**

`Grafo` sí constituye una clase conceptual importante.

No pertenece al dominio como "objeto de información", sino al **motor de estructuras de datos**.

### **Responsabilidad**

Administrar la representación del grafo en memoria y proporcionar operaciones sobre él.

### **Atributos internos conceptuales**

entidades  
listaAdyacencia

Además puede mantener estructuras auxiliares como:

indiceEntidades

### **Operaciones principales**

agregarEntidad()  
eliminarEntidad()  
buscarEntidad()  
existeEntidad()

agregarRelacion()  
eliminarRelacion()  
buscarRelacion()  
existeRelacion()

obtenerVecinos()

bfs()  
dfs()  
buscarCamino()

No conoce:

* SQL;  
* HTML;  
* HTTP;  
* APIs externas;  
* interfaz gráfica.

---

# **1.6 ListaAdyacencia**

Aquí se toma una decisión importante:

> `ListaAdyacencia` se considera una **estructura de datos interna del Grafo**, no una entidad del dominio y no una clase de negocio independiente.

Conceptualmente:

Grafo  
 │  
 └── ListaAdyacencia  
       │  
       ├── Entidad A → \[Relación 1, Relación 2\]  
       ├── Entidad B → \[Relación 3\]  
       └── Entidad C → \[\]

Puede materializarse posteriormente como una clase técnica si la tecnología elegida lo requiere, pero conceptualmente no tiene sentido que sea un objeto independiente del dominio.

Su existencia responde exclusivamente a una decisión de representación del grafo.

---

# **1.7 Relaciones entre clases**

┌─────────────────────┐  
│       Entidad       │  
├─────────────────────┤  
│ id                  │  
│ tipo                │  
│ valor               │  
│ descripcion         │  
│ metadata            │  
└─────────┬───────────┘  
          │  
          │ participa como  
          │ origen/destino  
          │  
          ▼  
┌─────────────────────┐  
│      Relacion       │  
├─────────────────────┤  
│ id                  │  
│ origen              │  
│ destino             │  
│ tipo                │  
│ descripcion         │  
│ fecha               │  
└─────────┬───────────┘  
          │  
          │ 0..N  
          ▼  
┌─────────────────────┐  
│      Evidencia      │  
├─────────────────────┤  
│ id                  │  
│ fuente              │  
│ descripcion         │  
│ fecha               │  
└─────────────────────┘

┌─────────────────────┐  
│       Grafo         │  
├─────────────────────┤  
│ entidades           │  
│ listaAdyacencia     │  
│ indiceEntidades     │  
├─────────────────────┤  
│ agregarEntidad()    │  
│ eliminarEntidad()   │  
│ buscarEntidad()     │  
│ agregarRelacion()   │  
│ eliminarRelacion()  │  
│ obtenerVecinos()    │  
│ bfs()               │  
│ dfs()               │  
│ buscarCamino()      │  
└──────────┬──────────┘  
           │  
           │ contiene  
           ▼  
┌─────────────────────┐  
│  ListaAdyacencia    │  
│ estructura interna  │  
└─────────────────────┘  
---

# **1.8 Cardinalidades conceptuales**

Una `Relacion` tiene:

1 Entidad origen  
1 Entidad destino

Una `Entidad` puede participar en:

0..N relaciones salientes  
0..N relaciones entrantes

Una `Relacion` puede tener:

0..N Evidencias

Una `Evidencia` pertenece a:

1 Relacion

El `Grafo` administra:

0..N Entidades  
0..N Relaciones  
---

# **1.9 Diagrama conceptual simplificado**

                   ┌───────────────┐  
                    │    Entidad    │  
                    └───────┬───────┘  
                            │  
                  origen / destino  
                            │  
                            ▼  
                    ┌───────────────┐  
                    │   Relación    │  
                    └───────┬───────┘  
                            │  
                          0..N  
                            │  
                            ▼  
                    ┌───────────────┐  
                    │   Evidencia   │  
                    └───────────────┘

                    ┌───────────────┐  
                    │     Grafo     │  
                    └───────┬───────┘  
                            │  
                            ▼  
                    ┌───────────────┐  
                    │ ListaAdjacencia│  
                    └───────────────┘  
---

# **1.10 Decisión sobre servicios**

No se agrega todavía una clase concreta como:

GrafoService  
EntidadService  
RelacionService

porque eso dependerá de cómo posteriormente se organice la aplicación.

Conceptualmente sí existe una **capa de aplicación/servicios**, pero no es necesario inventar clases técnicas antes de seleccionar tecnología.

La responsabilidad queda definida:

Caso de uso  
    ↓  
Servicio de aplicación  
    ↓  
Dominio / Grafo  
    ↓  
Persistencia  
---

# **ARTEFACTO 2**

# **Diagrama Entidad-Relación — v1.0**

# **2.1 Modelo propuesto**

El modelo mínimo de persistencia queda compuesto por cinco tablas:

TIPO\_ENTIDAD  
     │  
     │ 1:N  
     ▼  
  ENTIDAD  
     │  
     │  
     ├──────────────────────┐  
     │                      │  
     │ origen               │ destino  
     ▼                      ▼  
          RELACION  
              │  
              │ N:1  
              ▼  
       TIPO\_RELACION

              │  
              │ 1:N  
              ▼  
          EVIDENCIA  
---

# **2.2 TIPO\_ENTIDAD**

### **Propósito**

Catálogo de tipos válidos de entidades.

### **Atributos**

TIPO\_ENTIDAD  
\-------------------------  
id PK  
codigo UNIQUE  
nombre  
descripcion

Ejemplo:

1 | PERSONA  
2 | ORGANIZACION  
3 | EMAIL  
4 | USUARIO  
5 | DOMINIO  
6 | SITIO\_WEB  
7 | IP  
---

# **2.3 ENTIDAD**

### **Propósito**

Persistir los vértices del grafo.

### **Atributos**

ENTIDAD  
\-------------------------  
id PK  
tipo\_entidad\_id FK  
valor  
descripcion  
metadata

### **Restricción principal**

UNIQUE(tipo\_entidad\_id, valor\_normalizado)

La existencia exacta de `valor_normalizado` queda como decisión técnica pendiente, porque dependerá de cómo se resuelva la normalización.

---

# **2.4 TIPO\_RELACION**

### **Propósito**

Catálogo de tipos de relaciones.

TIPO\_RELACION  
\-------------------------  
id PK  
codigo UNIQUE  
nombre  
descripcion

Valores iniciales:

POSEE  
UTILIZA  
TRABAJA\_EN  
ADMINISTRA  
PERTENECE\_A  
APUNTA\_A  
---

# **2.5 RELACION**

Esta es la tabla central para representar las aristas.

RELACION  
\-------------------------  
id PK  
origen\_id FK → ENTIDAD.id  
destino\_id FK → ENTIDAD.id  
tipo\_relacion\_id FK → TIPO\_RELACION.id  
descripcion  
fecha

### **Restricción**

UNIQUE(  
    origen\_id,  
    destino\_id,  
    tipo\_relacion\_id  
)  
---

# **2.6 Representación de dirección**

Una relación:

ENTIDAD 10  
   │  
   │ TRABAJA\_EN  
   ▼  
ENTIDAD 25

se almacena como:

origen\_id  \= 10  
destino\_id \= 25  
tipo       \= TRABAJA\_EN

No se genera automáticamente:

25 → 10

La dirección forma parte del significado de la relación.

---

# **2.7 EVIDENCIA**

EVIDENCIA  
\-------------------------  
id PK  
relacion\_id FK → RELACION.id  
fuente  
descripcion  
fecha

Cardinalidad:

RELACION 1 ───── 0..N EVIDENCIA  
---

# **2.8 DER completo**

┌──────────────────────┐  
│    TIPO\_ENTIDAD      │  
├──────────────────────┤  
│ PK id                │  
│ UK codigo            │  
│ nombre               │  
│ descripcion          │  
└──────────┬───────────┘  
           │ 1  
           │  
           │ N  
┌──────────▼───────────┐  
│       ENTIDAD        │  
├──────────────────────┤  
│ PK id                │  
│ FK tipo\_entidad\_id   │  
│ valor                │  
│ descripcion          │  
│ metadata             │  
└──────┬─────────┬─────┘  
       │         │  
     origen    destino  
       │         │  
       └────┬────┘  
            │  
            │  
┌───────────▼────────────┐  
│       RELACION         │  
├────────────────────────┤  
│ PK id                  │  
│ FK origen\_id           │  
│ FK destino\_id          │  
│ FK tipo\_relacion\_id    │  
│ descripcion            │  
│ fecha                  │  
└──────────┬─────────────┘  
           │  
           │ N  
           │  
           │ 1  
┌──────────▼─────────────┐  
│      EVIDENCIA         │  
├────────────────────────┤  
│ PK id                  │  
│ FK relacion\_id         │  
│ fuente                 │  
│ descripcion            │  
│ fecha                  │  
└────────────────────────┘

┌──────────────────────┐  
│   TIPO\_RELACION      │  
├──────────────────────┤  
│ PK id                │  
│ UK codigo            │  
│ nombre               │  
│ descripcion          │  
└──────────┬───────────┘  
           │  
           │ 1:N  
           ▼  
       RELACION  
---

# **2.9 ¿Son necesarias las cinco tablas?**

Sí, con una salvedad.

### **TIPO\_ENTIDAD**

Es útil para controlar los valores permitidos y mantener integridad.

### **ENTIDAD**

Necesaria.

### **TIPO\_RELACION**

Útil por la misma razón.

### **RELACION**

Necesaria.

### **EVIDENCIA**

Necesaria únicamente porque se decidió que una relación puede tener múltiples evidencias.

Por lo tanto, no se considera una tabla ornamental.

---

# **2.10 ¿Podrían eliminarse los catálogos?**

Sí, técnicamente podrían reemplazarse por valores controlados.

Por ejemplo:

ENTIDAD.tipo \= "PERSONA"

Pero la solución con tablas proporciona:

* integridad referencial;  
* catálogo central;  
* menor riesgo de valores inválidos;  
* extensibilidad.

Para un proyecto académico, además, hace explícita la relación entre el dominio y la persistencia.

### **Decisión**

Se mantienen.

---

# **2.11 Restricciones principales**

## **ENTIDAD**

id → único  
tipo\_entidad\_id → obligatorio  
valor → obligatorio  
tipo \+ valor normalizado → único

## **RELACION**

origen\_id → obligatorio  
destino\_id → obligatorio  
tipo\_relacion\_id → obligatorio  
origen \+ destino \+ tipo → único

## **EVIDENCIA**

relacion\_id → obligatorio

Una evidencia no puede existir sin una relación.

---

# **2.12 Eliminación**

Si se elimina una entidad:

Entidad  
   ↓  
Relaciones entrantes/salientes  
   ↓  
Evidencias asociadas

deben desaparecer las dependencias correspondientes.

La implementación concreta podrá resolverlo mediante reglas de integridad referencial.

---

# **ARTEFACTO 3**

# **Casos de Uso del MVP — v1.0**

# **3.1 Decisión sobre el alcance**

Partiendo de la lista inicial, se eliminan dos casos de uso como acciones independientes:

### **"Guardar información"**

No será un caso de uso del usuario.

La persistencia será parte de las operaciones de modificación.

Por ejemplo:

Crear entidad  
    ↓  
Validar  
    ↓  
Persistir  
    ↓  
Actualizar Grafo

Esto evita tener:

Crear entidad  
Guardar entidad

como dos acciones que podrían quedar inconsistentes.

### **"Cargar información"**

Tampoco será una acción central del usuario.

La carga inicial de la información persistida forma parte de la inicialización del contexto de trabajo.

Por lo tanto, se trata como comportamiento interno del sistema.

---

# **3.2 Casos de uso finales**

El MVP queda con:

| ID | Caso de uso |
| ----- | ----- |
| CU-01 | Crear entidad |
| CU-02 | Consultar entidad |
| CU-03 | Eliminar entidad |
| CU-04 | Crear relación |
| CU-05 | Consultar relaciones |
| CU-06 | Eliminar relación |
| CU-07 | Visualizar grafo |
| CU-08 | Ejecutar BFS |
| CU-09 | Ejecutar DFS |
| CU-10 | Buscar camino |

Son diez casos.

No se agregan:

* administración avanzada;  
* autenticación compleja;  
* importación masiva;  
* scraping;  
* análisis externo;  
* edición avanzada de evidencias;  
* dashboards;  
* reportes complejos.

---

# **CU-01 — Crear entidad**

### **Objetivo**

Incorporar una nueva entidad al sistema.

### **Actor**

Usuario.

### **Precondiciones**

* sistema disponible;  
* tipo de entidad válido.

### **Flujo principal**

1. El usuario selecciona crear entidad.  
2. El sistema solicita tipo y valor.  
3. El usuario proporciona los datos.  
4. El sistema valida los datos.  
5. El sistema verifica que no exista una entidad equivalente.  
6. Se crea la entidad.  
7. Se persiste.  
8. Se incorpora al grafo en memoria.  
9. El sistema confirma la operación.

### **Alternativas**

**A1 — Datos opcionales**

El usuario puede agregar descripción y metadata.

**A2 — Entidad equivalente ya existente**

El sistema informa que la entidad ya existe y evita duplicarla.

### **Excepciones**

* tipo inválido;  
* valor vacío;  
* error de persistencia;  
* inconsistencia al actualizar el grafo.

### **Postcondición**

La entidad existe en:

BD  
\+  
Grafo

### **Componentes**

Usuario  
 ↓  
Caso de uso  
 ↓  
Servicio  
 ├── Dominio Entidad  
 ├── Persistencia  
 └── Grafo  
       ↓  
   ListaAdyacencia

### **AED3**

* Grafo  
* Lista de adyacencia  
* OOP

---

# **CU-02 — Consultar entidad**

### **Objetivo**

Obtener información de una entidad.

### **Actor**

Usuario.

### **Precondiciones**

Sistema disponible.

### **Flujo principal**

1. El usuario introduce un criterio de búsqueda.  
2. El sistema busca la entidad.  
3. El sistema muestra sus datos.  
4. El sistema puede mostrar sus relaciones asociadas.

### **Alternativas**

**A1**

La entidad existe pero no posee relaciones.

Se muestra como entidad aislada.

### **Excepciones**

Entidad inexistente.

### **Postcondición**

No se modifica el sistema.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ├── Persistencia / consulta  
 └── Grafo

### **AED3**

* búsqueda sobre estructura;  
* grafo/lista de adyacencia cuando se consultan conexiones.

---

# **CU-03 — Eliminar entidad**

### **Objetivo**

Eliminar una entidad y sus relaciones asociadas.

### **Actor**

Usuario.

### **Precondiciones**

Entidad existente.

### **Flujo principal**

1. El usuario selecciona una entidad.  
2. El sistema muestra información básica.  
3. El usuario confirma la eliminación.  
4. El sistema identifica relaciones entrantes y salientes.  
5. El sistema elimina la entidad y sus relaciones de persistencia.  
6. El sistema elimina la entidad y sus relaciones del grafo.  
7. El sistema confirma la operación.

### **Excepciones**

* entidad inexistente;  
* error de persistencia;  
* inconsistencia durante actualización.

### **Postcondición**

La entidad no existe en BD ni Grafo.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ├── Entidad  
 ├── Persistencia  
 └── Grafo

### **AED3**

* grafo;  
* lista de adyacencia;  
* complejidad de eliminación.

---

# **CU-04 — Crear relación**

### **Objetivo**

Crear una conexión dirigida entre dos entidades.

### **Actor**

Usuario.

### **Precondiciones**

* origen existente;  
* destino existente;  
* tipo de relación válido.

### **Flujo principal**

1. El usuario selecciona origen.  
2. Selecciona destino.  
3. Selecciona tipo de relación.  
4. Opcionalmente incorpora descripción, fecha y evidencia.  
5. El sistema valida los datos.  
6. Verifica que no exista la misma relación.  
7. Persiste la relación.  
8. Agrega la relación al grafo.  
9. Confirma la operación.

### **Alternativas**

**A1 — Relación diferente entre mismos extremos**

Se permite si cambia el tipo.

Ejemplo:

A ──POSEE──\> B  
A ──UTILIZA──\> B

### **Excepciones**

* origen inexistente;  
* destino inexistente;  
* tipo inválido;  
* relación duplicada;  
* error de persistencia.

### **Postcondición**

La relación existe en BD y Grafo.

### **AED3**

* grafo dirigido;  
* lista de adyacencia;  
* relaciones tipadas.

---

# **CU-05 — Consultar relaciones**

### **Objetivo**

Conocer las conexiones de una entidad.

### **Actor**

Usuario.

### **Precondiciones**

Entidad existente.

### **Flujo principal**

1. El usuario selecciona una entidad.  
2. El sistema obtiene sus relaciones.  
3. El sistema muestra:  
   * destino;  
   * tipo;  
   * descripción;  
   * evidencia disponible.  
4. El usuario puede seleccionar una relación para consultar mayor detalle.

### **Alternativas**

**A1 — Sin relaciones**

Se informa que la entidad está aislada.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ↓  
Grafo  
 ↓  
ListaAdyacencia

Para información persistente detallada pueden consultarse datos de BD.

### **AED3**

* lista de adyacencia;  
* recorrido de vecinos;  
* complejidad O(grado).

---

# **CU-06 — Eliminar relación**

### **Objetivo**

Eliminar una conexión existente sin eliminar sus entidades.

### **Actor**

Usuario.

### **Precondiciones**

Relación existente.

### **Flujo principal**

1. El usuario selecciona la relación.  
2. El sistema muestra sus datos.  
3. El usuario confirma.  
4. Se elimina la relación de persistencia.  
5. Se elimina del grafo.  
6. Se eliminan las evidencias asociadas.  
7. Se confirma la operación.

### **Excepciones**

* relación inexistente;  
* error de persistencia.

### **Postcondición**

Las entidades permanecen.

La relación deja de existir.

### **AED3**

* lista de adyacencia;  
* grafo dirigido.

---

# **CU-07 — Visualizar grafo**

### **Objetivo**

Representar visualmente las entidades y relaciones existentes.

### **Actor**

Usuario.

### **Precondiciones**

* sistema disponible;  
* grafo cargado.

### **Flujo principal**

1. El usuario solicita visualizar el grafo.  
2. El sistema obtiene entidades y relaciones.  
3. La interfaz representa los vértices.  
4. La interfaz representa las aristas dirigidas.  
5. Se muestran los tipos de relación.  
6. El usuario puede seleccionar una entidad.

### **Alternativas**

**A1 — Grafo vacío**

Se muestra un estado vacío.

**A2 — Grafo grande**

La interfaz puede limitar inicialmente la cantidad de elementos visualizados o permitir seleccionar una entidad de referencia.

### **Excepciones**

Error de carga del grafo.

### **Postcondición**

No modifica el dominio.

### **Componentes**

Usuario  
 ↓  
Interfaz  
 ↓  
Servicio de consulta  
 ↓  
Grafo  
 ↓  
ListaAdyacencia

### **AED3**

* grafo;  
* lista de adyacencia.

---

# **CU-08 — Ejecutar BFS**

### **Objetivo**

Explorar las entidades alcanzables desde una entidad inicial utilizando BFS.

### **Actor**

Usuario.

### **Precondiciones**

La entidad inicial existe.

### **Flujo principal**

1. El usuario selecciona una entidad inicial.  
2. Solicita BFS.  
3. El sistema valida el nodo inicial.  
4. Inicializa visitados y cola.  
5. Ejecuta BFS.  
6. Obtiene:  
   * orden de recorrido;  
   * niveles;  
   * predecesores.  
7. Muestra el resultado.

### **Alternativas**

**A1 — Nodo aislado**

Resultado:

\[Entidad inicial\]

**A2 — Ciclo**

El conjunto de visitados evita recorrer indefinidamente.

### **Excepciones**

Entidad inicial inexistente.

### **Postcondición**

El grafo no se modifica.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ↓  
Grafo  
 ├── ListaAdyacencia  
 ├── Visitados  
 ├── Cola  
 └── Predecesores

### **AED3**

* Grafo;  
* lista de adyacencia;  
* cola;  
* complejidad O(V+E).

---

# **CU-09 — Ejecutar DFS**

### **Objetivo**

Recorrer el grafo desde una entidad inicial mediante búsqueda en profundidad.

### **Actor**

Usuario.

### **Precondiciones**

Entidad inicial existente.

### **Flujo principal**

1. Usuario selecciona entidad.  
2. Solicita DFS.  
3. Sistema crea conjunto de visitados.  
4. Comienza recorrido recursivo.  
5. Marca entidades visitadas.  
6. Continúa por relaciones salientes.  
7. Finaliza cuando no quedan vértices nuevos.  
8. Muestra el orden de recorrido.

### **Alternativas**

**A1 — Ciclos**

Visitados evita recursión infinita.

**A2 — Nodo aislado**

Se devuelve solamente el nodo inicial.

### **Excepciones**

Entidad inexistente.

### **Postcondición**

No se modifica el grafo.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ↓  
Grafo  
 ↓  
ListaAdyacencia  
 ↓  
DFS recursivo

### **AED3**

* Grafo;  
* lista de adyacencia;  
* recursividad;  
* complejidad O(V+E).

---

# **CU-10 — Buscar camino**

### **Objetivo**

Encontrar un camino entre dos entidades.

### **Actor**

Usuario.

### **Precondiciones**

* origen existente;  
* destino existente.

### **Flujo principal**

1. Usuario selecciona origen.  
2. Usuario selecciona destino.  
3. Sistema valida ambos.  
4. Ejecuta BFS.  
5. Registra predecesores.  
6. Encuentra el destino.  
7. Reconstruye el camino.  
8. Devuelve entidades y relaciones correspondientes.  
9. Muestra el camino.

### **Alternativas**

**A1 — Origen \= destino**

Se devuelve el camino trivial:

\[A\]

sin relaciones.

**A2 — Existen múltiples caminos**

Se devuelve uno de mínima cantidad de aristas.

### **Excepciones**

No existe camino.

Esto no constituye un error del sistema, sino un resultado válido:

No existe camino entre A y B.

### **Postcondición**

No se modifica el grafo.

### **Componentes**

Usuario  
 ↓  
Servicio  
 ↓  
Grafo  
 ├── ListaAdyacencia  
 ├── Cola  
 ├── Visitados  
 └── Predecesores

### **AED3**

* grafo;  
* BFS;  
* cola;  
* predecesores;  
* complejidad O(V+E).

---

# **3.3 Comportamientos internos que NO son casos de uso**

Para evitar sobre-documentación:

### **Carga inicial**

BD  
 ↓  
Entidades  
 ↓  
Relaciones  
 ↓  
Grafo

Es un proceso interno de inicialización.

### **Persistencia**

Cada operación que modifica el dominio debe coordinar:

Persistencia  
\+  
Grafo

No se expone como "Guardar" separado.

### **Reconstrucción del grafo**

Es una responsabilidad interna de la aplicación.

---

# **3.4 Relación entre casos de uso**

                ┌────────────────────┐  
                 │      Usuario       │  
                 └─────────┬──────────┘  
                           │  
             ┌─────────────┼──────────────┐  
             │             │              │  
             ▼             ▼              ▼  
       Crear entidad   Crear relación   Consultar  
                                          │  
                                  ┌───────┴───────┐  
                                  ▼               ▼  
                             Entidad         Relaciones

             ┌──────────────────────────────┐  
             │       Análisis de Grafo      │  
             ├──────────────────────────────┤  
             │ Visualizar grafo             │  
             │ Ejecutar BFS                 │  
             │ Ejecutar DFS                 │  
             │ Buscar camino                │  
             └──────────────────────────────┘  
---

# **3.5 Casos de uso y AED3**

| Caso de uso | Conceptos AED3 demostrados |
| ----- | ----- |
| CU-01 Crear entidad | Grafo, lista de adyacencia |
| CU-02 Consultar entidad | Búsqueda, estructura de datos |
| CU-03 Eliminar entidad | Grafo, lista de adyacencia |
| CU-04 Crear relación | Grafo dirigido, lista de adyacencia |
| CU-05 Consultar relaciones | Lista de adyacencia |
| CU-06 Eliminar relación | Grafo, lista de adyacencia |
| CU-07 Visualizar grafo | Grafo |
| CU-08 Ejecutar BFS | Grafo, cola, visitados, complejidad |
| CU-09 Ejecutar DFS | Grafo, recursividad, complejidad |
| CU-10 Buscar camino | Grafo, BFS, cola, predecesores |

No se fuerza el uso de estructuras que no son necesarias.

---

# **3.6 Matriz de trazabilidad final**

| Requisito | Caso de uso | Componente | Estructura | Algoritmo | Prueba futura |
| ----- | ----- | ----- | ----- | ----- | ----- |
| RF-01 Registrar entidad | CU-01 | Servicio \+ Grafo \+ Persistencia | Hash \+ Grafo | — | Crear entidad válida |
| RF-02 Evitar entidades duplicadas | CU-01 | Servicio | Hash / índice | Búsqueda | Rechazar duplicado |
| RF-03 Consultar entidad | CU-02 | Servicio \+ Grafo | Hash | — | Buscar existente/inexistente |
| RF-04 Eliminar entidad | CU-03 | Servicio \+ Grafo \+ BD | Lista de adyacencia | — | Eliminar entidad con relaciones |
| RF-05 Registrar relación | CU-04 | Servicio \+ Grafo \+ BD | Lista de adyacencia | — | Crear relación válida |
| RF-06 Evitar relación duplicada | CU-04 | Grafo \+ Servicio | Lista de adyacencia | Búsqueda local | Rechazar duplicado |
| RF-07 Consultar conexiones | CU-05 | Grafo | Lista de adyacencia | Recorrido de vecinos | Consultar vecinos |
| RF-08 Eliminar relación | CU-06 | Servicio \+ Grafo \+ BD | Lista de adyacencia | — | Eliminar relación |
| RF-09 Visualizar estructura | CU-07 | Interfaz \+ Grafo | Lista de adyacencia | — | Mostrar nodos/aristas |
| RF-10 Recorrer en amplitud | CU-08 | Grafo | Cola \+ visitados | BFS | BFS con ciclo |
| RF-11 Recorrer en profundidad | CU-09 | Grafo | Visitados \+ pila de llamadas | DFS recursivo | DFS con ciclo |
| RF-12 Encontrar camino | CU-10 | Grafo | Cola \+ predecesores | BFS | Camino existente/inexistente |
| RF-13 Persistir información | CU-01/03/04/06 | Persistencia \+ Servicio | BD relacional | — | BD y grafo consistentes |
| RF-14 Reconstruir grafo | Inicialización | Persistencia \+ Grafo | Lista de adyacencia | Construcción | BD → grafo correcto |

---

# **REVISIÓN DE CONSISTENCIA**

## **4.1 Arquitectura v1.1 ↔ Diseño v1.0**

### **Resultado**

**Consistente.**

Se mantienen:

* aplicación web;  
* monolito modular;  
* BD relacional;  
* grafo dirigido;  
* relaciones tipadas;  
* evidencias;  
* lista de adyacencia;  
* BFS;  
* DFS;  
* búsqueda de caminos;  
* APIs externas opcionales;  
* ausencia de Graph Database;  
* ausencia de microservicios;  
* ausencia de scraping masivo;  
* ausencia de escaneo intrusivo.

---

# **4.2 Diseño de dominio ↔ Diagrama de clases**

### **Resultado**

**Consistente.**

Se mantiene:

Entidad  
Relación  
Evidencia  
Grafo  
ListaAdyacencia

y se evita convertir artificialmente:

TipoEntidad  
TipoRelacion

en clases complejas.

La decisión de `ListaAdyacencia` como estructura interna también coincide con el diseño anterior.

---

# **4.3 Clases ↔ Base de datos**

### **Matriz**

| Clase/concepto | Tabla / estructura persistente | Motivo |
| ----- | ----- | ----- |
| Entidad | ENTIDAD | Persistencia de vértices |
| TipoEntidad | TIPO\_ENTIDAD | Catálogo |
| Relación | RELACION | Persistencia de aristas |
| TipoRelacion | TIPO\_RELACION | Catálogo |
| Evidencia | EVIDENCIA | Persistencia de respaldo |
| Grafo | **No tiene tabla propia** | Existe en memoria |
| ListaAdyacencia | **No tiene tabla propia** | Estructura de datos |
| Cola BFS | **No persiste** | Estructura temporal |
| Visitados | **No persiste** | Estructura temporal |
| Predecesores | **No persiste** | Resultado temporal del algoritmo |

Este punto es fundamental:

> **La base de datos almacena el estado persistente del dominio; no almacena la estructura de datos utilizada para ejecutar los algoritmos.**

---

# **4.4 BD ↔ Grafo**

La relación queda:

                PERSISTENCIA  
                      │  
                      ▼  
             ┌─────────────────┐  
             │       BD        │  
             │                 │  
             │ Entidades       │  
             │ Relaciones      │  
             │ Evidencias      │  
             └────────┬────────┘  
                      │  
                 reconstruir  
                      │  
                      ▼  
             ┌─────────────────┐  
             │     GRAFO       │  
             │                 │  
             │ ListaAdjacencia │  
             │ Índice entidades│  
             └────────┬────────┘  
                      │  
             ┌────────┼─────────┐  
             ▼        ▼         ▼  
            BFS      DFS      Camino

No existe una tabla:

GRAFO

porque eso sería confundir persistencia con estructura de datos.

---

# **4.5 Operaciones del Grafo ↔ Casos de uso**

| Grafo | Caso de uso |
| ----- | ----- |
| agregarEntidad() | CU-01 |
| eliminarEntidad() | CU-03 |
| buscarEntidad() | CU-02 |
| existeEntidad() | CU-01, CU-02, CU-04 |
| agregarRelacion() | CU-04 |
| eliminarRelacion() | CU-06 |
| buscarRelacion() | CU-05, CU-06 |
| existeRelacion() | CU-04 |
| obtenerVecinos() | CU-05 |
| bfs() | CU-08, CU-10 |
| dfs() | CU-09 |
| buscarCamino() | CU-10 |

La interfaz definida en el documento anterior queda, por tanto, cubierta por los casos de uso.

---

# **4.6 Tipos de entidades**

Se mantienen exactamente:

PERSONA  
ORGANIZACION  
EMAIL  
USUARIO  
DOMINIO  
SITIO\_WEB  
IP

No se agregaron tipos nuevos.

---

# **4.7 Tipos de relaciones**

Se mantienen exactamente:

POSEE  
UTILIZA  
TRABAJA\_EN  
ADMINISTRA  
PERTENECE\_A  
APUNTA\_A

No se agregaron tipos nuevos.

---

# **4.8 Contradicción detectada**

Existe una pequeña tensión conceptual entre dos decisiones anteriores:

### **Documento anterior**

Se planteó que una operación podría:

guardar en BD  
\+  
actualizar Grafo

### **Nuevo diseño**

Para mantener consistencia, el orden exacto de esas dos operaciones no puede considerarse todavía una decisión de implementación.

La cuestión depende de cómo posteriormente se manejen transacciones y errores.

### **Decisión**

No se modifica el modelo conceptual.

Se establece únicamente el requisito:

> Una operación de modificación debe finalizar dejando BD y Grafo en un estado consistente.

El mecanismo técnico para garantizarlo queda pendiente de la selección del stack.

**Estado: Pendiente.**

---

# **4.9 Otra decisión que permanece pendiente**

La normalización de:

tipo \+ valor

sigue necesitando una definición técnica concreta.

Por ejemplo, queda pendiente determinar exactamente cómo se normalizarán:

* emails;  
* dominios;  
* URLs;  
* IP;  
* nombres;  
* usuarios.

No es necesario resolverlo antes de seleccionar tecnología.

**Estado: Pendiente.**

---

# **4.10 Revisión de simplicidad**

Se eliminaron deliberadamente:

* clase Referencia separada;  
* clase TipoEntidad compleja;  
* clase TipoRelacion compleja;  
* tabla GRAFO;  
* tabla LISTA\_ADYACENCIA;  
* casos de uso independientes de guardar;  
* casos de uso independientes de cargar;  
* servicios artificiales;  
* estructuras de datos no utilizadas;  
* algoritmos adicionales;  
* entidades de dominio no justificadas.

El diseño queda centrado en:

ENTIDAD  
RELACIÓN  
EVIDENCIA  
       ↓  
GRAFO  
       ↓  
LISTA DE ADYACENCIA  
       ↓  
BFS / DFS / CAMINOS  
       ↓  
BD RELACIONAL  
---

# **4.11 Estado final de los artefactos**

| Artefacto | Estado |
| ----- | ----- |
| Diagrama de Clases Conceptual | Definido |
| DER | Definido |
| Casos de Uso MVP | Definidos |
| Trazabilidad AED3 | Definida |
| Responsabilidades | Definidas |
| Operaciones del Grafo | Cubiertas |
| Persistencia | Definida conceptualmente |
| Algoritmos | Definidos |
| Tecnología | Pendiente |
| Lenguaje | Pendiente |
| Framework | Pendiente |
| Normalización concreta | Pendiente |
| Estrategia técnica BD/Grafo ante fallos | Pendiente |

---

# **4.12 Conclusión**

Los tres artefactos son coherentes entre sí y con la Arquitectura v1.1 y el Diseño de Dominio y Motor del Grafo v1.0.

No se detectó ningún problema que justifique revisar las decisiones arquitectónicas principales.

Quedan solamente decisiones técnicas posteriores, especialmente:

1. lenguaje;  
2. framework;  
3. motor de BD;  
4. estrategia concreta de normalización;  
5. mecanismo técnico para mantener consistente BD \+ Grafo ante errores.

Estas decisiones **no afectan el modelo conceptual actual**.

## **Estado del diseño**

**DISEÑO LISTO PARA SELECCIÓN DE STACK**

La conclusión importante es que **ya no necesitamos seguir agregando documentación conceptual antes de elegir tecnología**. El próximo paso puede ser comparar stacks candidatos contra este contrato —por ejemplo, facilidad para implementar el grafo, persistencia relacional, visualización, testing y tiempo disponible— y recién entonces seleccionar uno.
