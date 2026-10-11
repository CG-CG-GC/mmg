# **CONTRATO TÉCNICO DEL PROYECTO**

## **Mini-Maltego Académico — v1.0**

**Estado:** Aprobado para inicio de implementación  
**Propósito:** Documento técnico operativo y fuente de verdad para el desarrollo  
**Proyecto:** Herramienta web académica de mapeo y análisis de relaciones OSINT  
**Plazo disponible:** aproximadamente 1,5 meses  
**Desarrollador:** 1 persona

---

# **1\. Propósito del contrato**

Este documento consolida las decisiones técnicas adoptadas para comenzar la implementación del proyecto.

Su objetivo es evitar que durante el desarrollo cada agente, herramienta o etapa vuelva a modificar arbitrariamente la arquitectura, el modelo de dominio o el alcance.

A partir de este documento:

**Requisito → Funcionalidad → Estructura de datos → Algoritmo → Implementación → Prueba**

debe mantenerse trazable.

Las decisiones conceptuales previas se consideran válidas y no deben rediseñarse sin una justificación explícita.

---

# **2\. Objetivo técnico**

Construir una aplicación web pequeña que permita:

* registrar entidades;  
* registrar relaciones entre entidades;  
* almacenar evidencias asociadas a relaciones;  
* representar las relaciones mediante un grafo dirigido;  
* mantener el grafo en memoria mediante una lista de adyacencia;  
* recorrer el grafo mediante BFS;  
* recorrer el grafo mediante DFS;  
* buscar caminos entre entidades;  
* persistir la información en una base de datos relacional;  
* visualizar gráficamente el resultado.

El objetivo académico principal es demostrar la aplicación práctica de estructuras de datos y algoritmos de AED3.

El proyecto no pretende convertirse en una plataforma OSINT completa.

---

# **3\. Alcance técnico**

## **Incluido**

* Aplicación web.  
* Backend Python.  
* API HTTP.  
* Modelo de dominio.  
* Grafo dirigido.  
* Lista de adyacencia.  
* BFS.  
* DFS.  
* Búsqueda de caminos.  
* Base de datos relacional.  
* CRUD básico de entidades.  
* CRUD básico de relaciones.  
* Evidencias asociadas a relaciones.  
* Visualización del grafo.  
* Validaciones.  
* Testing.  
* Seguridad básica.  
* Posibilidad futura de integraciones OSINT externas.

## **Fuera del MVP**

Quedan expresamente fuera:

* Graph Database.  
* Microservicios.  
* Kubernetes.  
* arquitectura distribuida;  
* Redis u otras infraestructuras innecesarias;  
* frontend SPA complejo;  
* React/Angular/Vue;  
* scraping masivo;  
* reconocimiento masivo;  
* escaneo intrusivo;  
* explotación de vulnerabilidades;  
* automatización de reconocimiento ofensivo;  
* dashboards complejos;  
* autenticación empresarial;  
* sistemas de usuarios complejos;  
* reportes avanzados;  
* algoritmos adicionales no justificados;  
* estructuras de datos que no tengan una función real.

El alcance es una decisión técnica crítica debido al plazo disponible.

---

# **4\. Stack tecnológico oficial**

## **Backend**

**Python \+ FastAPI**

FastAPI será responsable de:

* exponer la API;  
* recibir solicitudes;  
* validar entradas;  
* invocar la capa de aplicación;  
* devolver resultados.

FastAPI no será responsable de implementar BFS, DFS ni la estructura interna del grafo.

---

## **Frontend**

**HTML \+ CSS \+ JavaScript**

No se utilizará un framework SPA para el MVP.

La interfaz debe ser suficiente para:

* crear entidades;  
* crear relaciones;  
* consultar información;  
* ejecutar recorridos;  
* buscar caminos;  
* visualizar el grafo;  
* mostrar resultados y errores.

---

## **Base de datos**

**SQLite**

La base de datos será relacional y se utilizará principalmente para persistencia.

