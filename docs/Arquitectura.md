# **Proyecto Mini-Maltego — Arquitectura propuesta para AED3**

> **Documento histórico de propuesta.** Para la arquitectura efectivamente
> implementada y sus limitaciones consultá la [guía del MVP](mvp-academico.md).

## **1\. Propósito del proyecto**

El proyecto consiste en desarrollar una aplicación inspirada conceptualmente en herramientas de análisis OSINT como Maltego, pero con un alcance **académico, reducido y controlado**.

La aplicación permitirá registrar entidades y las relaciones existentes entre ellas para posteriormente analizar la información mediante un **grafo**.

El objetivo principal no es construir una herramienta profesional de inteligencia ni realizar reconocimiento masivo, sino desarrollar un sistema pequeño pero completo que permita demostrar de manera concreta los conocimientos adquiridos en **Algoritmos y Estructuras de Datos 3**.

El grafo constituye el núcleo del proyecto:

* Los **vértices** representan entidades.  
* Las **aristas** representan relaciones entre entidades.  
* Las relaciones serán **tipadas**.  
* Las entidades y relaciones podrán almacenarse de forma persistente.  
* El grafo será cargado en memoria utilizando una **lista de adyacencia**.  
* Sobre el grafo se ejecutarán algoritmos como **BFS y DFS**.

Esto permite que la estructura de datos no sea un agregado artificial, sino una parte fundamental del funcionamiento del sistema.

---

# **2\. Decisiones principales**

Hasta este punto quedaron definidas cinco decisiones principales.

| Decisión | Elección | Estado |
| ----- | ----- | ----- |
| A — Tipo de aplicación | Aplicación web | Confirmada |
| B — Persistencia | Base de datos relacional | Confirmada |
| C — Tipo de grafo | Grafo dirigido | Confirmada |
| D — Relaciones | Relaciones tipadas | Confirmada |
| E — Evidencias | Referencias/evidencias asociadas | Confirmada |

Estas decisiones no se toman solamente por preferencia tecnológica, sino intentando responder a la pregunta central del proyecto:

> **¿Por qué existe esta decisión y qué problema resuelve?**

---

# **3\. Aplicación web**

Se propone desarrollar el proyecto como una **aplicación web monolítica modular**.

No se plantea utilizar microservicios ni una arquitectura distribuida porque, para el tamaño y el tiempo disponible, agregarían complejidad sin aportar un beneficio académico proporcional.

La aplicación podría organizarse conceptualmente de la siguiente manera:

┌───────────────────────────────────────┐  
│              INTERFAZ WEB             │  
│                                       │  
│  Entidades │ Grafo │ Búsqueda │ Análisis│  
└───────────────────┬───────────────────┘  
                    │  
                    ▼  
┌───────────────────────────────────────┐  
│          CAPA DE APLICACIÓN           │  
│                                       │  
│ Servicios / Casos de uso              │  
└───────────────────┬───────────────────┘  
                    │  
                    ▼  
┌───────────────────────────────────────┐  
│            MOTOR DEL GRAFO            │  
│                                       │  
│ Entidades                             │  
│ Relaciones                            │  
│ Lista de adyacencia                   │  
│ BFS / DFS / búsqueda de caminos       │  
└───────────────────┬───────────────────┘  
                    │  
          ┌─────────┴─────────┐  
          ▼                   ▼  
┌─────────────────┐   ┌─────────────────┐  
│ BASE DE DATOS   │   │ INTEGRACIONES   │  
│ RELACIONAL      │   │ OPCIONALES      │  
└─────────────────┘   └─────────────────┘

La idea importante es que **el motor del grafo no dependa de la interfaz gráfica**.

Esto permite probar los algoritmos independientemente de la aplicación web.

---

# **4\. Base de datos relacional**

Se decidió utilizar una base de datos relacional.

Esto requiere aclarar algo importante:

> **La base de datos no reemplaza a la estructura de datos de AED3.**

