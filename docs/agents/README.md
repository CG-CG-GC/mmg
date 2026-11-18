# Coordinación de agentes

Este directorio es la memoria compartida de los agentes 03 a 07 del proyecto
Mini-Maltego Académico. Permite abrir un chat nuevo, leer pocos documentos y
continuar sin el historial de las conversaciones anteriores.

## Orden de lectura

1. [`AGENTS.md`](../../AGENTS.md): instrucciones vigentes para cualquier agente.
2. Tu ficha individual (tabla de abajo).
3. [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md): resumen técnico y reglas de trabajo.
4. [`DECISIONS.md`](DECISIONS.md): decisiones vigentes y puntos pendientes.
5. [`HANDOFF.md`](HANDOFF.md) y [`BACKLOG.md`](BACKLOG.md), según la tarea: el
   primero para retomar una entrega, el segundo para saber qué falta.

## Fichas

| Agente | Especialidad | Ficha |
|---|---|---|
| 03 | Backend, dominio, aplicación e integraciones | [agent-03-backend.md](agent-03-backend.md) |
| 04 | Persistencia, repositorios, SQLAlchemy y SQLite | [agent-04-persistence.md](agent-04-persistence.md) |
| 05 | Frontend, UX, JavaScript y Cytoscape.js | [agent-05-frontend.md](agent-05-frontend.md) |
| 06 | QA independiente, regresiones, accesibilidad y seguridad | [agent-06-qa.md](agent-06-qa.md) |
| 07 | Documentación académica y defensa | [agent-07-documentation.md](agent-07-documentation.md) |

## Reglas de comunicación

- La comunicación entre agentes queda por escrito en `HANDOFF.md`, no en
  conversaciones privadas.
- Cada agente actualiza `HANDOFF.md` al terminar y `BACKLOG.md` si cambia el
  estado real de una tarea.
- No se modifican archivos de otra especialidad salvo que la tarea lo requiera
  y esté autorizado.
- Una decisión que afecta a varios módulos (contratos de API, esquema SQLite,
  dependencias, comportamiento del dominio) se deja como **pendiente** en
  `DECISIONS.md` y se coordina antes de implementarla.
- No se copian historiales de chat a estos documentos: se registran hechos,
  archivos, resultados y pendientes.
- Una tarea solo se marca como completada si se verificó. Lo no probado se
  declara como no probado.
- No hay atribución de autoría de IA en Git: sin `Co-authored-by` ni otros
  trailers. Nadie hace commit ni push sin autorización del usuario.

## Cómo registrar una entrega

1. Copiá la plantilla de `HANDOFF.md` al principio de la sección de entregas.
2. Completá todos los campos con datos reales: archivos tocados, resultados
   exactos de las pruebas y lo que no se probó.
3. Indicá el estado: pendiente, en curso, listo para revisión, aprobado o
   requiere correcciones.
4. Cuando el destinatario revise, actualiza el estado de esa entrega en lugar
   de escribir otra.

## Relación con la documentación existente

Estos documentos resumen y enlazan; no reemplazan a
[`ContratoTecnico.md`](../ContratoTecnico.md),
[`reglas-desarrollo.md`](../reglas-desarrollo.md) ni a
[`mvp-academico.md`](../mvp-academico.md). Ante una contradicción entre
documentos, no la resuelvas en silencio: registrala en `DECISIONS.md` como
pendiente. Las diferencias ya detectadas están en
[`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md#documentos-con-criterios-distintos).
