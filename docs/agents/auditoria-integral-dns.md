# Auditoría integral de incorporación DNS

La auditoría y reauditoría anteriores son registros históricos. El resultado vigente está en [Verificación final del 2026-11-18](#verificación-final-del-2026-11-18).

**Fecha:** 2026-11-17
**Auditor:** Agente 06
**Alcance:** incorporación selectiva de DNS A/AAAA, regresiones del MVP y capacidades previas de OSINT DNS.

## Resumen ejecutivo

La suite completa pasó: **257 pruebas aprobadas y 1 omitida**, igual que el último resultado comunicado. La revisión de aplicación, API, persistencia, frontend y navegador confirmó la selección y escritura de A/AAAA, el manejo de errores, la protección frente a HTML externo y la ausencia de desbordamiento horizontal en los anchos solicitados.

La versión **no está lista para aprobarse ni para cerrar el manual académico**. Se reprodujeron dos defectos de severidad ALTO:

1. El codec IDNA 2003 transforma `straße.de` en `strasse.de`, por lo que la consulta DNS silenciosamente apunta a otro nombre.
2. Dos incorporaciones concurrentes pueden publicar fuera de orden sus reconstrucciones y dejar el grafo en memoria atrasado respecto de SQLite, aunque ambas escrituras hayan sido exitosas.

También se confirmó el pendiente P-05: el CRUD acepta simultáneamente dominios equivalentes en Unicode y punycode; la incorporación evita escribir parcialmente y devuelve 409 ante la ambigüedad. No se modificó lógica funcional ni el esquema.

**Veredicto: REQUIERE CORRECCIONES.**

## Cobertura

### Verificado

- Consulta DNS en aplicación, API e integración; validación de respuesta, estados por tipo, metadatos de fuente/fecha, prioridad MX, deduplicación, límites y errores del proveedor.
- Selección, revisión deliberada, confirmación y construcción del lote A/AAAA. CNAME, MX y NS no tienen control de incorporación y el backend rechaza tipos ajenos.
- Canonicalización de dominios e IP, reutilización de entidades y relaciones, evidencias, ambigüedad, idempotencia, `BEGIN IMMEDIATE`, rollback, commit bloqueado y liberación de sesiones.
- Contrato API frente a la interfaz, procedencia declarada, actualización del grafo y recuperación de errores.
- `osint.js` completo. El archivo no está versionado y no existe diff fiable contra HEAD; se comprobó su comportamiento actual, no su equivalencia textual con una versión anterior.
- CRUD, endpoints y algoritmos del MVP mediante pytest; BFS, DFS y camino corto también tienen sus pruebas de dominio/API existentes.
- Navegador real sobre servidor local, SQLite temporal y respuesta DNS interceptada. No se consultó Internet ni se modificó la base de datos del usuario.
- Responsive a 320, 700, 900 y 1440 px; no se observó overflow horizontal.
- Contraste calculado para colores representativos: texto normal 6.20:1, botón principal 7.76:1, error 9.19:1, éxito 9.15:1 y foco 3.60:1.

### No verificado

- `pip-audit`: no se ejecutó porque requiere consultar el índice de vulnerabilidades en Internet y la instrucción de esta auditoría prohíbe consultas externas.
- CI de GitHub, despliegue, concurrencia entre procesos, modo WAL, reinicio del servidor durante una petición y rendimiento con una base grande.
- Se perdió el identificador de página del navegador antes de repetir BFS/DFS/camino en esa sesión. Las pruebas automatizadas de esas funcionalidades sí pasaron.
- La revisión del navegador midió overflow y contraste de colores representativos; no fue una auditoría automatizada completa WCAG.

## Hallazgos

### QA-06-01 - IDNA 2003 consulta un dominio diferente

- **Severidad:** ALTO
- **Componente:** aplicación, consulta DNS y preparación de incorporación.
- **Evidencia:** [dns_lookup.py](../../app/application/dns_lookup.py), función `normalizar_dominio` y conversión con el codec estándar `idna`. La forma unicode `straße.de` se convierte en `strasse.de`; la forma A-label `xn--strae-oqa.de` se conserva como `xn--strae-oqa.de`.
- **Pasos de reproducción:** llamar `normalizar_dominio("straße.de")` y `normalizar_dominio("xn--strae-oqa.de")`. Resultado real: `strasse.de` y `xn--strae-oqa.de`, respectivamente. `DnsLookupService` consulta al proveedor con el primer resultado; por tanto, el usuario que ingresa el nombre Unicode puede recibir registros de otro dominio.
- **Resultado esperado:** consultar el nombre DNS equivalente al texto ingresado, o rechazarlo explícitamente si la implementación no puede representarlo sin ambigüedad.
- **Resultado real:** la consulta se completa con un nombre distinto sin advertencia.
- **Responsable:** Agente 03.
- **Prueba necesaria:** prueba unitaria con proveedor falso que capture el QNAME para `straße.de`, `strasse.de` y `xn--strae-oqa.de`, y prueba de API del comportamiento acordado. Verificar además que la incorporación no guarde evidencia para un dominio distinto del consultado.
- **Mitigación mínima viable:** sin dependencia ni cambio global del CRUD, rechazar explícitamente `ß` Unicode en el flujo DNS de consulta e incorporación hasta acordar soporte IDNA 2008; conservar la aceptación del A-label válido. Esta mitigación cubre el caso reproducido, no demuestra compatibilidad IDNA 2008 general. No declarar P-06 resuelto hasta implementar y probar una política completa.
- **Nota documental:** P-06 afirma que el A-label IDNA 2008 no se decodifica. En el código actual se conserva sin cambios; el defecto confirmado es que queda distinto de la conversión de `straße.de`.

### QA-06-02 - Reconstrucciones concurrentes pueden dejar un grafo obsoleto

- **Severidad:** ALTO
- **Componente:** aplicación, publicación de la proyección en memoria.
- **Evidencia:** [service.py](../../app/application/service.py), `GraphApplicationService._refresh_after_write`: carga un candidato y asigna `_graph` sin exclusión mutua ni control de generación. [database.py](../../app/persistence/database.py) serializa las escrituras con `BEGIN IMMEDIATE`, pero ese bloqueo termina antes de publicar la proyección.
- **Pasos de reproducción:** en SQLite temporal, lanzar dos incorporaciones en hilos. Pausar la primera después de que su loader lea la base y antes de devolver el grafo; permitir que la segunda escriba y publique el grafo actualizado; luego liberar la primera. Reproducción determinista ejecutada: SQLite terminó con 3 entidades, la segunda entidad estaba visible tras la segunda escritura y dejó de estarlo después de que la primera publicara su snapshot viejo.
- **Resultado esperado:** después de ambas respuestas exitosas, el grafo en memoria representa todos los datos confirmados en SQLite, independientemente del orden de finalización de las reconstrucciones.
- **Resultado real:** una reconstrucción antigua puede sobrescribir una más reciente; operaciones posteriores que usan el grafo pueden observar datos ausentes hasta una actualización manual.
- **Responsable:** Agente 03.
- **Prueba necesaria:** prueba de aplicación con dos incorporaciones concurrentes y barreras deterministas entre lectura y publicación; comprobar que el grafo final contiene todas las entidades, relaciones y evidencias confirmadas y coincide con una reconstrucción desde SQLite. Incluir la misma protección para las escrituras CRUD que comparten `GraphApplicationService`.

### QA-06-03 - Duplicados Unicode/punycode preexistentes bloquean la incorporación

- **Severidad:** MEDIO
- **Componente:** CRUD y búsqueda de entidades en persistencia.
- **Evidencia:** P-05 en [DECISIONS.md](DECISIONS.md); [incorporacion_dns.py](../../app/persistence/incorporacion_dns.py) detecta varias coincidencias canónicas y falla de forma segura.
- **Pasos de reproducción:** crear por CRUD un DOMINIO `münchen.de` y otro `xn--mnchen-3ya.de`; ambas solicitudes devuelven 201. Incorporar luego el dominio punycode devuelve 409 con las dos entidades coincidentes y no escribe el lote.
- **Resultado esperado:** el CRUD no debería permitir representaciones duplicadas equivalentes, o el proyecto debería documentar y ofrecer una resolución de los datos heredados.
- **Resultado real:** las dos entidades pueden existir; la incorporación se detiene con conflicto explícito y sin escritura parcial.
- **Responsable:** Agentes 03 y 04, después de la decisión de alcance del usuario sobre P-05.
- **Prueba necesaria:** con la política aprobada, prueba API que impida crear el segundo equivalente y prueba de migración/diagnóstico para datos ya duplicados. No cambiar la normalización global en esta auditoría.

## Resultados

### Pruebas automatizadas

- `.\.venv\Scripts\python.exe -m pytest -q`: **257 passed, 1 skipped**, 21.85 s.
- La suite incluye la repetición idempotente del lote, rollback por ambigüedad de IP después de crear el dominio, bloqueo en `BEGIN IMMEDIATE`, bloqueo al commit y recuperación, concurrencia de dos sesiones en persistencia y liberación de conexiones. Estas pruebas detectan fallos transaccionales de persistencia, pero no la carrera de publicación del grafo de QA-06-02.
- No se añadieron pruebas automatizadas durante esta auditoría. La reproducción de QA-06-02 se ejecutó con un script temporal, sin crear archivos en el repositorio.

### Navegador y frontend

Se ejecutó la app local con `MMG_DATABASE_PATH` apuntando a SQLite temporal. Las respuestas DNS se simularon con interceptación; la incorporación exitosa y el bloqueo SQLite usaron el backend local.

- Camino feliz: 2 registros A y 1 AAAA revisados; CNAME, MX y NS no seleccionables; confirmación con foco; doble activación produjo una solicitud; respuesta creó 3 IP, 3 relaciones y 3 evidencias; grafo actualizado a 4 entidades y 3 relaciones.
- Cancelar y Escape: no enviaron solicitudes y devolvieron el foco al botón de revisión. Se probaron Espacio y Enter para operar los controles.
- HTTP 422 y 409 simulados: conservaron selección y permitieron corregir o revisar.
- HTTP 503 SQLite ocupado: bloqueo real de la base temporal; la interfaz informó que el lote no se aplicó y permitió reintentar.
- HTTP 503 con `persistencia: confirmada`: simulación de respuesta; indicó que los datos se guardaron, bloqueó el reenvío y ofreció actualizar el grafo.
- Error de red, timeout acelerado para la prueba, JSON malformado y forma JSON inválida: mostraron el estado incierto o el error de consulta apropiado y devolvieron el foco.
- Nueva consulta: descartó revisión y selección previas. `sessionStorage` restauró la selección/revisión tras recargar la misma pestaña.
- Tras incorporar, el grafo se actualizó; una actualización manual posterior conservó la selección del inspector y el layout Círculo, persistido en `localStorage`.
- Valores DNS maliciosos de prueba se mostraron como texto; no crearon elementos `img`/`svg` ni ejecutaron el manejador simulado.
- Los avisos de consola de HTTP 4xx/5xx y solicitudes abortadas procedían de las respuestas de error deliberadamente simuladas. No se observó una excepción JavaScript no controlada.

La heurística de duplicados sigue siendo orientativa: un registro recién incorporado se marca como “Incorporado” y también puede mostrar “Posible duplicado” porque ya existe en el grafo. No se considera corrupción de datos; conviene decidir si se aclara el texto antes de una demostración académica.

### Calidad, seguridad y regresiones

- `.\.venv\Scripts\python.exe -m ruff check .`: sin errores.
- `.\.venv\Scripts\python.exe -m ruff format --check .`: código 1; 21 archivos podrían reformatearse y 71 ya están formateados. El formato es no bloqueante según la configuración del proyecto; no se reformateó trabajo ajeno.
- `.\.venv\Scripts\python.exe -m bandit -c bandit.yaml -r app`: sin hallazgos.
- `.\.venv\Scripts\python.exe -m bandit -c bandit.yaml -r tests -s B101`: sin hallazgos.
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas.
- `node --check` para `app.js`, `osint.js`, `osint-incorporacion.js`, `osint_incorporacion_harness.js` y `frontend_refresh_harness.js`: todos con código 0.
- `pip-audit` no ejecutado, por la prohibición de consultar Internet.
- Se comprobó el contrato de consulta por tipo, estados, fuente/fecha, prioridad MX, marcas de revisión, aviso de duplicados, limpiar, nueva consulta, timeout, errores HTTP y respuestas malformadas. La selección de A/AAAA, escape, foco, persistencia temporal y manejo de errores no mostró una regresión reproducible.
- CRUD de entidades/relaciones, grafo, layouts, contadores y algoritmos cubiertos por la suite completa. La actualización posterior a la incorporación se verificó en navegador.

## Riesgos aceptados

- La fuente y la fecha se declaran por el cliente. La API y la interfaz lo indican; no son evidencia de que el proveedor DNS haya sido consultado por el servidor.
- P-05 continúa pendiente de decisión global. Mientras existan representaciones duplicadas, la incorporación responde 409 de forma segura.
- P-06 continúa abierto y es un hallazgo ALTO, no una limitación ya resuelta.
- El navegador no se probó en múltiples procesos, con WAL, durante reinicio del servidor ni con una base de gran tamaño.
- `pip-audit` queda pendiente de un entorno donde se autorice la consulta de vulnerabilidades; no se puede afirmar que las dependencias estén libres de vulnerabilidades conocidas.
- El indicador posterior “Posible duplicado” se basa en la existencia actual de la entidad y no distingue por sí solo que el registro acaba de incorporarse.
- No se ejecutó CI en GitHub. La preparación de publicación requiere resolver los dos hallazgos ALTO y repetir las verificaciones permitidas.

## Recomendaciones por agente

- **Agente 03:** corregir QA-06-01 sin introducir dependencias ni cambiar el CRUD global; corregir QA-06-02 para impedir que una reconstrucción vieja sobrescriba el estado reciente; agregar pruebas deterministas. Revisar la nota de P-06.
- **Agente 04:** coordinar con Agente 03 la consistencia de canonicalización y, solo después de decisión sobre P-05, proponer control del CRUD y resolución de datos duplicados. No cambiar el esquema sin autorización.
- **Agente 05:** no se requiere corrección funcional urgente en `osint.js` por esta auditoría. Considerar ajustar el texto del aviso de duplicado para diferenciar una entidad recién incorporada.
- **Agente 07:** esperar la corrección y reauditoría antes de afirmar en el manual que el flujo DNS está listo para publicación.

## Veredicto

**REQUIERE CORRECCIONES.** No cerrar la versión ni afirmar que la incorporación DNS está lista para publicación hasta corregir QA-06-01 y QA-06-02 y ejecutar las pruebas de confirmación. P-05 puede permanecer como riesgo documentado si se acepta el conflicto seguro 409; P-06 no.

## Reauditoría final (2026-11-18)

### Veredicto único

**REQUIERE CORRECCIONES.** La corrección de publicación del grafo queda verificada dentro de un proceso y QA-06-03 puede aceptarse como riesgo documentado para esta versión académica. Sin embargo, la mitigación IDNA no cubre la `İ` mayúscula y las capas aceptan A-labels `xn--` inválidas. Las pruebas de reproducción agregadas fallan de forma reproducible. No aprobar aún la publicación.

### QA-06-01 - Mitigación parcial, no cerrado

- **Estado final:** el caso original `straße.de` está mitigado, pero la política D-20 tiene una vía de evasión, por lo que el hallazgo sigue abierto.
- **Evidencia:** `normalizar_dominio()` en [dns_lookup.py](../../app/application/dns_lookup.py) aplica `lower()` antes de llamar `convertir_dominio()`. [canonizar_dominio()](../../app/persistence/incorporacion_dns.py) hace lo mismo. Así, la `İ` mayúscula se convierte primero en `i` más punto combinante y ya no llega a la regla que debería rechazar el cambio de longitud.
- **Reproducción:** `normalizar_dominio("\u0130stanbul.tr")` y `canonizar_dominio("\u0130stanbul.tr")` devuelven `xn--istanbul-o0e.tr`. La consulta API con proveedor falso respondió 200 y llegó al proveedor; la incorporación API respondió 200 y creó DOMINIO, IP, relación y evidencia. Ambas deberían responder 422 antes del proveedor o de SQLite.
- **Verificación que sí pasó:** `straße.de` se rechaza con 422, sin proveedor ni escrituras. `strasse.de` permanece diferente; `münchen.de`, su forma descompuesta y mayúsculas aceptadas se canonicalizan; `xn--strae-oqa.de` se preserva y se consulta tal cual.
- **Pruebas:** las pruebas previas de Agente 03 para `ß`, transformaciones Unicode listadas, formas válidas de München y A-label válida pasaron. Las nuevas reproducciones para `İ` fallan en aplicación, persistencia, consulta API e incorporación API.
- **Limitación y riesgo residual:** no hay soporte general de IDNA 2008. La normalización previa permite una transformación no declarada y puede consultar o persistir un nombre distinto.
- **¿Impide publicar?:** sí, hasta rechazar la entrada antes de cualquier consulta o escritura y verificar el 422 coherente.
- **Responsable:** Agente 03. Agente 04 debe revisar la corrección en `canonizar_dominio`, sin modificar el CRUD global.

### QA-06-02 - Corregido dentro de un proceso

- **Estado final:** verificado para un único proceso, que es el modo de ejecución documentado.
- **Evidencia:** [service.py](../../app/application/service.py) usa `_PUBLICACION_GRAFO`, de módulo, para cubrir carga y publicación en `reconstruir_grafo()` y `_refresh_after_write()`. Los métodos CRUD refrescan por ese camino y [main.py](../../app/api/main.py) conecta la incorporación DNS con `graph_service.refrescar_tras_escritura`.
- **Pruebas:** las seis pruebas de [test_concurrencia_grafo.py](../../tests/application/test_concurrencia_grafo.py) pasaron. Cubren snapshot viejo, fallo de reconstrucción, CRUD junto con incorporación, escrituras CRUD simultáneas, lotes idénticos y dos instancias del servicio. Se comparan entidades, relaciones y evidencias del grafo con SQLite; también se comprueban reutilización y no duplicación. BFS y camino se verifican en el escenario concurrente; BFS, DFS y camino pasan además en la suite.
- **Commit durante la reconstrucción:** una escritura puede confirmar mientras otra reconstrucción posee el cerrojo, porque el commit precede a la publicación. Su refresco espera el cerrojo y vuelve a cargar después, por lo que el estado final incluye ambos commits.
- **Fallo y recuperación:** si falla la carga, el servicio invalida `_graph` y propaga el error; la siguiente reconstrucción/escritura puede recuperarlo. El test API verifica 503 con `persistencia: confirmada` tras el commit y que el lote no se reenvíe para recuperarlo.
- **Calidad de las pruebas:** se corrigió una aserción tautológica en el test de lotes idénticos y se amplió la igualdad grafo/SQLite para incluir evidencias. La comprobación negativa de espera todavía usa un timeout de 0,3 s; una demora de planificación podría producir un falso positivo en la aserción de bloqueo, aunque la comparación final y los `join` acotados aportan comprobaciones adicionales. No se detectaron bloqueos permanentes en las ejecuciones.
- **Limitación y riesgo residual:** el cerrojo solo coordina hilos del mismo proceso. Con varios workers/procesos, cada uno conserva su grafo. Los comandos de ejecución revisados en [README.md](../../README.md), [frontend.md](../frontend.md) y [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) no usan `--workers`, así que mantienen el modo admitido.
- **¿Impide publicar?:** no, si la ejecución sigue siendo de un solo proceso. La garantía multiproceso queda expresamente fuera de alcance.

### QA-06-03 - Riesgo conocido aceptable para esta versión académica

- **Estado final:** no corregido en el CRUD; riesgo documentado con salvaguarda.
- **Evidencia:** la prueba API crea `münchen.de` y `xn--mnchen-3ya.de` por CRUD, ambos con 201. La incorporación devuelve 409 con el conflicto de equivalencia; no elige una entidad. No crea relaciones ni entidades adicionales. Las pruebas de persistencia también verifican rollback ante ambigüedad y que no se guarde un lote parcial.
- **Pruebas:** `test_crud_con_unicode_y_punycode_equivalentes_responde_409_sin_escribir` y las pruebas de ambigüedad/rollback de `test_incorporacion_dns.py`.
- **Limitación y riesgo residual:** los CRUD manuales siguen permitiendo representaciones equivalentes. El usuario debe resolver el conflicto de forma explícita; P-05 continúa pendiente como política global.
- **¿Impide publicar?:** no para esta versión académica, bajo la condición de documentar que la incorporación se detiene con 409. No se afirma que el CRUD esté corregido.

### QA-06-04 - A-label `xn--` malformada aceptada

- **Severidad:** MEDIO
- **Estado final:** defecto nuevo, reproducido en dominio, aplicación, persistencia y API.
- **Evidencia:** [convertir_dominio()](../../app/domain/nombres_dns.py) retorna sin validar cualquier etiqueta ASCII. `normalizar_dominio()` y `canonizar_dominio()` aceptan `xn--bogus.de` y `xn--invalid-zz.de`; al decodificar esos prefijos con el codec IDNA estándar se produce error de ida y vuelta o de Punycode.
- **Reproducción:** la consulta API con proveedor falso devuelve 200 y `sin_registros` en vez de 422. La incorporación devuelve 200 y persiste dominio, IP, relación y evidencia, en vez de rechazar el lote antes de SQLite.
- **Pruebas:** se agregaron pruebas de reproducción en [test_dns_lookup.py](../../tests/application/test_dns_lookup.py), [test_dns_idna_api.py](../../tests/api/test_dns_idna_api.py) y [test_incorporacion_dns.py](../../tests/persistence/test_incorporacion_dns.py). Las seis pruebas API y las seis comprobaciones de aplicación/persistencia fallan contra el comportamiento actual.
- **Limitación y riesgo residual:** la validación debe distinguir A-labels válidas, incluyendo `xn--strae-oqa.de` que se conserva sin reinterpretar con IDNA 2003, de cargas Punycode malformadas o inválidas. No implementar IDNA 2008 ni agregar dependencias como parte de esta corrección.
- **¿Impide publicar?:** sí, hasta rechazar A-labels inválidas con 422 en consulta e incorporación, sin llamadas al proveedor ni escrituras.
- **Responsables:** Agente 03 para la política compartida; Agente 04 para validar que el límite de persistencia aplique la misma regla.

### Resultados de la reauditoría

- Suite completa, con las pruebas nuevas de reproducción: `.\.venv\Scripts\python.exe -m pytest -q`: **293 passed, 1 skipped, 12 failed**. Las 12 fallidas corresponden exclusivamente a las reproducciones nuevas de `İ` y A-labels inválidas. La prueba de red opt-in quedó omitida; `MMG_RUN_NETWORK_TESTS` no estaba definido.
- Suite enfocada anterior a las nuevas reproducciones: `.\.venv\Scripts\python.exe -m pytest -q tests/domain/test_nombres_dns.py tests/api/test_dns_idna_api.py tests/application/test_concurrencia_grafo.py tests/persistence/test_incorporacion_dns.py tests/application/test_incorporacion_servicio_dns.py`: **116 passed**.
- Suite enfocada con las reproducciones y pruebas API de incorporación: **183 passed, 12 failed**. Las seis pruebas de concurrencia pasan.
- `.\.venv\Scripts\python.exe -m ruff check .`: sin errores.
- `.\.venv\Scripts\python.exe -m ruff format --check .`: código 1; **23 files would be reformatted, 74 files already formatted**. Es informativo/no bloqueante y no se reformatearon archivos ajenos.
- Bandit en `app` y `tests` con `-s B101`: sin hallazgos; Bandit emitió avisos de palabras en comentarios, no hallazgos.
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas.
- `node --check` para `app.js`, `osint.js`, `osint-incorporacion.js` y los dos harnesses: código 0.
- Formato Ruff acotado a los tres archivos de pruebas IDNA modificados: código 1 por formato pendiente en estos archivos, que ya contenían secciones previas no formateadas. No se reformateó trabajo de otros agentes. La regla de formato del proyecto es informativa/no bloqueante.
- `pip-audit` no ejecutado: no se consultó Internet.
- No se ejecutó navegador: los cambios auditados no afectan la interfaz.
- No hay cambios en manifiestos de dependencias ni en `app/persistence/schema.py`; no se cambió el esquema.
- La base opt-in de navegador de la auditoría anterior ya no existe, el puerto 8765 no tiene listener y no se usó la base principal.

### Estado del workspace

- `git -c core.whitespace=cr-at-eol diff --check`: código 0. No se encontraron espacios finales en los tres documentos de auditoría/handoff/backlog.
- `git status --short --untracked-files=all` muestra cambios previos de otros agentes y archivos nuevos de la entrega. No se descartó ni sobrescribió ninguno.
- No aparecen archivos `.env`, bases SQLite/DB, logs ni nombres temporales entre los archivos no versionados. `.claude/` y `.codex/` contienen instrucciones y skills de agentes sin nombres de credenciales; conviene revisar su alcance local antes de decidir versionarlos.
- `tests/network/test_dns_google_real.py` es una prueba opt-in para Google DoH, no un artefacto temporal. Quedó omitida con `MMG_RUN_NETWORK_TESTS` sin definir y no se ejecutó ningún servicio OSINT real.
- Los documentos de coordinación y las pruebas añadidas aparecen como no versionados en el estado actual. No hubo commit, pull ni push.

### Archivos de esta reauditoría

- Documentación: `docs/agents/auditoria-integral-dns.md`, `docs/agents/HANDOFF.md`, `docs/agents/BACKLOG.md`.
- Pruebas: `tests/application/test_dns_lookup.py`, `tests/api/test_dns_idna_api.py`, `tests/persistence/test_incorporacion_dns.py` y `tests/application/test_concurrencia_grafo.py`.
- Sin cambios funcionales, de esquema o dependencias. Sin commit, pull ni push.

### Recomendación final

No pasar todavía a aprobación técnica de publicación. Agente 03 debe cerrar QA-06-01 residual y QA-06-04, con pruebas que demuestren 422 antes de proveedor/SQLite y con aceptación de `münchen.de` y `xn--strae-oqa.de`. Agente 04 debe revisar la misma política en persistencia. QA-06-02 puede darse por corregido para un proceso; QA-06-03 puede documentarse como riesgo aceptado. La elaboración del manual con capturas y la presentación oral pueden continuar como preparación, pero no deben declarar cerrada ni aprobada la versión hasta que las pruebas nuevas pasen.

## Verificación final del 2026-11-18

### Veredicto vigente: APROBADO CON OBSERVACIONES

La versión puede pasar a la elaboración del manual con capturas reales, la presentación oral y la actualización documental, y puede prepararse para su publicación académica manual. No se verificó un despliegue público ni se hizo commit o push.

### Estado final de los hallazgos

| Hallazgo | Estado verificado | Observaciones |
|---|---|---|
| QA-06-01 | Corregido para las transformaciones comprendidas en D-20 | La política recibe el texto original antes de convertir a minúsculas. `İstanbul.tr`, `straße.de` y los casos peligrosos probados se rechazan. P-06 sigue abierto: no se implementó IDNA 2008 completo. |
| QA-06-02 | Corregido para un proceso y una instancia de aplicación | El cerrojo cubre la carga y publicación del grafo. Las seis pruebas de concurrencia pasan; varias instancias conservan sus propios grafos y varios procesos no se sincronizan. |
| QA-06-03 | Riesgo conocido, no corregido en el CRUD | Las representaciones Unicode y punycode equivalentes pueden coexistir. La incorporación ambigua responde 409 sin elegir ni escribir parcialmente; P-05 sigue pendiente. |
| QA-06-04 | Corregido para las A-label inválidas y la política limitada verificadas | `xn--bogus.de`, `xn--invalid-zz.de` y `xn--a.com` se rechazan. `xn--mnchen-3ya.de` y `xn--strae-oqa.de` se conservan. |

Las 12 reproducciones agregadas por QA se mantienen con sus aserciones originales y pasan. Las pruebas API usan proveedor falso o bloquean el transporte, verifican 422 y comprueban que no se creen entidades ni relaciones. Las pruebas de persistencia también verifican que no se escriban evidencias. Unicode válido, incluidas `münchen.de`, `MÜNCHEN.de` y la forma descompuesta de `ü`, conserva su forma canónica esperada.

La revisión del cambio en `canonizar_dominio` confirma que delega en la misma regla del dominio antes de abrir la transacción, sin modificar la búsqueda, `BEGIN IMMEDIATE`, rollback, reutilización ni el contrato del repositorio. La suite dirigida cubre conflictos, rollback e idempotencia. **No se necesita otra intervención del Agente 04 para esta corrección.** Una futura política global para P-05 requeriría una decisión separada.

### Pruebas y controles

Para cada ejecución de pytest se definió `MMG_RUN_NETWORK_TESTS=0` y `MMG_DATABASE_PATH` en un archivo temporal exclusivo; los fixtures emplearon además sus propias bases temporales. No se consultaron servicios OSINT reales.

- `.\.venv\Scripts\python.exe -m pytest -q`: **368 passed, 1 skipped in 21.86s**. La omitida es la prueba opt-in de Google DoH.
- `.\.venv\Scripts\python.exe -m pytest -q tests\application\test_dns_lookup.py::test_i_con_punto_y_a_labels_invalidas_se_rechazan_antes_de_consultar tests\api\test_dns_idna_api.py::test_consulta_rechaza_i_con_punto_y_a_labels_invalidas_sin_llamar_proveedor tests\api\test_dns_idna_api.py::test_incorporacion_rechaza_i_con_punto_y_a_labels_invalidas_sin_escribir tests\persistence\test_incorporacion_dns.py::test_canonizacion_rechaza_i_con_punto_y_a_labels_invalidas`: **12 passed in 1.98s**.
- Política DNS, aplicación, API, persistencia y concurrencia: **267 passed in 14.76s**, con `.\.venv\Scripts\python.exe -m pytest -q tests\domain\test_nombres_dns.py tests\application\test_dns_lookup.py tests\application\test_incorporacion_servicio_dns.py tests\api\test_dns_api.py tests\api\test_dns_idna_api.py tests\api\test_incorporacion_dns_api.py tests\persistence\test_politica_idna_coherente.py tests\persistence\test_incorporacion_dns.py tests\application\test_concurrencia_grafo.py`.
- `.\.venv\Scripts\python.exe -m pytest -q tests\application\test_concurrencia_grafo.py`: **6 passed in 2.91s**. CRUD, BFS, DFS y camino también pasan en la suite completa.
- `.\.venv\Scripts\python.exe -m ruff check .`: sin errores.
- `.\.venv\Scripts\python.exe -m bandit -q -c bandit.yaml -r app` y `.\.venv\Scripts\python.exe -m bandit -q -c bandit.yaml -r tests -s B101`: código 0, sin hallazgos; en `tests` hubo avisos del gestor sobre palabras en comentarios.
- `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas.
- `git -c core.whitespace=cr-at-eol diff --check`: código 0. Este control no incluye los archivos sin seguimiento; se revisó también el espacio final en los documentos editados.
- Arranque local de `python -m uvicorn app.api.main:app --host 127.0.0.1 --port <puerto temporal>` con `MMG_DATABASE_PATH` aislada: `/health` respondió 200 y `{"status":"ok"}`. Se detuvo el proceso de prueba.
- No se ejecutó `pip-audit` ni la prueba de red: no se autorizó consultar Internet. No se repitió la auditoría de navegador de la etapa anterior.

### Observaciones para el cierre

- P-06 sigue abierto: no se promete compatibilidad completa con IDNA 2008 ni validez universal ante registros externos.
- P-05 sigue abierto: si existen dominios equivalentes, el usuario debe resolver el conflicto 409 antes de incorporar.
- Ejecutar una sola instancia de la aplicación en un solo proceso; no usar múltiples workers ni modificar la base externamente mientras se utiliza el grafo.
- La fuente y la fecha DNS son declaradas por el cliente, no verificadas por el servidor. Solo A y AAAA se incorporan; CNAME, MX y NS son vista previa.
- Tras un resultado incierto o un 503 con persistencia confirmada, usar la recuperación que ofrece la interfaz antes de otro envío. La heurística puede señalar un registro recién incorporado como posible duplicado.
- La base real `data/mmg.sqlite3` y el entorno `.venv` están ignorados. Los archivos DNS nuevos y la documentación de agentes están presentes pero sin seguimiento; deben incluirse deliberadamente en el cierre manual. Revisar `.claude/` y `.codex/` antes de decidir versionarlos.
- `requirements.txt`, `requirements-dev.txt` y `app/persistence/schema.py` no muestran cambios frente a Git. El resultado de `pip check` no sustituye una auditoría de vulnerabilidades.
