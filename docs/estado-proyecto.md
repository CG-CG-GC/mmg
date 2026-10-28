# **Estado del Proyecto — Mini-Maltego Académico**

> **Actualización de cierre del MVP:** el contenido fechado a continuación es
> un estado histórico de planificación y no refleja la implementación actual.
> Para instalación, alcance y pruebas consultá el [README](../README.md) y
> la [guía del MVP](mvp-academico.md). El dominio, la persistencia, la API y
> el frontend están implementados en el workspace; la última ejecución local
> de pytest registró 61 pruebas aprobadas. Esto no confirma requisitos docentes
> externos ni convierte las propuestas futuras en funcionalidades existentes.

**Estado:** Diseño técnico previo al desarrollo  
**Fecha:** 7 de octubre de 2026  
**Versión:** 0.1

---

# **1\. Proyecto**

Proyecto final de **Algoritmos y Estructuras de Datos 3** de la carrera Analista de Sistemas.

Objetivo:

Construir una aplicación web pequeña para modelar entidades y relaciones mediante un grafo dirigido, almacenar la información persistentemente y aplicar algoritmos de recorrido y búsqueda utilizando una representación mediante lista de adyacencia.

El proyecto está orientado a un escenario académico de análisis de relaciones tipo OSINT.

No se busca desarrollar una herramienta OSINT profesional ni realizar actividades intrusivas.

---

# **2\. Objetivo académico**

El proyecto debe demostrar de forma clara y defendible:

* estructuras de datos;  
* grafos;  
* lista de adyacencia;  
* grafos dirigidos;  
* cola;  
* BFS;  
* recursividad;  
* DFS;  
* búsqueda de caminos;  
* complejidad;  
* programación orientada a objetos;  
* testing;  
* refactoring;  
* separación de responsabilidades.

No se agregarán estructuras únicamente para demostrar contenidos que no tengan relación con el problema.

---

# **3\. Arquitectura congelada**

Aplicación web:

**Python \+ FastAPI \+ HTML/CSS/JavaScript \+ SQLite \+ SQLAlchemy/SQLModel \+ Cytoscape.js \+ pytest**

Arquitectura:

**Monolito modular**

Capas principales:

Interfaz  
    ↓  
Aplicación / Servicios  
    ↓  
Dominio / Motor del Grafo  
    ↓  
Persistencia

El Motor del Grafo no depende de persistencia ni de la interfaz.

---

# **4\. Dominio**

Conceptos principales:

* Entidad;  
* Relación;  
* Evidencia;  
* Tipo de Entidad;  
* Tipo de Relación.

Tipos de entidad definidos:

* PERSONA  
* ORGANIZACION  
* EMAIL  
* USUARIO  
* DOMINIO  
* SITIO\_WEB  
* IP

Tipos de relación definidos:

* POSEE  
* UTILIZA  
* TRABAJA\_EN  
* ADMINISTRA  
* PERTENECE\_A  
* APUNTA\_A

---

# **5\. Grafo**

Características:

* dirigido;  
* tipado;  
* entidades \= vértices;  
* relaciones \= aristas;  
* representación \= lista de adyacencia.

Estructuras auxiliares:

* diccionario/tabla hash;  
* cola;  
* conjunto de visitados;  
* mapa de predecesores;  
* listas de resultados;  
* pila de llamadas para DFS recursivo.

---

# **6\. Algoritmos**

### **BFS**

Implementación propia.

Utiliza:

* cola FIFO;  
* visitados;  
* predecesores;  
* niveles cuando corresponda.

Complejidad esperada:

**O(V \+ E)**

### **DFS**

Implementación propia.

Debe utilizar recursividad.

Complejidad esperada:

**O(V \+ E)**

### **Búsqueda de caminos**

Basada en:

**BFS → predecesores → reconstrucción**

---

# **7\. MVP**

Casos de uso principales:

* crear entidad;  
* consultar entidad;  
* eliminar entidad;  
* crear relación;  
* consultar relación;  
* eliminar relación;  
* visualizar grafo;  
* ejecutar BFS;  
* ejecutar DFS;  
* buscar camino.

Fuera del MVP:

* autenticación compleja;  
* administración avanzada;  
* importación masiva;  
* scraping;  
* escaneo intrusivo;  
* dashboards complejos;  
* reportes complejos;  
* Graph DB;  
* microservicios.