El modelo definido contiene:

* TIPO\_ENTIDAD  
* ENTIDAD  
* TIPO\_RELACION  
* RELACION  
* EVIDENCIA

SQLite es la opción inicial por simplicidad y bajo costo operativo.

El diseño deberá evitar decisiones que impidan una futura migración a PostgreSQL.

---

## **Persistencia / ORM**

Se utilizará una capa de persistencia basada en:

**SQLAlchemy o SQLModel**

La elección definitiva entre ambas se realizará al comenzar la implementación, priorizando simplicidad.

La elección del ORM no modifica el modelo conceptual.

---

## **Visualización**

**Cytoscape.js**

Cytoscape.js será exclusivamente una herramienta de visualización e interacción gráfica.

No se utilizará su implementación de BFS/DFS para demostrar los algoritmos de AED3.

La cadena será:

Motor propio  
    ↓  
Grafo  
    ↓  
Lista de adyacencia  
    ↓  
Algoritmo  
    ↓  
Resultado  
    ↓  
JSON  
    ↓  
Cytoscape.js  
    ↓  
Visualización

Esta separación es obligatoria para mantener la trazabilidad académica.

---

## **Testing**

**pytest**

El motor del grafo debe comenzar a probarse antes de construir toda la aplicación web.

---

# **5\. Arquitectura**

Se utilizará un:

**Monolito modular**

No se utilizarán microservicios.

La arquitectura conceptual será:

               INTERFAZ WEB  
                     │  
                     ▼  
                  FASTAPI  
                     │  
                     ▼  
             CAPA DE APLICACIÓN  
                     │  
          ┌──────────┴──────────┐  
          ▼                     ▼  
       DOMINIO             MOTOR DEL GRAFO  
          │                     │  
          │               LISTA DE ADYACENCIA  
          │                     │  
          │              BFS / DFS / CAMINOS  
          │  
          ▼  
     PERSISTENCIA  
          │  
          ▼  
        SQLite

Las integraciones OSINT, cuando existan, estarán separadas del núcleo.

---

# **6\. Estructura del proyecto**

Se adopta inicialmente:

proyecto/  
│  
├── app/  
│   ├── main.py  
│   │  
│   ├── domain/  
│   │   ├── entidad.py  
│   │   ├── relacion.py  
│   │   ├── evidencia.py  
│   │   └── grafo.py  
│   │  
│   ├── services/  
│   │   ├── entidad\_service.py  
│   │   ├── relacion\_service.py  
│   │   └── grafo\_service.py  
│   │  
│   ├── persistence/  
│   │   ├── models.py  
│   │   ├── database.py  
│   │   └── repositories.py  
│   │  
│   ├── api/  
│   │   └── routes/  
│   │  
│   ├── integrations/  
│   │   └── osint/  
│   │  
│   └── web/  
│       ├── templates/  
│       └── static/  
│           ├── css/  
│           └── js/  
│  
├── tests/  
│   ├── domain/  
│   ├── services/  
│   └── api/  
│  
└── README.md

Esta estructura no debe interpretarse como obligación de crear clases o servicios artificiales.

Si durante la implementación una separación resulta innecesaria, se priorizará la simplicidad.

---

# **7\. Modelo de dominio**

Las entidades principales son:

Entidad  
Relación  
Evidencia

## **Entidad**

Representa un elemento del universo investigado.

Tipos definidos:

PERSONA  
ORGANIZACION  
EMAIL  
USUARIO  
DOMINIO  
SITIO\_WEB  
IP

Una entidad tendrá como mínimo:

id  
tipo  
valor  
descripcion  
metadata

---

## **Relación**

Representa una conexión dirigida:

Entidad origen  
      │  
      ▼  
    Relación  
      │  
      ▼  
Entidad destino

Tipos definidos:

POSEE  
UTILIZA  
TRABAJA\_EN  
ADMINISTRA  
PERTENECE\_A  
APUNTA\_A

Las relaciones pueden contener:

* descripción;  
* fecha;  
* evidencias.

---

## **Evidencia**

Representa la procedencia o respaldo de una relación.

Contendrá conceptualmente:

id  
source  
description  
date

Una relación puede tener cero o múltiples evidencias.

---

# **8\. Motor del grafo**

El grafo es uno de los componentes centrales del proyecto.

Será:

**dirigido**

y tendrá:

* vértices \= entidades;  
* aristas \= relaciones.

El motor deberá conocer:

* entidades;  
* relaciones;  
* vecinos;  
* lista de adyacencia;  
* recorridos;  
* caminos.

El motor del grafo NO deberá conocer:

* SQL;  
* SQLite;  
* HTML;  
* CSS;  
* HTTP;  
* FastAPI;  
* APIs externas;  
* Cytoscape.js.

Esta separación es una decisión arquitectónica obligatoria.

---

# **9\. Lista de adyacencia**

La representación interna principal será:

**Lista de Adyacencia**

Conceptualmente:

A → \[B, C\]  
B → \[D\]  
C → \[D, E\]  
D → \[\]  
E → \[\]

La lista de adyacencia es una estructura de datos interna.

No tendrá:

* tabla propia en la BD;  
* persistencia independiente;  
* endpoint propio;  
* modelo SQL propio.

La BD almacena el estado persistente.

El grafo construye su representación en memoria a partir de ese estado.

---

# **10\. BFS**

Se implementará BFS manualmente.

Componentes principales:

Grafo  
 ↓  
Lista de adyacencia  
 ↓  
Cola FIFO  
 ↓  
Visitados  
 ↓  
Predecesores  
 ↓  
Niveles

El resultado conceptual deberá poder contener:

ordenRecorrido  
niveles  
predecesores

Complejidad esperada:

**Tiempo: O(V \+ E)**  
**Espacio auxiliar: O(V)**

Esto permitirá demostrar:

* grafos;  
* lista de adyacencia;  
* colas;  
* recorrido;  
* complejidad algorítmica.

---

# **11\. DFS**

DFS será implementado principalmente de forma:

**recursiva**

La intención académica es relacionar:

Grafo  
\+  
Recursividad

La implementación deberá incluir:

* condición de existencia del nodo;  
* conjunto de visitados;  
* recorrido de vecinos;  
* caso base apropiado.

Complejidad esperada:

**O(V \+ E)**

---

# **12\. Búsqueda de caminos**

La búsqueda de caminos utilizará:

BFS  
 ↓  
Predecesores  
 ↓  
Destino encontrado  
 ↓  
Reconstrucción inversa  
 ↓  
Camino

El objetivo del MVP será obtener un camino con cantidad mínima de aristas cuando exista.

No se implementarán algoritmos de caminos ponderados porque el MVP no utiliza pesos en las aristas.

---

# **13\. Persistencia**

La base de datos almacenará el estado persistente.

Modelo:

TIPO\_ENTIDAD  
      │  
      ▼  
   ENTIDAD  
      │  
      ├──────────────┐  
      │              │  
      ▼              ▼  
   RELACION       RELACION  
      │  
      ▼  
  EVIDENCIA

La representación exacta seguirá el DER definido previamente.

No se almacenará:

GRAFO  
LISTA\_ADYACENCIA  
COLA  
VISITADOS  
PREDECESORES

porque son estructuras de ejecución, no datos persistentes.

---

# **14\. BD ↔ Grafo**

Este es uno de los puntos técnicos pendientes que ahora queda convertido en requisito de implementación.

La aplicación deberá mantener:

**BD y Grafo consistentes.**

La coordinación corresponderá a la capa de aplicación/servicios.

Conceptualmente:

Solicitud  
   │  
   ▼  
Servicio  
   ├── Persistencia  
   └── Grafo

El motor del grafo nunca realizará directamente operaciones SQL.

Una modificación no debe considerarse completada si solamente se actualizó uno de los dos estados.

