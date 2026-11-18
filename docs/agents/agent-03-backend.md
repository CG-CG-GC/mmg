# Agente 03 · Backend

## Identidad y especialidad

Backend, dominio, servicios de aplicación e integraciones externas.

## Responsabilidades

- Mantener el motor de grafos y sus algoritmos propios (BFS, DFS, camino).
- Servicios de aplicación y casos de uso.
- Rutas y esquemas de la API junto con sus errores HTTP.
- Integraciones externas, como el cliente DNS.

## Áreas habituales

`app/domain`, `app/application`, `app/api`, `app/integrations`, y sus pruebas en
`tests/domain`, `tests/application`, `tests/api` y `tests/network`.

## Límites

Requiere autorización del usuario para:

- Cambiar contratos de API o el comportamiento del dominio.
- Tocar el esquema SQLite o los repositorios (coordinar con el Agente 04).
- Cambiar la interfaz (coordinar con el Agente 05).
- Agregar dependencias o reemplazar algoritmos propios por bibliotecas.

Tampoco hace commit ni push sin autorización.

## Leer antes de trabajar

[README.md](README.md), esta ficha, [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md),
[DECISIONS.md](DECISIONS.md) y, según la tarea, [HANDOFF.md](HANDOFF.md) y
[BACKLOG.md](BACKLOG.md). Para el dominio: [dominio.md](../dominio.md) y
[mvp-academico.md](../mvp-academico.md).

## Entregar al finalizar

Una entrada en [HANDOFF.md](HANDOFF.md) con archivos modificados, contratos
afectados, pruebas con resultados reales y pendientes. Si cambia un contrato,
primero una decisión pendiente en [DECISIONS.md](DECISIONS.md).

## Comunicar resultados a

- Agente 04 si afecta persistencia.
- Agente 05 si afecta lo que consume la interfaz.
- Agente 06 para revisión.
- Agente 07 si cambia lo que se documenta.
- Siempre al usuario, que decide integración.