---

# **8\. Stack visual**

Cytoscape.js se utilizará para visualizar/interactuar con el grafo.

No debe implementar ni reemplazar:

* BFS;  
* DFS;  
* búsqueda de caminos;  
* lista de adyacencia.

Cadena:

Motor propio  
    ↓  
Resultado del algoritmo  
    ↓  
Datos/API  
    ↓  
Cytoscape.js  
    ↓  
Visualización

---

# **9\. Reglas vigentes**

Documentos de referencia:

1. **Contrato Técnico del Proyecto v1.0**  
2. **Reglas de Desarrollo y Calidad de Código v1.0**  
3. **Reglas de Frontend y UX — AntiIAUX v1.0**  
4. **Protocolo de Entrega de Agentes v1.0**  
5. Arquitectura vigente  
6. Dominio vigente  
7. Diseño vigente

---

# **10\. Regla fundamental de los agentes**

Los agentes de VS Code:

**NO modifican directamente el proyecto local.**

Deben:

* analizar;  
* diseñar;  
* proponer;  
* entregar código;  
* entregar estructura;  
* entregar tests;  
* indicar integración.

El usuario decide qué incorporar.

---

# **11\. Calidad de código**

Principios:

* evitar spaghetti code;  
* separación de responsabilidades;  
* funciones pequeñas;  
* clases con responsabilidades claras;  
* evitar duplicación;  
* evitar abstracciones innecesarias;  
* evitar patrones artificiales;  
* validar entradas;  
* tratar errores explícitamente;  
* probar el código;  
* refactorizar cuando exista una razón concreta.

---

# **12\. UX / AntiIAUX**

La interfaz no debe adoptar automáticamente:

* bento grids decorativos;  
* glassmorphism;  
* gradientes neón;  
* sparkles;  
* shimmer;  
* exceso de pills;  
* dashboards genéricos;  
* CTAs genéricos;  
* métricas ficticias;  
* animaciones innecesarias;  
* tarjetas para absolutamente todo.

No son prohibiciones absolutas.

La regla es:

> Cada decisión visual importante debe tener una justificación funcional.

---

# **13\. Estado actual**

### **Completado**

* definición del proyecto;  
* alcance general;  
* arquitectura;  
* dominio;  
* diseño;  
* selección tecnológica;  
* contrato técnico;  
* reglas de desarrollo;  
* reglas AntiIAUX;  
* protocolo de entrega de agentes.

### **En curso**

Preparación de agentes para VS Code.

### **Próxima tarea**

**Agent 03 — Motor del Grafo**

Objetivo:

Construir la propuesta de:

* dominio;  
* grafo;  
* lista de adyacencia;  
* operaciones básicas;  
* BFS;  
* DFS;  
* búsqueda de caminos;  
* tests.

Todavía no implementar:

* API;  
* persistencia;  
* frontend.

---

# **14\. Secuencia prevista de agentes**

### **Agent 03**

Motor del Grafo.

### **Agent 04**

Persistencia \+ sincronización BD ↔ Grafo.

### **Agent 05**

API / FastAPI.

### **Agent 06**

Frontend \+ UX \+ Cytoscape.

### **Agent 07**

QA / Auditoría técnica.

### **Agent 08**

Integración.

### **Agent 09**

Documentación.

### **Agent 10**

Preparación de defensa.

Los números podrán modificarse si el proyecto evoluciona.

---

# **15\. Principio general del proyecto**

> **No construir un sistema grande que demuestre poco. Construir un sistema pequeño en el que cada decisión técnica pueda ser explicada, probada y defendida.**

---

# **16\. Próximo punto de reentrada**

Cuando se abra un nuevo chat dentro del mismo Project, comenzar indicando:

**"Continuamos Mini-Maltego Académico. Leer el Estado del Proyecto vigente y continuar desde la próxima tarea indicada."**

Si existe un Estado posterior a esta versión, utilizar siempre el más reciente.

---

# **17\. Regla de actualización**

Cada vez que se complete una etapa importante:

1. actualizar este Estado;  
2. registrar decisiones nuevas;  
3. registrar decisiones congeladas;  
4. registrar pendientes;  
5. registrar próximo agente/tarea.

Esto permite cambiar de conversación sin perder continuidad.