La base de datos tiene una responsabilidad diferente:

### **Base de datos**

Se utiliza para:

* conservar entidades;  
* conservar relaciones;  
* conservar referencias;  
* mantener los datos cuando la aplicación se cierra;  
* permitir volver a cargar el proyecto posteriormente.

### **Estructura de datos en memoria**

La estructura de datos será:

> **Grafo representado mediante lista de adyacencia.**

Se cargará la información desde la base de datos y se construirá el grafo en memoria.

Conceptualmente:

Base de datos  
      │  
      ▼  
Carga de datos  
      │  
      ▼  
Construcción del grafo  
      │  
      ▼  
Lista de adyacencia  
      │  
      ▼  
BFS / DFS / Caminos  
      │  
      ▼  
Resultados

Esto permite defender claramente por qué existen ambas cosas.

---

# **5\. Grafo dirigido**

Se decidió utilizar un **grafo dirigido**.

Esto se debe a que las relaciones tienen significado.

Por ejemplo:

Persona ── posee ──\> Email

No necesariamente significa:

Email ── posee ──\> Persona

Otro ejemplo:

Persona ── administra ──\> Sitio Web

La relación tiene una dirección determinada.

Por eso una relación puede representarse conceptualmente como:

Entidad A ──\[tipo de relación\]──\> Entidad B

Por ejemplo:

Juan  
  │  
  │ posee  
  ▼  
juan@gmail.com

o:

Empresa  
   │  
   │ administra  
   ▼  
Sitio Web

Esto además hace que BFS y DFS tengan un comportamiento interesante, porque podemos analizar qué entidades son alcanzables **siguiendo la dirección de las relaciones**.

---

# **6\. Entidades**

Se propone utilizar una entidad genérica.

No sería necesario crear inicialmente clases completamente diferentes como:

Persona  
Email  
IP  
Dominio  
Empresa  
SitioWeb

En su lugar podemos tener:

Entidad

con atributos como:

Entidad  
\-----------------------  
id  
tipo  
nombre / valor  
descripcion  
metadata

Por ejemplo:

Entidad

id: 15  
tipo: EMAIL  
valor: juan@gmail.com  
descripcion: correo utilizado por Juan

Otro ejemplo:

Entidad

id: 20  
tipo: DOMINIO  
valor: ejemplo.com  
descripcion: sitio institucional

El campo `tipo` permite diferenciar las entidades.

---

# **7\. Tipos de entidades**

El MVP podría comenzar con un conjunto reducido:

PERSONA  
ORGANIZACION  
EMAIL  
USUARIO  
DOMINIO  
SITIO\_WEB  
IP

No es necesario implementar una enorme cantidad de tipos.

Incluso podría dejarse preparado el sistema para agregar nuevos tipos posteriormente.

Esto mantiene el proyecto pequeño y evita que el alcance se descontrole.

---

# **8\. Relaciones tipadas**

Las relaciones tendrán un tipo.

Por ejemplo:

Persona ──\[POSEE\]──\> Email  
Persona ──\[UTILIZA\]──\> Usuario  
Organización ──\[POSEE\]──\> Dominio  
Dominio ──\[APUNTA\_A\]──\> IP  
Persona ──\[TRABAJA\_EN\]──\> Organización  
SitioWeb ──\[PERTENECE\_A\]──\> Organización

La estructura conceptual podría ser:

Relacion  
\-----------------------  
id  
entidad\_origen  
entidad\_destino  
tipo  
descripcion  
fecha  
referencia  
evidencia

Esto permite que el grafo no sea simplemente:

A → B

sino:

A ──\[RELACION\]──\> B

La información resulta mucho más útil para el análisis.

---

# **9\. Referencias y evidencias**

Se decidió incorporar referencias/evidencias asociadas a las relaciones.

Esto permite registrar de dónde surge una determinada relación.

Por ejemplo:

Juan  
 │  
 │ trabaja\_en  
 ▼  