La estrategia concreta para manejar transacciones, errores y recuperación deberá definirse durante la implementación del stack.

---

# **15\. Normalización**

La BD utilizará como criterio conceptual de unicidad:

tipo \+ valor\_normalizado

Sin embargo, la normalización concreta todavía no se considera cerrada.

Deberá definirse durante la implementación para:

* EMAIL;  
* DOMINIO;  
* SITIO\_WEB;  
* IP;  
* USUARIO;  
* PERSONA;  
* ORGANIZACION.

La normalización debe ser:

* simple;  
* explicable;  
* consistente;  
* suficiente para evitar duplicaciones obvias.

No se implementará un sistema excesivamente sofisticado.

---

# **16\. Metadata**

La metadata queda como decisión técnica pendiente.

Debe evitarse introducir un modelo excesivamente complejo.

La primera implementación deberá utilizar una representación sencilla y justificable.

La metadata nunca debe ser necesaria para que BFS, DFS o la estructura del grafo funcionen.

---

# **17\. Seguridad**

No se requiere seguridad empresarial.

Sí se consideran obligatorias las medidas básicas:

### **Validación**

Validar:

* campos obligatorios;  
* tipos;  
* identificadores;  
* URLs;  
* fechas;  
* tamaños;  
* valores ingresados.

### **SQL Injection**

Utilizar ORM/consultas parametrizadas.

Nunca construir SQL concatenando directamente información ingresada por el usuario.

### **XSS**

Tratar como no confiables:

* descripciones;  
* metadata;  
* evidencias;  
* información proveniente de APIs.

### **APIs externas**

Todo dato externo deberá pasar por:

API externa  
    ↓  
Validación  
    ↓  
Normalización  
    ↓  
Modelo de dominio  
    ↓  
Persistencia

Nunca:

API externa → BD

sin validación intermedia.

No se agregará autenticación salvo que posteriormente exista una necesidad real de despliegue.

---

# **18\. Integraciones OSINT**

Las integraciones externas son:

**opcionales**

y no forman parte del núcleo del MVP.

La aplicación deberá funcionar completamente mediante carga manual.

Arquitectura:

API externa  
    ↓  
Adaptador / integración  
    ↓  
Validación  
    ↓  
Normalización  
    ↓  
Entidad / Relación  
    ↓  
Persistencia  
    ↓  
Grafo

Nunca:

Grafo → API externa

La integración no debe contaminar el motor del grafo.

---

# **19\. Testing**

El motor del grafo tendrá prioridad de pruebas.

Se deberán probar como mínimo:

### **Entidades**

* creación;  
* búsqueda;  
* eliminación;  
* duplicados;  
* entidades inexistentes.

### **Relaciones**

* creación;  
* eliminación;  
* relaciones duplicadas;  
* origen inexistente;  
* destino inexistente.

### **Grafo**

* vecinos;  
* grafo vacío;  
* nodo inexistente;  
* ciclos;  
* nodos aislados.

### **BFS**

* grafo simple;  
* grafo con ramas;  
* ciclos;  
* nodo aislado;  
* nodo inexistente.

### **DFS**

* grafo simple;  
* ciclos;  
* ramas;  
* nodo inexistente.

### **Caminos**

* camino existente;  
* múltiples caminos;  
* camino inexistente;  
* origen \= destino;  
* nodos inexistentes.

---

# **20\. Orden oficial de implementación**

La implementación seguirá este orden aproximado:

1\. Entidad  
2\. Relación  
3\. Evidencia

4\. Grafo  
5\. Lista de adyacencia  
6\. Operaciones básicas

7\. BFS  
8\. DFS  
9\. Búsqueda de caminos

10\. Tests del motor

11\. SQLite  
12\. Persistencia  
13\. Repositories

14\. Servicios de aplicación  
15\. Coordinación BD ↔ Grafo

16\. FastAPI  
17\. Endpoints

18\. Frontend básico  
19\. CRUD

20\. Cytoscape.js

21\. Seguridad y validaciones

