# **Reglas de Desarrollo y Calidad de Código — v1.0**

**Proyecto:** Mini-Maltego Académico  
**Versión:** 1.0  
**Propósito:** Establecer las reglas que deberán seguir los agentes de desarrollo y cualquier código incorporado al proyecto.

---

# **1\. Principio fundamental**

El objetivo no es producir la mayor cantidad de código posible.

El objetivo es construir un sistema pequeño, claro, mantenible y académicamente defendible.

> **No construir un sistema grande que demuestre poco. Construir un sistema pequeño en el que cada decisión técnica pueda ser explicada, probada y defendida.**

---

# **2\. Los agentes NO modifican el entorno local**

Esta es una regla obligatoria para todos los agentes.

Los agentes utilizados durante el desarrollo:

* NO deben modificar directamente el proyecto local del usuario;  
* NO deben crear archivos directamente en su repositorio;  
* NO deben eliminar archivos;  
* NO deben ejecutar migraciones sobre la base de datos local;  
* NO deben instalar dependencias automáticamente;  
* NO deben modificar configuraciones del entorno;  
* NO deben ejecutar acciones destructivas.

Su función es:

**analizar → diseñar → proponer → entregar**

El usuario será quien decida qué incorporar a su proyecto.

---

# **3\. Qué debe entregar un agente**

Cuando se requiera una modificación, el agente debe entregar, según corresponda:

* código completo;  
* archivos nuevos;  
* archivos modificados;  
* estructura de carpetas;  
* contenido de configuración;  
* comandos que el usuario debe ejecutar;  
* dependencias necesarias;  
* pruebas;  
* instrucciones de integración;  
* explicación de las decisiones;  
* advertencias o posibles conflictos.

Cuando sea necesario modificar un archivo existente, debe indicar claramente:

**Archivo:** `ruta/al/archivo`

**Acción:** crear / reemplazar / agregar / modificar

**Contenido o cambio propuesto:** código correspondiente.

No debe asumir que el cambio ya fue aplicado.

---

# **4\. El usuario mantiene el control**

El agente propone.

El usuario decide.

Por lo tanto, un agente nunca debe decir:

> "Ya implementé esto en tu proyecto."

Debe decir:

> "Te propongo incorporar este cambio."

o:

> "Este es el archivo que deberías crear/reemplazar."

---

# **5\. No modificar arquitectura silenciosamente**

El proyecto posee un contrato técnico.

Los documentos de referencia principales son:

1. Contrato Técnico del Proyecto;  
2. Reglas de Desarrollo;  
3. Reglas de Frontend y UX — AntiIAUX;  
4. documentos de arquitectura y dominio vigentes.

Si un agente detecta que una implementación requiere modificar una decisión arquitectónica:

**NO debe cambiarla silenciosamente.**

Debe informar:

* decisión actual;  
* conflicto detectado;  
* motivo;  
* alternativa propuesta;  
* consecuencias;  
* recomendación.

La decisión final corresponde al usuario.

---

# **6\. Separación de responsabilidades**

Debe respetarse la separación definida en la arquitectura.

### **Interfaz**

Responsable de:

* mostrar información;  
* recibir acciones;  
* representar estados;  
* enviar solicitudes.

No debe contener reglas de negocio complejas.

### **Aplicación / Servicios**

Responsable de:

* casos de uso;  
* validaciones;  
* coordinación;  
* persistencia;  
* actualización del grafo.

### **Dominio**

Responsable de:

* Entidad;  
* Relación;  
* Evidencia;  
* tipos;  
* reglas propias del dominio.

### **Motor del Grafo**

Responsable de:

* representación en memoria;  
* lista de adyacencia;  
* recorridos;  
* búsqueda de caminos.

No debe conocer:

* HTML;  
* HTTP;  
* SQL;  
* FastAPI;  
* JavaScript;  
* Cytoscape;  
* APIs externas.

### **Persistencia**

Responsable de:

* guardar;  
* recuperar;  
* actualizar;  
* eliminar datos.

No debe implementar BFS ni DFS.

### **Integraciones**

Responsables de:

* comunicarse con APIs externas;  
* transformar respuestas;  
* producir información compatible con el dominio.

Las integraciones no deben ser necesarias para que el núcleo del proyecto funcione.

---

# **7\. Evitar spaghetti code**

Debe evitarse especialmente:

* funciones gigantes;  
* clases con demasiadas responsabilidades;  
* archivos que contienen todo el sistema;  
* lógica de negocio mezclada con HTML;  
* SQL mezclado con reglas de negocio;  
* endpoints que realizan demasiadas operaciones;  
* duplicación innecesaria;  
* variables globales innecesarias;  
* dependencias circulares;  
* código difícil de probar;  
* condicionales excesivamente anidados;  
* lógica duplicada entre frontend y backend;  
* funciones que hacen cosas conceptualmente diferentes.

Si una función tiene demasiadas responsabilidades, debe evaluarse dividirla.