Empresa X

La relación podría tener:

Referencia:  
https\://ejemplo.com

Descripción:  
La página institucional menciona a Juan  
como integrante de la organización.

Fecha:  
20/09/2026

Esto no pretende convertir el sistema en una plataforma forense.

La finalidad es permitir que el usuario pueda responder:

> ¿Por qué existe esta relación?

Esto agrega trazabilidad y hace que el proyecto sea conceptualmente más sólido.

---

# **10\. Representación del grafo**

La representación elegida será una:

> **Lista de adyacencia.**

Conceptualmente:

Entidad A  
 ├── Relación → Entidad B  
 ├── Relación → Entidad C  
 └── Relación → Entidad D

Entidad B  
 ├── Relación → Entidad E  
 └── Relación → Entidad F

Por ejemplo:

Juan  
 ├── posee → juan@gmail.com  
 └── trabaja\_en → Empresa X

Empresa X  
 ├── posee → empresa.com  
 └── administra → sitio.com

empresa.com  
 └── apunta\_a → 192.168.1.10

En memoria podría representarse conceptualmente como:

Grafo  
 └── listaAdyacencia  
       ├── Juan → \[Email, Empresa\]  
       ├── Empresa → \[Dominio, Sitio\]  
       └── Dominio → \[IP\]

La lista de adyacencia resulta especialmente conveniente porque un vértice normalmente tendrá relaciones con una cantidad limitada de otros vértices.

---

# **11\. Búsqueda de entidades**

El sistema deberá permitir localizar entidades.

Por ejemplo:

Buscar:  
"juan@gmail.com"

Resultado:

EMAIL  
juan@gmail.com

Internamente se podrá utilizar una estructura auxiliar basada en una tabla hash/diccionario para localizar entidades rápidamente.

Pero hay una distinción importante:

> La tabla hash puede utilizarse como mecanismo auxiliar de búsqueda; **la estructura principal del grafo sigue siendo la lista de adyacencia**.

Esto evita confundir ambas estructuras durante la defensa.

---

# **12\. BFS**

Uno de los algoritmos principales será:

> **Breadth-First Search — BFS**

o búsqueda en anchura.

Ejemplo:

       A  
       / \\  
      B   C  
     / \\  
    D   E

Comenzando desde A:

A  
↓  
B C  
↓  
D E

BFS resulta útil para analizar las entidades alcanzables por niveles.

Además permite utilizar explícitamente una estructura lineal:

> **Cola (Queue)**

Conceptualmente:

Cola

A  
↓  
B  
↓  
C  
↓  
D

El algoritmo utilizará también un conjunto de visitados.

---

# **13\. Complejidad de BFS**

Para un grafo representado mediante lista de adyacencia:

O(V \+ E)

donde:

V \= cantidad de vértices  
E \= cantidad de aristas

Esto permite conectar directamente el proyecto con el contenido de complejidad algorítmica estudiado durante el año.

---

# **14\. DFS**

El segundo algoritmo principal será:

> **Depth-First Search — DFS**

o búsqueda en profundidad.

Ejemplo:

       A  
       / \\  
      B   C  
     / \\  
    D   E

DFS puede recorrer:

A → B → D  
      ↓  
      E  
  ↓  
C

Una implementación particularmente interesante para el proyecto es mediante **recursividad**, permitiendo relacionar dos temas de la materia:

DFS  
 \+  
Recursividad

También se puede implementar mediante una pila, aunque para el proyecto académico puede ser interesante justificar la versión recursiva.

Su complejidad también será:

O(V \+ E)  
---

# **15\. Búsqueda de caminos**

Otra operación interesante será:

> Encontrar un camino entre dos entidades.

Por ejemplo:

Juan  
 ↓  
Empresa X  
 ↓  
empresa.com  
 ↓  
192.168.1.10

El usuario podría solicitar:

Origen:  
Juan

Destino:  
192.168.1.10