22\. Integraciones OSINT opcionales

23\. Pruebas finales  
24\. Preparación de defensa

El principio fundamental es:

**primero demostrar que el motor funciona; después construir la aplicación alrededor de él.**

---

# **21\. Prioridad del desarrollo**

La prioridad será:

### **Prioridad 1 — Académica**

Grafo  
Lista de adyacencia  
BFS  
DFS  
Recursividad  
Complejidad  
Búsqueda de caminos

### **Prioridad 2 — Funcional**

Entidades  
Relaciones  
Persistencia  
API  
Interfaz  
Visualización

### **Prioridad 3 — Complementaria**

Evidencias mejoradas  
Metadata avanzada  
Integraciones OSINT

Si el tiempo comienza a ser insuficiente, se recortará la prioridad 3 antes de tocar el núcleo académico.

---

# **22\. Criterio para agregar funcionalidades**

Toda nueva funcionalidad deberá responder:

1. ¿Aporta al objetivo del proyecto?  
2. ¿Aporta algo a AED3?  
3. ¿Es necesaria para el MVP?  
4. ¿Puede implementarse sin poner en riesgo el plazo?  
5. ¿Puede explicarse y defenderse fácilmente?

Si la respuesta es negativa, la funcionalidad no se incorpora al MVP.

---

# **23\. Decisiones congeladas**

Las siguientes decisiones no deberán modificarse sin una justificación explícita:

* aplicación web;  
* monolito modular;  
* Python;  
* FastAPI;  
* HTML/CSS/JavaScript;  
* SQLite;  
* Cytoscape.js;  
* pytest;  
* BD relacional;  
* grafo dirigido;  
* lista de adyacencia;  
* BFS;  
* DFS;  
* búsqueda de caminos;  
* relaciones tipadas;  
* evidencias;  
* APIs externas opcionales;  
* Graph Database fuera del MVP;  
* microservicios fuera del MVP;  
* scraping masivo fuera del MVP;  
* escaneo intrusivo fuera del MVP.

La selección del stack fue realizada considerando especialmente velocidad de desarrollo, claridad académica, implementación manual de estructuras y algoritmos, integración con BD, testing y plazo de aproximadamente 1,5 meses.

---

# **24\. Decisiones todavía abiertas**

Estas decisiones pueden definirse durante la implementación:

### **D-01 — ORM**

SQLAlchemy o SQLModel.

### **D-02 — Normalización**

Reglas concretas para cada tipo de entidad.

### **D-03 — Metadata**

Formato y almacenamiento.

### **D-04 — BD ↔ Grafo**

Mecanismo concreto para garantizar consistencia ante errores.

### **D-05 — Detalles de interfaz**

Diseño visual, distribución y experiencia de usuario.

Estas decisiones no deben utilizarse como motivo para volver a abrir la arquitectura general.

---

# **25\. Regla para agentes de desarrollo**

Todo agente que trabaje sobre el proyecto deberá considerar este documento como referencia técnica.

Un agente NO debe:

* cambiar el stack sin autorización;  
* reemplazar el grafo por una librería;  
* implementar BFS/DFS mediante Cytoscape;  
* introducir una Graph Database;  
* convertir el proyecto en una SPA compleja;  
* agregar microservicios;  
* agregar funcionalidades fuera del MVP;  
* modificar el modelo conceptual arbitrariamente.

Si detecta un problema real con una decisión congelada, deberá informar:

DECISIÓN EN CONFLICTO:  
\[decisión actual\]

PROBLEMA DETECTADO:  
\[explicación\]

IMPACTO:  
\[qué afecta\]

PROPUESTA:  
\[alternativa\]

JUSTIFICACIÓN:  
\[por qué\]

El agente no debe modificar unilateralmente una decisión arquitectónica.

---

# **26\. Regla académica fundamental**

Cada componente importante del sistema debe poder responder:

> **¿Por qué existe?**

Ejemplos:

**¿Por qué un grafo?**  
Porque el problema consiste en representar relaciones entre entidades.