---

# **8\. No sobrearquitecturar**

Evitar crear abstracciones únicamente porque "son buenas prácticas".

No crear:

* factories innecesarias;  
* interfaces artificiales;  
* capas sin responsabilidad real;  
* patrones de diseño por obligación;  
* clases que solamente envuelven otra clase;  
* configuraciones excesivamente complejas;  
* microservicios;  
* sistemas de eventos innecesarios.

Un patrón de diseño solo debe incorporarse cuando resuelva un problema real.

---

# **9\. Patrones de diseño**

Los patrones incluidos en AED3 deben utilizarse cuando tengan sentido.

No se deben agregar patrones solamente para demostrar que fueron estudiados.

Por ejemplo:

**Observer**

Solo si existe realmente un mecanismo de notificación/desacoplamiento que lo justifique.

**Adapter**

Solo si existe una interfaz externa o componente incompatible que necesite adaptación.

La ausencia de patrones también puede ser una decisión técnicamente defendible.

---

# **10\. Algoritmos académicos**

Los algoritmos centrales deben ser implementados de manera explícita y comprensible.

Especialmente:

* representación mediante lista de adyacencia;  
* BFS;  
* DFS;  
* búsqueda de caminos.

No reemplazar estos algoritmos mediante una biblioteca que esconda su funcionamiento.

Las bibliotecas pueden utilizarse para:

* persistencia;  
* HTTP;  
* visualización;  
* utilidades;  
* infraestructura.

Pero el núcleo académico debe permanecer bajo control del proyecto.

---

# **11\. Estructuras de datos**

Cada estructura utilizada debe tener una razón.

El proyecto utilizará principalmente:

* lista de adyacencia;  
* diccionario/tabla hash;  
* cola;  
* conjunto de visitados;  
* mapa de predecesores;  
* pila de llamadas para DFS recursivo;  
* listas de resultados.

No agregar estructuras como:

* listas enlazadas;  
* árboles;  
* ABB;  
* B/B+;  
* matrices;

únicamente para demostrar contenido de la materia.

La documentación debe explicar por qué una estructura fue utilizada y por qué otras no.

---

# **12\. Complejidad**

Las operaciones relevantes deben poder analizarse.

Especialmente:

* agregar/buscar entidades;  
* recorrer vecinos;  
* BFS;  
* DFS;  
* búsqueda de caminos.

Los agentes deben evitar afirmaciones de complejidad sin fundamento.

Para BFS y DFS sobre lista de adyacencia, la referencia conceptual será:

**O(V \+ E)**

donde:

* V \= cantidad de vértices;  
* E \= cantidad de aristas.

La complejidad debe poder explicarse en la defensa.

---

# **13\. Código legible**

El código debe priorizar:

* nombres descriptivos;  
* funciones pequeñas;  
* responsabilidades claras;  
* estructuras simples;  
* flujo comprensible;  
* convenciones consistentes.

No se debe buscar "código inteligente".

Se debe buscar código que otro estudiante pueda leer y comprender.

---

# **14\. Comentarios**

Los comentarios deben explicar:

* decisiones;  
* motivos;  
* restricciones;  
* aspectos no evidentes.

Evitar comentarios que simplemente repitan el código.

Ejemplo poco útil:

\# Incrementa i  
i \+= 1

Ejemplo útil:

\# Se utiliza una cola FIFO porque BFS debe procesar  
\# los vértices en orden de nivel.

---

# **15\. Manejo de errores**

Los errores deben tratarse explícitamente.

No utilizar:

* `except: pass`;  
* silenciamiento de excepciones;  
* valores falsos para ocultar errores;  
* mensajes genéricos cuando se pueda identificar el problema.

Los errores deben permitir determinar:

* qué ocurrió;  
* dónde ocurrió;  
* qué operación estaba realizándose;  
* qué debe corregirse.

---

# **16\. Validaciones**

Las entradas deben validarse antes de procesarse.

Especialmente:

* identificadores;  
* tipos;  
* valores obligatorios;  
* longitudes;  
* URLs;  
* fechas;  
* relaciones;  
* referencias a entidades inexistentes.

No confiar ciegamente en datos provenientes de:

* frontend;  
* base de datos;  
* APIs externas.

---

# **17\. Seguridad básica**

Debe evitarse:

* SQL construido mediante concatenación;  
* datos externos tratados como confiables;  
* HTML sin sanitización cuando corresponda;  
* exposición innecesaria de información;  
* secretos dentro del código;  
* credenciales hardcodeadas.

La seguridad debe ser proporcional al alcance del proyecto.

No convertir el proyecto en un sistema empresarial de seguridad si no es necesario.

---

# **18\. Dependencias**

Toda dependencia externa debe tener una razón.

Antes de incorporar una biblioteca, el agente debe indicar:

* qué problema resuelve;  
* por qué no conviene resolverlo directamente;  
* impacto en el proyecto;  
* si afecta la explicación académica.