Y el sistema devolver:

Juan  
 ↓  
trabaja\_en  
 ↓  
Empresa X  
 ↓  
posee  
 ↓  
empresa.com  
 ↓  
apunta\_a  
 ↓  
192.168.1.10

Esto puede implementarse utilizando BFS y almacenando el **predecesor** de cada nodo.

Por ejemplo:

predecesor\[B\] \= A  
predecesor\[C\] \= B  
predecesor\[D\] \= C

Luego se reconstruye el camino desde el destino hacia el origen.

---

# **16\. Operaciones principales del MVP**

El sistema inicialmente debería permitir:

### **Entidades**

* Crear entidad.  
* Modificar entidad.  
* Eliminar entidad.  
* Buscar entidad.  
* Listar entidades.

### **Relaciones**

* Crear relación.  
* Modificar relación.  
* Eliminar relación.  
* Consultar relaciones.  
* Ver relaciones de una entidad.

### **Grafo**

* Construir grafo.  
* Mostrar conexiones.  
* Recorrer mediante BFS.  
* Recorrer mediante DFS.  
* Buscar caminos.

### **Referencias**

* Asociar referencia a una relación.  
* Registrar descripción.  
* Registrar fecha/observación.

---

# **17\. Qué NO se incluirá inicialmente**

Para mantener el proyecto realizable en aproximadamente un mes y medio, quedarían fuera del MVP:

* scraping masivo;  
* reconocimiento masivo;  
* explotación de vulnerabilidades;  
* escaneo intrusivo;  
* recolección automática indiscriminada;  
* múltiples bases de datos;  
* arquitectura de microservicios;  
* Kubernetes;  
* una graph database;  
* sistemas distribuidos;  
* inteligencia artificial como componente obligatorio;  
* decenas de integraciones externas.

El principio es:

> **El grafo y sus algoritmos deben funcionar aunque no exista ninguna API externa.**

Esto es importante porque las integraciones externas pueden fallar, cambiar o requerir configuración adicional.

---

# **18\. Integraciones externas**

Si posteriormente se incorpora alguna API o fuente externa, la integración debería considerarse un módulo de **enriquecimiento**.

Por ejemplo:

                ┌───────────────┐  
                 │ API externa   │  
                 └───────┬───────┘  
                         │  
                     Adapter  
                         │  
                         ▼  
                 ┌───────────────┐  
                 │ Sistema       │  
                 └───────────────┘

Esto permite aplicar el patrón **Adapter** si realmente existe una necesidad concreta.

No tendría sentido implementar Adapter simplemente para demostrar que conocemos el patrón.

---

# **19\. Observer**

El patrón **Observer** queda como una posibilidad, no como una obligación.

Podría utilizarse si la aplicación necesita reaccionar automáticamente ante eventos del grafo.

Por ejemplo:

Se crea una relación  
        │  
        ▼  
   Evento  
        │  
 ┌──────┼─────────┐  
 ▼      ▼         ▼  
UI    Registro   Análisis

Cuando se agrega una relación:

RelacionCreada

diferentes componentes podrían reaccionar.

Pero la implementación deberá justificarse por una necesidad real del sistema.

---

# **20\. Arquitectura final propuesta**

La arquitectura conceptual queda entonces:

┌──────────────────────────────────────────┐  
│                FRONTEND                  │  
│                                          │  
│ Entidades │ Relaciones │ Grafo │ Análisis│  
└────────────────────┬─────────────────────┘  
                     │  
                     ▼  
┌──────────────────────────────────────────┐  
│           CAPA DE APLICACIÓN             │  
│                                          │  
│ Casos de uso / Servicios                 │  
└────────────────────┬─────────────────────┘  
                     │  
                     ▼  
┌──────────────────────────────────────────┐  
│              MOTOR DEL GRAFO             │  
│                                          │  
│ Entidades                                │  
│ Relaciones                               │  
│ Lista de adyacencia                      │  
│ BFS                                      │  
│ DFS                                      │  
│ Path Finding                             │  
└────────────────────┬─────────────────────┘  
                     │  
                     ▼  
