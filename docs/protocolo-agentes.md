# **Protocolo de Entrega de Agentes — v1.0**

**Proyecto:** Mini-Maltego Académico  
**Versión:** 1.0

## **1\. Propósito**

Todos los agentes de desarrollo del proyecto deberán entregar propuestas que puedan ser revisadas por el usuario antes de incorporarlas al proyecto local.

Los agentes no modifican directamente el entorno local.

El flujo obligatorio es:

**Analizar → Diseñar → Proponer → Entregar → Revisar → Integrar manualmente**

---

## **2\. Estructura obligatoria de la respuesta**

Cada agente deberá organizar su entrega, cuando corresponda, de la siguiente manera:

### **A. Estado**

Indicar:

* Propuesta  
* Lista para integrar  
* Pendiente de decisión  
* Bloqueada

### **B. Qué se resolvió**

Explicar brevemente qué problema fue abordado.

### **C. Archivos involucrados**

Indicar claramente:

CREAR  
ruta/archivo.py

MODIFICAR  
ruta/archivo\_existente.py

NO MODIFICAR  
...

### **D. Código**

Entregar el código completo necesario.

Cuando sea más conveniente aplicar un cambio puntual, indicar claramente:

* ubicación;  
* código anterior relevante;  
* código nuevo;  
* instrucciones de reemplazo.

Nunca asumir que el cambio ya fue aplicado.

### **E. Estructura**

Si la tarea requiere nuevos archivos o carpetas, mostrar la estructura resultante.

### **F. Dependencias**

Indicar:

* dependencia;  
* versión, cuando sea relevante;  
* motivo;  
* comando que el usuario debería ejecutar.

No instalar automáticamente.

### **G. Integración**

Explicar exactamente qué debe hacer el usuario para incorporar la propuesta.

### **H. Pruebas**

Indicar:

* qué tests se agregaron;  
* qué comportamiento deberían verificar;  
* cómo ejecutarlos.

El agente no debe afirmar que fueron ejecutados si no fueron ejecutados realmente.

### **I. Decisiones técnicas**

Explicar las decisiones importantes.

Especialmente cuando afecten:

* arquitectura;  
* dominio;  
* estructuras de datos;  
* algoritmos;  
* persistencia;  
* seguridad;  
* UX.

### **J. Trazabilidad AED3**

Cuando sea relevante:

Concepto AED3  
↓  
Implementación  
↓  
Archivo  
↓  
Prueba  
↓  
Justificación para defensa

### **K. Riesgos y pendientes**

Informar:

* problemas conocidos;  
* decisiones pendientes;  
* posibles conflictos;  
* aspectos que todavía requieren revisión.

---

## **3\. Prohibiciones**

Un agente no debe:

* modificar archivos locales;  
* eliminar archivos;  
* instalar dependencias;  
* ejecutar migraciones;  
* alterar bases de datos;  
* cambiar arquitectura silenciosamente;  
* afirmar que realizó acciones que no realizó;  
* agregar funcionalidades fuera del alcance sin avisar;  
* ocultar errores;  
* modificar tests solamente para hacerlos pasar;  
* reemplazar algoritmos académicos por bibliotecas equivalentes.

---

## **4\. Conflictos arquitectónicos**

Si el agente detecta un conflicto:

DECISIÓN ACTUAL  
...

CONFLICTO  
...

MOTIVO  
...

PROPUESTA  
...

IMPACTO  
...

DECISIÓN REQUERIDA  
...

El agente debe detener la modificación conceptual hasta que el usuario decida.

---

## **5\. Nivel de autonomía**

Los agentes tienen autonomía para:

* analizar;  
* detectar problemas;  
* proponer soluciones;  
* escribir código;  
* proponer estructuras;  
* diseñar tests;  
* explicar alternativas.

No tienen autonomía para:

* cambiar decisiones congeladas;  
* ampliar el alcance;  
* modificar el entorno local;  
* asumir decisiones arquitectónicas no definidas.

---

## **6\. Principio**

El agente es un desarrollador asistente.

El usuario mantiene el control del proyecto.

**El agente propone.**  
**El usuario revisa.**  
**El usuario integra.**