**¿Por qué dirigido?**  
Porque las relaciones poseen dirección y significado.

**¿Por qué lista de adyacencia?**  
Porque permite representar eficientemente las conexiones y recorrerlas.

**¿Por qué BFS?**  
Porque permite recorrer por niveles y sirve para búsqueda de caminos.

**¿Por qué DFS?**  
Porque permite explorar en profundidad y relacionar grafos con recursividad.

**¿Por qué una cola?**  
Porque BFS requiere un mecanismo FIFO.

**¿Por qué base de datos?**  
Para persistir el estado del sistema.

**¿Por qué Cytoscape.js?**  
Para visualizar el resultado del motor propio.

**¿Por qué no Graph Database?**  
Porque introduciría complejidad innecesaria y no aporta al objetivo académico del MVP.

Estas relaciones deben mantenerse visibles durante el desarrollo y posteriormente utilizarse en la defensa oral.

---

# **27\. Cadena de trazabilidad académica**

La implementación deberá poder explicarse mediante:

AED3  
 │  
 ├── Grafos  
 │      ↓  
 │   Grafo dirigido  
 │      ↓  
 │   Lista de adyacencia  
 │      ↓  
 │   BFS ──────→ Cola  
 │      │  
 │      └──────→ Predecesores  
 │  
 ├── Recursividad  
 │      ↓  
 │     DFS  
 │  
 ├── Complejidad  
 │      ↓  
 │   O(V \+ E)  
 │  
 └── POO  
        ↓  
   Entidad / Relación / Evidencia / Grafo

La implementación deberá preservar esta correspondencia.

---

# **28\. Criterio de éxito del MVP**

El proyecto se considera técnicamente satisfactorio cuando puede:

1. Crear entidades.  
2. Crear relaciones dirigidas.  
3. Persistirlas.  
4. Reconstruir el grafo.  
5. Representarlo mediante lista de adyacencia.  
6. Ejecutar BFS propio.  
7. Ejecutar DFS propio.  
8. Buscar un camino entre dos entidades.  
9. Mostrar los resultados.  
10. Visualizar el grafo.  
11. Demostrar mediante pruebas que el motor funciona.  
12. Explicar claramente qué conceptos de AED3 se aplicaron y por qué.

Las integraciones OSINT automáticas NO son requisito para considerar exitoso el MVP.

---

# **29\. Estado del proyecto**

## **Diseño conceptual**

**CERRADO**

## **Arquitectura**

**CERRADA**

## **Modelo de dominio**

**CERRADO**

## **DER**

**CERRADO**

## **Casos de uso MVP**

**CERRADOS**

## **Stack**

**CERRADO**

## **Motor del grafo**

**DEFINIDO — LISTO PARA IMPLEMENTAR**

## **Persistencia**

**DEFINIDA — LISTA PARA IMPLEMENTAR**

## **Frontend**

**DEFINIDO A NIVEL TÉCNICO**

## **Seguridad**

**DEFINIDA A NIVEL MVP**

## **Integraciones OSINT**

**OPCIONALES**

## **Implementación**

**PRÓXIMA ETAPA**

---

# **30\. Veredicto técnico**

El proyecto se encuentra en condiciones de abandonar la etapa de diseño conceptual y comenzar la implementación.

La prioridad absoluta es construir y probar:

Entidad  
   ↓  
Relación  
   ↓  
Grafo  
   ↓  
Lista de adyacencia  
   ↓  
BFS  
   ↓  
DFS  
   ↓  
Búsqueda de caminos

Después se incorporarán:

SQLite  
   ↓  
Persistencia  
   ↓  
FastAPI  
   ↓  
Frontend  
   ↓  
Cytoscape.js

Y solamente cuando el MVP esté estable:

Integraciones OSINT

**Regla final del proyecto:**

> No construir un sistema grande que demuestre poco.  
> Construir un sistema pequeño en el que cada decisión técnica pueda ser explicada, probada y defendida.