┌──────────────────────────────────────────┐  
│             PERSISTENCIA                 │  
│                                          │  
│ Base de datos relacional                 │  
└──────────────────────────────────────────┘

             Opcional  
                 │  
                 ▼  
       ┌────────────────────┐  
       │ APIs / Fuentes     │  
       │ externas           │  
       │ mediante Adapter   │  
       └────────────────────┘  
---

# **21\. Flujo general de funcionamiento**

Un flujo típico sería:

Usuario  
   │  
   ▼  
Crea entidades  
   │  
   ▼  
Crea relaciones  
   │  
   ▼  
Se almacenan en BD  
   │  
   ▼  
Se carga el grafo  
   │  
   ▼  
Lista de adyacencia  
   │  
   ├──────────────┐  
   ▼              ▼  
  BFS            DFS  
   │              │  
   └──────┬───────┘  
          ▼  
      Análisis  
          │  
          ▼  
      Resultado  
---

# **22\. Relación con AED3**

Esta es una de las partes más importantes para la defensa.

El proyecto no debería presentarse simplemente como:

> "Hice una aplicación web que muestra un grafo."

Debería presentarse como:

> "Desarrollé una aplicación que utiliza un grafo dirigido representado mediante una lista de adyacencia como estructura principal para modelar relaciones entre entidades, y sobre dicha estructura implementé algoritmos de recorrido y búsqueda."

Ahí aparece claramente el contenido de la materia.

La trazabilidad podría quedar así:

| Tema AED3 | Aplicación en el proyecto |
| ----- | ----- |
| Estructuras dinámicas | Representación del grafo |
| Estructuras no lineales | Grafo |
| Lista de adyacencia | Representación del grafo |
| Vértices | Entidades |
| Aristas | Relaciones |
| Grafo dirigido | Relaciones semánticas |
| Cola | BFS |
| Recursividad | DFS |
| Complejidad | O(V+E) |
| OOP | Entidades, relaciones, grafo, servicios |
| Patrones | Observer/Adapter si se justifican |
| Testing | Pruebas unitarias e integración |
| Refactoring | Evolución del código durante el desarrollo |

Los contenidos de AED3 respaldan especialmente el uso de estructuras lineales, complejidad, recursividad y grafos; el material de la materia presenta los grafos como estructuras no lineales y contempla la representación mediante matriz o lista de adyacencia.

---

# **23\. Orden recomendado de desarrollo**

No conviene empezar por la interfaz.

El desarrollo debería avanzar aproximadamente así:

### **Etapa 1 — Modelo**

Definir:

Entidad  
Relacion  
TipoEntidad  
TipoRelacion  
Referencia

### **Etapa 2 — Grafo**

Implementar:

Grafo  
Lista de adyacencia  
Agregar entidad  
Agregar relación  
Eliminar entidad  
Eliminar relación  
Consultar vecinos

### **Etapa 3 — Algoritmos**

Implementar:

BFS  
DFS  
Búsqueda de caminos

### **Etapa 4 — Pruebas**

Probar el motor del grafo independientemente de la interfaz.

### **Etapa 5 — Persistencia**

Implementar:

BD → entidades  
BD → relaciones

y:

BD → Grafo en memoria

### **Etapa 6 — Servicios/API**

Conectar el motor con la aplicación.

### **Etapa 7 — Interfaz**

Construir:

* gestión de entidades;  
* gestión de relaciones;  
* visualización del grafo;  
* búsquedas;  
* análisis.

### **Etapa 8 — Mejoras**

Solo después evaluar:

Observer  
Adapter  
integraciones externas

si realmente aportan.

---

# **24\. Decisiones que todavía NO deberíamos cerrar**

Hay algunas cosas que todavía conviene dejar abiertas.