Evitar dependencias que oculten justamente el contenido que se pretende demostrar.

---

# **19\. Testing**

Las pruebas no deben ser una etapa final olvidada.

El desarrollo debe contemplar pruebas desde las primeras implementaciones.

Especialmente:

### **Motor del grafo**

Probar:

* agregar entidad;  
* eliminar entidad;  
* agregar relación;  
* eliminar relación;  
* vecinos;  
* BFS;  
* DFS;  
* caminos;  
* casos inexistentes;  
* grafos vacíos;  
* grafos con ciclos;  
* grafos desconectados.

### **Servicios**

Probar:

* validaciones;  
* coordinación;  
* errores;  
* consistencia.

### **API**

Probar:

* solicitudes válidas;  
* solicitudes inválidas;  
* respuestas;  
* errores.

---

# **20\. No ocultar problemas con tests**

Los tests deben detectar problemas.

No modificar un test simplemente para que pase si el comportamiento correcto todavía no está resuelto.

Si existe una contradicción entre:

* requisito;  
* arquitectura;  
* implementación;  
* test;

el agente debe informar la contradicción.

---

# **21\. Refactoring**

El código puede cambiar durante el desarrollo.

Refactorizar cuando exista:

* duplicación;  
* responsabilidad excesiva;  
* nombres confusos;  
* dependencia innecesaria;  
* función demasiado grande;  
* acoplamiento excesivo.

Pero no refactorizar simplemente para "hacerlo más sofisticado".

El refactoring debe mejorar una propiedad concreta.

---

# **22\. No implementar antes de comprender**

Antes de proponer código importante, el agente debe comprender:

* arquitectura;  
* dominio;  
* responsabilidades;  
* estructuras;  
* casos de uso;  
* restricciones.

Si falta información crítica, debe preguntar.

No debe inventar decisiones importantes.

---

# **23\. No expandir el alcance**

El agente no debe agregar funcionalidades por iniciativa propia que no sean necesarias para el MVP.

Especialmente:

* autenticación compleja;  
* roles;  
* dashboards;  
* scraping masivo;  
* escaneo;  
* Graph DB;  
* microservicios;  
* importaciones masivas;  
* sistemas de reportes complejos;  
* integraciones innecesarias.

Una funcionalidad adicional puede proponerse, pero debe quedar claramente separada del MVP.

---

# **24\. Documentar decisiones relevantes**

Cuando exista una decisión técnica importante, el agente debe explicar:

* qué se propone;  
* por qué;  
* alternativas;  
* ventajas;  
* desventajas;  
* impacto;  
* relación con AED3.

Esto permitirá posteriormente utilizar el desarrollo como material para la defensa oral.

---

# **25\. Formato de entrega de los agentes**

Cuando un agente termine una tarea, debe entregar como mínimo:

### **1\. Resultado**

Qué propone incorporar.

### **2\. Archivos**

Qué archivos deben:

* crearse;  
* modificarse;  
* eliminarse, si correspondiera.

### **3\. Código**

Código completo o cambios claramente delimitados.

### **4\. Integración**

Qué debe hacer el usuario para incorporarlo.

### **5\. Pruebas**

Qué pruebas deben ejecutarse.

### **6\. Decisiones**

Qué decisiones técnicas fueron tomadas.

### **7\. Riesgos**

Qué problemas o puntos pendientes quedan.

### **8\. Estado**

Indicar si la tarea está:

* propuesta;  
* lista para integrar;  
* pendiente de decisión;  
* bloqueada.

---

# **26\. Regla de transparencia**

Un agente nunca debe afirmar que:

* ejecutó código;  
* ejecutó tests;  
* verificó una integración;  
* modificó archivos;  
* instaló dependencias;

si realmente no lo hizo.

Debe diferenciar claramente entre:

**"Esto debería funcionar"**

y

**"Esto fue probado y produjo este resultado."**

---

# **27\. Regla de trazabilidad académica**

Siempre que sea relevante, el agente debe poder señalar:

**Concepto AED3 → implementación → ubicación del código → prueba → explicación para defensa**

Ejemplo:

**Grafo → `grafo.py` → lista de adyacencia → `test_grafo.py` → explicación de representación.**

**BFS → `grafo.py` → cola FIFO → test BFS → O(V+E).**

Esto permitirá demostrar que los conceptos de la materia no están presentes únicamente de forma nominal.

---

# **28\. Regla final**

Los agentes no deben optimizar para:

> "generar mucho código".

Deben optimizar para:

> **generar el código mínimo necesario, correctamente estructurado, comprensible, probado y defendible.**

Y siempre respetar:

**Arquitectura antes que implementación.**

**Claridad antes que sofisticación.**

**Necesidad antes que abstracción.**

**Pruebas antes que confianza.**

**Decisiones explícitas antes que defaults.**

**Propuesta antes que modificación.**

**Control del usuario antes que automatización.**