### **Tecnología**

Todavía no es necesario decidir inmediatamente:

Python / Java / C\# / JavaScript / etc.

Primero deberíamos terminar de definir el modelo y los requisitos.

Después podemos comparar las tecnologías disponibles según:

* conocimientos previos;  
* velocidad de desarrollo;  
* facilidad para implementar el grafo;  
* facilidad para crear la interfaz;  
* visualización;  
* acceso a BD;  
* facilidad de testing;  
* facilidad para defender académicamente el proyecto.

### **Motor visual del grafo**

También queda pendiente decidir cómo se visualizará:

A → B → C

Podría ser mediante una biblioteca JavaScript especializada, pero esa decisión puede tomarse después.

---

# **25\. Matriz de decisiones actual**

| Decisión | Estado | Decisión |
| ----- | ----- | ----- |
| Tipo de aplicación | **Confirmada** | Web |
| Arquitectura | **Confirmada** | Monolítica modular |
| Persistencia | **Confirmada** | BD relacional |
| Estructura principal | **Confirmada** | Grafo |
| Representación | **Confirmada** | Lista de adyacencia |
| Dirección | **Confirmada** | Dirigido |
| Relaciones | **Confirmada** | Tipadas |
| Referencias | **Confirmada** | Sí |
| BFS | **Confirmada** | Sí |
| DFS | **Confirmada** | Sí |
| Búsqueda de caminos | **Confirmada** | Sí |
| Graph DB | **Descartada** | No necesaria |
| Microservicios | **Descartada** | No necesarios |
| Scraping masivo | **Descartada** | Fuera del alcance |
| Escaneo intrusivo | **Descartada** | Fuera del alcance |
| APIs externas | **Propuesta** | Opcionales |
| Adapter | **Propuesta** | Solo si hay integración |
| Observer | **Propuesta** | Solo si existe una necesidad real |
| Pesos en aristas | **Descartada para MVP** | No necesarios |

---

# **26\. La idea central del proyecto**

Si tuviera que reducir todo el proyecto a una sola frase para guiar el desarrollo, sería:

> **Construir una aplicación web pequeña que permita modelar entidades y relaciones mediante un grafo dirigido, almacenarlo persistentemente y aplicar algoritmos de recorrido y búsqueda sobre una representación mediante lista de adyacencia.**

Eso es suficientemente pequeño para el tiempo disponible, pero tiene bastante profundidad técnica para una materia de **Algoritmos y Estructuras de Datos 3**.

Y, sobre todo, permite defender cada componente:

**¿Por qué grafo?**  
Porque el problema consiste en representar relaciones entre entidades.

**¿Por qué dirigido?**  
Porque las relaciones tienen significado y dirección.

**¿Por qué lista de adyacencia?**  
Porque es una representación natural del grafo y adecuada para recorrer las conexiones.

**¿Por qué BFS?**  
Para recorrer el grafo por niveles y analizar conexiones.

**¿Por qué DFS?**  
Para explorar el grafo en profundidad y aplicar recursividad.

**¿Por qué una cola?**  
Porque BFS la utiliza naturalmente.

**¿Por qué base de datos?**  
Para persistir la información, no para reemplazar el grafo.

**¿Por qué aplicación web?**  
Porque permite una interfaz adecuada para visualizar e interactuar con el grafo sin introducir una arquitectura innecesariamente compleja.

**¿Por qué relaciones tipadas?**  
Porque `posee`, `trabaja_en`, `administra`, `apunta_a`, etc. representan significados diferentes.

**¿Por qué referencias?**  
Para mantener trazabilidad sobre el origen de una relación.

---

Esta sería la **base arquitectónica v1.1** que habíamos alcanzado. A partir de acá, el siguiente paso lógico es bajar un nivel: **diseñar concretamente las clases/objetos, el modelo de la base de datos y la interfaz del `Grafo`**, antes de elegir definitivamente el lenguaje y framework.
