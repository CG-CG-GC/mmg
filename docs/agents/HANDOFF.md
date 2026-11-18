# Entregas entre agentes

Las entregas más recientes van primero. No se copian conversaciones: solo datos
verificables. Reglas en [README.md](README.md).

## Plantilla

```markdown
### AAAA-MM-DD · Agente XX → Agente YY · Título breve

- **Estado:** pendiente | en curso | listo para revisión | aprobado | requiere correcciones
- **Objetivo:**
- **Archivos modificados:**
- **Contratos o decisiones relevantes:**
- **Pruebas ejecutadas y resultados:** comando exacto y resultado real
- **No probado:**
- **Pendientes, riesgos y bloqueos:**
```

## Entregas

### 2026-11-18 · Agente 07 → Agente 06 (copia a 03 y 04) · Demostración personal aislada

- **Estado:** listo para revisión
- **Objetivo:** preparar una base privada reutilizable para la presentación sin modificar el esquema, el arranque normal, los algoritmos ni la base principal.
- **Archivos creados:** `scripts/preparar_demo_personal.py` lee un perfil JSON externo, valida las URL y crea una base fuera del repositorio; `tests/scripts/test_preparar_demo_personal.py` comprueba el grafo sembrado y el rechazo de sobrescritura.
- **Archivos actualizados:** `README.md` documenta el uso de la herramienta y la separación de datos personales.
- **Datos privados:** el perfil, las instrucciones de presentación y la base SQLite están en `%LOCALAPPDATA%\MiniMaltego\demo-personal`; ninguno se guarda en el repositorio. No se crearon capturas personales.
- **Grafo inicial verificado:** la base privada final quedó limpia con 7 entidades, 6 relaciones y 0 evidencias. No hay ORGANIZACION ISETA ni direcciones IP personales; se usaron los tipos y relaciones existentes.
- **Pruebas ejecutadas:** `.\.venv\Scripts\python.exe -m pytest -q` → **370 passed, 1 skipped**; `.\.venv\Scripts\python.exe -m pytest -q tests\scripts\test_preparar_demo_personal.py` → **2 passed**; `.\.venv\Scripts\python.exe -m ruff check .` → **All checks passed**; Ruff format check de ambos archivos nuevos → **2 files already formatted**; Bandit `-q -c bandit.yaml -r app scripts` → código 0, sin hallazgos.
- **Servidor y navegador:** con una instancia de Uvicorn y la variable `MMG_DATABASE_PATH`, `/health` respondió `ok`, `/` y `/static/app.js` respondieron 200, y el navegador mostró 7 entidades y 6 relaciones sin errores de página. BFS y DFS recorrieron 7 entidades; camino a `github.com` de 3 relaciones y a `iseta.edu.ar` de 2.
- **DNS offline:** se interceptó solo `POST /api/v1/osint/dns` en el navegador con respuesta sintética `simulacion-demo-sin-red` y direcciones reservadas. La incorporación usó la API y SQLite locales: primera ejecución creó 1 dominio, 2 IP, 2 relaciones y 2 evidencias; la repetición reutilizó todos sin aumentar los totales. Luego se volvió a preparar la base privada limpia para que la exposición comience con el grafo personal.
- **Persistencia y aislamiento:** tras detener y reiniciar el servidor con la base privada limpia, `/health` respondió `ok` y persistieron 7 entidades y 6 relaciones. SHA256 de `data/mmg.sqlite3` antes y después: `052ECE35185A7043FE46ED9EC7B4CA98700FC550E06AB725DFF5D283D2131293`.
- **Restricciones:** no se modificaron funcionalidades de producción, dependencias, esquema ni base principal. No se realizaron operaciones de Git que alteren índice o historial.
- **Publicación:** incluir `README.md`, `scripts/preparar_demo_personal.py`, `tests/scripts/test_preparar_demo_personal.py` junto con los archivos públicos previamente pendientes en `app`, `docs`, `scripts` y `tests`. Excluir `.claude/`, `.codex/`, `.venv/`, `data/` y todo el directorio privado de `%LOCALAPPDATA%`.
- **Estado Git observado:** rama `feature/project-expansion`, dos commits locales por delante de `origin/feature/project-expansion`; índice vacío. La integración con `main` queda para el usuario, preferentemente mediante PR revisado y CI.

### 2026-11-18 · Agente 07 → Agente 06 (copia a 03, 04 y 05) · Documentación final, manual visual y guion de defensa

- **Estado:** listo para revisión
- **Objetivo:** manual de usuario con capturas reales, demostración reproducible, guion oral y actualización de la documentación técnica, sobre la versión aprobada con observaciones por el Agente 06. Sin cambios de código funcional, dependencias ni esquema SQLite.
- **Archivos creados:**
  - `docs/manual-usuario.md` (28 secciones, instalación en Windows con VS Code, errores frecuentes, limitaciones y glosario).
  - `docs/img/manual/01-pantalla-principal.png` a `24-api-relacion-con-evidencias.png` (24 capturas tomadas de la interfaz en navegador).
  - `docs/presentacion-oral.md` (guion de 10 a 15 minutos, preparación para preguntas, definiciones, diferencias BFS y DFS, esquema de 10 diapositivas).
  - `docs/demo-presentacion.md` (17 pasos con entradas exactas, resultados esperados y plan alternativo).
  - `docs/demo/respuesta-dns-simulada.json` (respuesta simulada usada solo para las capturas; marcada con la fuente `simulacion-demo-sin-red`).
  - `scripts/preparar_demo.py` (crea una base nueva con datos ficticios; se niega a sobrescribir un archivo existente y a usar `data/mmg.sqlite3`).
- **Archivos actualizados:** `README.md` (alcance corregido, instalación, sección de demostración, enlaces), `docs/mvp-academico.md` (tabla de API con PUT y OSINT, trazabilidad, 368 pruebas, limitaciones), `docs/frontend.md` (edición por PUT, confirmación previa, sin buscador), `docs/agents/DECISIONS.md` (D-22, P-07), `docs/agents/BACKLOG.md`, `docs/agents/HANDOFF.md`.
- **Correcciones de contradicciones verificadas con el código:** el README y la guía del MVP decían que no había edición de entidades ni relaciones; la API tiene `PUT` y la interfaz edita en línea. La guía decía 61 pruebas; la verificación actual es 368 aprobadas y 1 omitida.
- **Contratos o decisiones relevantes:** D-22 (demostraciones con base aislada y respuesta DNS simulada identificada). P-07 (DFS recursivo, pendiente de decisión). No se cambió D-16 a D-21.
- **Pruebas ejecutadas y resultados:**
  - `.\.venv\Scripts\python.exe -m pytest -q`: **368 passed, 1 skipped in 21.44s** (ejecutada dos veces, la última tras los cambios documentales).
  - `.\.venv\Scripts\python.exe -m ruff check .`: **All checks passed!**
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts`: **ya formateado** (se formateó solo `scripts/preparar_demo.py`, archivo nuevo).
  - `.\.venv\Scripts\python.exe -m bandit -q -c bandit.yaml -r app scripts`: código 0, sin hallazgos.
  - `.\.venv\Scripts\python.exe -m pip check`: **No broken requirements found.**
  - `git -c core.whitespace=cr-at-eol diff --check`: código 0.
  - `.\.venv\Scripts\python.exe scripts\preparar_demo.py`: base nueva creada (9 entidades, 9 relaciones, 2 evidencias). Segunda ejecución con la misma ruta: rechazada con código 1. Ruta `data\mmg.sqlite3`: rechazada con código 1.
  - Servidor con `uvicorn app.api.main:app` sobre la base de demo: `/health` → `{"status":"ok"}`; `/`, `/static/app.js`, `/static/osint.js`, `/static/vendor/cytoscape.min.js`, `/static/styles.css`, `/docs` y `/openapi.json` respondieron 200.
  - Recorrido en navegador (Playwright) con 24 capturas: creación de entidad (409 ante duplicado), creación y edición de relación, inspección, cinco layouts, BFS, DFS, camino (3 relaciones; sin camino en sentido inverso), consulta DNS con respuesta simulada, revisión A/AAAA, confirmación, resultado de incorporación y grafo actualizado.
  - API: la incorporación repetida del mismo lote responde `reutilizada` en dominio, entidad, relación y evidencia; el total de entidades se mantiene en 12.
  - Verificación de DFS con una cadena de nodos en el dominio (sin base de datos): 500, 900 y 3000 nodos BFS OK; DFS OK hasta 900 y `RecursionError` en 1200 y 3000.
  - Activación del entorno: `Activate.ps1` bloqueado con la política por defecto de este equipo; funciona con `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` en la misma ventana.
- **Hallazgos para otros agentes:**
  - Agente 03 y 06 (P-07): DFS recursivo, `RecursionError` en cadenas de ~1000 nodos. La API lo propagaría como error no controlado; no se probó el código HTTP resultante.
  - Agente 05: la inspección de relaciones muestra solo el número de evidencias; y el mensaje de error del CRUD agrega "Si el servidor falló después de guardar..." también ante un 409 sin escritura (ver BACKLOG).
- **No probado:**
  - Consulta DNS real: no se consultó Internet. Las capturas de DNS usan una respuesta simulada interceptada en el navegador. El modo "sin red" de la demo se describe según el código, no se verificó.
  - `pip-audit` (no ejecutado en esta entrega).
  - Creación de un `.venv` nuevo desde cero (se usó el existente; `pip check` verde).
  - Navegadores distintos de uno basado en Chromium.
  - Interacción con el grafo por clic directo en el canvas de Cytoscape (se usaron las listas y los botones).
  - Ejecución de la prueba de red (`MMG_RUN_NETWORK_TESTS=1`).
- **Pendientes, riesgos y bloqueos:**
  - Las capturas 01 a 16 se tomaron en la misma ventana del navegador, pero el tamaño de viewport no fue fijo en todas las llamadas (la herramienta lo reiniciaba). El diseño es adaptable; las capturas son legibles, pero no son una serie con viewport idéntico.
  - Los identificadores de la demo (`#1`, `#8`, `#10`) son los de una base nueva creada por el script.
  - La captura 24 muestra la respuesta JSON de la API sin el formato del navegador.
  - Los archivos `.claude/`, `.codex/`, `docs/agents/agent-05-frontend.md` y los cambios de otros agentes no fueron tocados ni incluidos en esta entrega. Los documentos `docs/mvp-academico.md` y `docs/frontend.md` ya tenían cambios sin commit de otros agentes; se editaron sobre esos cambios sin revertirlos.
  - Regla de antislop: el skill se cargó y se aplicó como filtro de texto (sin rayas largas ni frases genéricas). Su modo (durante/después) no quedó definido; no se preguntó porque la tarea pedía una sola intervención.
- **Archivos para la futura publicación (decisión del usuario):** `docs/manual-usuario.md`, `docs/presentacion-oral.md`, `docs/demo-presentacion.md`, `docs/demo/respuesta-dns-simulada.json`, `docs/img/manual/` (24 PNG), `scripts/preparar_demo.py`, y las modificaciones de `README.md`, `docs/mvp-academico.md`, `docs/frontend.md`. Las bases de demostración quedaron en `%TEMP%` y se eliminaron; `data/mmg.sqlite3` no cambió (SHA256 `052ECE35…2131293`). No se hizo commit, pull ni push.

### 2026-11-18 · Agente 06 → Agente 07 (copia a 03 y 04) · Cierre técnico y preparación documental

- **Estado:** aprobado con observaciones
- **Objetivo:** entregar a documentación una versión académica verificada, sin crear todavía el manual ni el guion.
- **Archivos modificados:** `docs/agents/auditoria-integral-dns.md`, `docs/agents/HANDOFF.md` y `docs/agents/BACKLOG.md`. Sin cambios de lógica, pruebas, dependencias o esquema en esta intervención.
- **Contratos o decisiones relevantes:** QA-06-01 y QA-06-04 corregidos para la política limitada D-20; QA-06-02 corregido para un proceso y una instancia; QA-06-03 queda como riesgo documentado con conflicto 409. No se necesita otra intervención del Agente 04 sobre `canonizar_dominio`; P-05 y P-06 siguen pendientes de decisión.
- **Pruebas ejecutadas y resultados:**
  - `.\.venv\Scripts\python.exe -m pytest -q`: **368 passed, 1 skipped in 21.86s**, con DNS real deshabilitado y SQLite temporal.
  - Las 12 reproducciones de QA: **12 passed in 1.98s**; suite dirigida DNS y concurrencia: **267 passed in 14.76s**; concurrencia sola: **6 passed in 2.91s**.
  - Ruff check, Bandit de `app` y `tests -s B101`, pip check y `git -c core.whitespace=cr-at-eol diff --check`: código 0. Bandit emitió avisos sobre palabras en comentarios de tests, sin hallazgos.
  - Arranque de uvicorn con una base temporal: `/health` respondió 200; proceso detenido después de la prueba.
- **No probado:** `pip-audit` y consulta DNS real por la restricción de no usar Internet; despliegue público, multiproceso y navegador en esta intervención. La auditoría anterior documenta las verificaciones de navegador.
- **Funcionalidades para el manual:** crear, consultar y editar entidades y relaciones, inspeccionar nodos y aristas, visualizar el grafo, usar cinco distribuciones y contadores, ejecutar BFS, DFS y camino más corto. La API ofrece DELETE; la interfaz aún no ofrece eliminación.
- **Ejecución en Windows con VS Code:** abrir el proyecto en VS Code, usar PowerShell en su terminal, disponer del entorno `.venv` con las dependencias de `requirements.txt`, y ejecutar desde la raíz:

  ```powershell
  $env:MMG_DATABASE_PATH = Join-Path $env:TEMP ("mmg-demo-" + [guid]::NewGuid().ToString() + ".sqlite3")
  .\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
  ```

  Abrir `http://127.0.0.1:8000/` y detener con `Ctrl+C`. La ruta única evita tocar `data/mmg.sqlite3`. No usar múltiples workers ni varias instancias contra esa base. Para una instalación nueva, seguir [README.md](../../README.md).
- **Capturas a preparar:** vista vacía; creación y edición de entidad y relación; inspector de nodo y arista; grafo con contadores y distribución; ejecución de BFS, DFS y camino; vista previa DNS con estados, fuente y fecha; revisión, selección A/AAAA, confirmación y resultado de incorporación. Usar datos ficticios y capturas reales de la interfaz; no usar datos personales ni la base principal.
- **Defensa oral:** explicar grafo dirigido y persistencia SQLite, BFS y sus niveles, DFS y su recorrido, camino más corto por cantidad de aristas, reconstrucción del grafo y por qué Cytoscape visualiza pero no calcula esos algoritmos.
- **DNS a documentar:** la consulta muestra A, AAAA, CNAME, MX y NS sin guardar automáticamente. Solo A/AAAA revisados se seleccionan y requieren confirmación explícita. El lote crea o reutiliza dominio, IP, relación `APUNTA_A` y evidencia en una transacción; la procedencia es declarada por el cliente, no verificada por el servidor.
- **Advertencias del manual:** soporte IDNA limitado, no IDNA 2008 completo; P-05/409 ante duplicados equivalentes del CRUD; un proceso y una instancia; posible indicador orientativo de duplicado después de incorporar; recuperación de errores inciertos o persistencia confirmada mediante actualización del grafo. Consultas DNS reales requieren red y deben hacerse solo con autorización.
- **Documentos a revisar:** [README.md](../../README.md), [frontend.md](../frontend.md) y [mvp-academico.md](../mvp-academico.md) para el alcance final; [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) señala discrepancias históricas de [protocolo-agentes.md](../protocolo-agentes.md) y [estado-proyecto.md](../estado-proyecto.md). Actualizar según su carácter histórico, sin inventar funcionalidades.
- **Preparación GitHub:** el workspace contiene archivos funcionales DNS, pruebas y documentación sin seguimiento que deben incluirse deliberadamente. `data/mmg.sqlite3` y `.venv` están ignorados; revisar la conveniencia de versionar `.claude/` y `.codex/` y verificar secretos antes del cierre manual. No se realizó commit, pull ni push.

### 2026-11-18 · Agente 03 → Agente 06 (copia a 04 y 07) · Corrección de QA-06-01 residual y QA-06-04 (A-label `xn--` inválida)

- **Estado:** aprobado con observaciones (verificación independiente)
- **Objetivo:** cerrar las 12 reproducciones de la reauditoría: `İstanbul.tr` debe rechazarse y las A-label `xn--` inválidas deben responder 422 antes de consultar o escribir. Sin cambios de esquema, dependencias, frontend ni commit.
- **Causa raíz de QA-06-01:** `normalizar_dominio()` y `canonizar_dominio()` aplicaban `lower()` al texto completo antes de la regla. `İ` (U+0130) pasa a `i` más punto combinante, que ya tiene la longitud esperada. La comprobación de cambio de longitud nunca se disparaba. Verificado: reintroducir la minúscula previa en un plugin temporal hace fallar exactamente las 7 pruebas de `İstanbul.tr` y sus equivalentes.
- **Causa raíz de QA-06-04:** `convertir_dominio()` devolvía sin validar toda etiqueta ASCII, incluidas las que empiezan por `xn--`. Ninguna capa comprobaba la carga Punycode ni el contenido decodificado.
- **Solución:**
  - Una única función pública, `convertir_dominio(entrada)`, en `app/domain/nombres_dns.py`. Recibe el texto original: recorta espacios, quita un punto final, rechaza etiquetas vacías y separadores no ASCII, y decide la seguridad de cada etiqueta Unicode antes de cualquier minúscula.
  - Las etiquetas Unicode se codifican con `punycode` de la biblioteca estándar, con prefijo `xn--`, y el resultado pasa por la misma validación que una A-label recibida. El codec `idna` ya no se usa como criterio de validez.
  - `normalizar_dominio()` (aplicación) y `canonizar_dominio()` (persistencia) llaman a esa función. Cada capa conserva sus validaciones propias: IP, separadores y TLD en aplicación; etiquetas ASCII en persistencia.
- **Archivos modificados:**
  - `app/domain/nombres_dns.py`: reescrito. Política única.
  - `app/application/dns_lookup.py`: `normalizar_dominio()` usa la política sobre el texto original.
  - `app/persistence/incorporacion_dns.py`: **intervención en persistencia, el Agente 04 debe revisarla.** `canonizar_dominio()` delega en la misma política. Sin cambios en esquema, repositorios CRUD, normalización de entidades ni contrato transaccional.
  - Pruebas nuevas: `tests/persistence/test_politica_idna_coherente.py` (23).
  - Pruebas ampliadas: `tests/domain/test_nombres_dns.py` (de 15 a 47), `tests/api/test_dns_idna_api.py` (de 8 a 22).
  - Pruebas de Agente 06: sin cambios. Las 12 reproducciones se conservan sin modificar.
  - Documentación: `docs/agents/DECISIONS.md` (D-20 y P-06), `docs/agents/BACKLOG.md`, `docs/frontend.md` (un párrafo en OSINT DNS) y esta entrega.
- **Tratamiento de Unicode (QA-06-01):**
  - Se rechazan con 422, sin llegar a red ni a SQLite: `İ` y su forma descompuesta (`I` más combinante), `ẞ`, `ß`, `ς`, formas de ancho completo, ligaduras, guion blando, formas de compatibilidad, separadores ideográficos (`。`, `．`, `｡`) y etiquetas vacías.
  - Se aceptan: ASCII en cualquier mayúscula, `münchen.de` y `MÜNCHEN.de` (incluida la forma NFD de la `ü`), `σ.gr`, y los casos de espacios de borde y punto final.
  - Ante `İ`, la regla compara longitudes antes de bajar a minúsculas, sobre el texto NFC original.
- **Tratamiento de A-label (QA-06-04):** una etiqueta que empieza por `xn--` (sin distinguir mayúsculas) se valida así:
  1. La carga tiene solo `[a-z0-9-]`, no termina en guion y no está vacía.
  2. Se decodifica con `punycode` de la biblioteca estándar. Si falla, se rechaza.
  3. El resultado debe tener al menos un carácter no ASCII.
  4. El resultado está en minúsculas, en NFC y en NFKC. No tiene caracteres de control (`Cc`), formato (`Cf`), de uso privado (`Co`), no asignados (`Cn`), espacios ni separadores, y no empieza por marca combinante.
  5. Volver a codificar el resultado reproduce exactamente la carga (forma canónica).
  - Se rechazan: `xn--`, `xn--abc-`, `xn--bogus` (decodifica a letras griegas en mayúscula), `xn--invalid-zz` (carga mal formada), `xn--a` (decodifica a un byte de control), `xn--mnchen-3ya-` y las cargas con contenido prohibido.
  - Se aceptan y **no se reinterpretan**: `xn--mnchen-3ya.de`, `xn--strae-oqa.de` (contenido `straße`; es válido en IDNA 2008, aunque IDNA 2003 lo cambiaría, por eso no se somete a la regla de transformación) y `xn--4xa` (`σ`).
  - Límite de la política: no es IDNA 2008. Una etiqueta que pasa estas reglas puede seguir siendo inválida para IDNA 2008.
- **Resultado de las 12 reproducciones:** antes del cambio, `pytest -q` mostraba `12 failed, 293 passed, 1 skipped`. Después, las 12 pasan: las cuatro reproducciones juntas dan `12 passed`.
- **Pruebas ejecutadas y resultados:**
  - `.\.venv\Scripts\python.exe -m pytest -q` (suite completa): **368 aprobadas, 1 omitida**, 23 s, sin fallos.
  - `tests/domain/test_nombres_dns.py`: 47 aprobadas. `tests/persistence/test_politica_idna_coherente.py`: 23 aprobadas. `tests/api/test_dns_idna_api.py`: 22 aprobadas.
  - Mutación de QA-06-01: con la minúscula previa reintroducida, fallan exactamente 7 pruebas de `İstanbul.tr` y sus equivalentes.
  - `.\.venv\Scripts\python.exe -m ruff check .`: sin errores.
  - `.\.venv\Scripts\python.exe -m bandit -q -c bandit.yaml -r app`: código 0, sin hallazgos. Con `-r tests -s B101`, solo avisos del gestor sobre palabras en comentarios, sin hallazgos.
  - `.\.venv\Scripts\python.exe -m pip check`: sin dependencias rotas.
  - `git -c core.whitespace=cr-at-eol diff --check`: código 0.
- **No probado:**
  - IDNA 2008 completo y la lista exacta de caracteres que IDNA 2008 excluye. Solo se implementaron criterios conservadores con la biblioteca estándar.
  - Equivalencia con registros DNS reales: no se consultó Internet, y la decisión de qué A-label corresponde a cada nombre depende del registro.
  - Multiproceso, WAL y base grande (sin cambios desde la entrega anterior).
  - Navegador: no se cambió la interfaz; la verificación visual de los mensajes 422 queda para el Agente 05 o el Agente 06.
- **Pendientes, riesgos y bloqueos:**
  - **Agente 06, para la verificación independiente:**
    1. Reejecutar las 12 reproducciones de la reauditoría y confirmar que pasan sin debilitarlas.
    2. Revisar la lista de criterios de `validar_a_label` en `app/domain/nombres_dns.py`, en especial que `xn--strae-oqa.de` y `xn--mnchen-3ya.de` se acepten sin reinterpretación.
    3. Revisar el cambio de comportamiento: `xn--a.com` ahora responde 422 (antes se aceptaba), las etiquetas vacías se rechazan en la política de dominio, y `XN--...` en mayúsculas se canonicaliza a minúsculas.
    4. Reproducir la mutación con la minúscula previa para confirmar que las pruebas de `İstanbul.tr` fallan.
  - **Agente 04:** revisar la intervención en `canonizar_dominio`, que ahora delega en la política compartida. Las pruebas de equivalencia y de rechazo de CRUD siguen en su archivo. El resto de la capa no cambió.
  - **Agente 05:** no hay cambio de contrato. Los 422 llegan con el texto del servidor. Si se quiere un mensaje más breve, se puede pedir acortarlo en el servidor.
  - **Riesgo residual:** el set de caracteres que IDNA 2003 o la política propia tratan como válidos puede diferir de IDNA 2008. Una entrada aceptada aquí puede no ser válida en un registro que aplique 2008.
  - **P-06 sigue abierto** y es decisión del usuario. No declarar IDNA 2008 implementado ni la versión publicada.
  - Sin commit, sin push, sin cambios de esquema, dependencias, base real ni frontend.

### 2026-11-18 · Agente 06 → Agentes 03 y 04 (copia a 07) · Reauditoría final DNS

- **Estado:** requiere correcciones
- **Objetivo:** verificar QA-06-01/02, revisar el cambio de canonicalización de persistencia y evaluar P-05.
- **Archivos modificados:** `docs/agents/auditoria-integral-dns.md`, `docs/agents/HANDOFF.md`, `docs/agents/BACKLOG.md`; pruebas de aplicación, API, persistencia y concurrencia. Sin cambios de lógica funcional, esquema o dependencias.
- **Contratos o decisiones relevantes:** QA-06-02 está corregido para un solo proceso. QA-06-03 puede quedar como riesgo documentado para esta versión: el CRUD puede crear equivalentes, pero incorporación devuelve 409 sin elegir ni escribir parcialmente. D-20 no queda completamente verificada: la `İ` mayúscula evade el rechazo por el `lower()` previo. A-labels `xn--` inválidas también son aceptadas.
- **Pruebas ejecutadas y resultados:**
  - Suite enfocada previa a las reproducciones nuevas: `.\.venv\Scripts\python.exe -m pytest -q tests/domain/test_nombres_dns.py tests/api/test_dns_idna_api.py tests/application/test_concurrencia_grafo.py tests/persistence/test_incorporacion_dns.py tests/application/test_incorporacion_servicio_dns.py`: **116 passed**.
  - Suite completa con 12 reproducciones agregadas: `.\.venv\Scripts\python.exe -m pytest -q`: **293 passed, 1 skipped, 12 failed**. Las fallas son exclusivamente los casos de `İ` mayúscula y `xn--bogus.de` / `xn--invalid-zz.de` en dominio, aplicación, persistencia y API.
  - Suite enfocada final: **183 passed, 12 failed**; las seis pruebas de concurrencia pasan.
  - Ruff check, Bandit (`app`, `tests -s B101`), pip check y cinco `node --check`: aprobados.
  - `ruff format --check .`: **23 files would be reformatted, 74 files already formatted**, informativo/no bloqueante; no se reformateó trabajo ajeno.
  - `git -c core.whitespace=cr-at-eol diff --check`: código 0.
- **No probado:** `pip-audit` por restricción de no consultar Internet; navegador, no afectado por estos cambios; concurrencia multiproceso, fuera del alcance.
- **Pendientes, riesgos y bloqueos:**
  - **Agente 03:** corregir el bypass de `İ` y rechazar A-labels Punycode inválidas, preservando nombres válidos como München y `xn--strae-oqa.de`, sin IDNA 2008 ni nueva dependencia.
  - **Agente 04:** revisar la misma validación dentro de `canonizar_dominio`; no cambiar el CRUD global en esta corrección.
  - **Agente 07:** el manual y la presentación pueden prepararse, pero no declarar versión aprobada o lista para publicar hasta que pasen las pruebas nuevas.
  - La ejecución soportada sigue siendo un proceso. Los comandos documentados no usan `--workers`. `.claude/` y `.codex/` son configs/skills sin seguimiento que requieren decisión antes de versionar; `tests/network/test_dns_google_real.py` es opt-in y no se ejecutó. Sin commit, pull ni push.

### 2026-11-18 · Agente 03 → Agente 06 (copia a 04, 05 y 07) · Correcciones de QA-06-01 y QA-06-02; evaluación de QA-06-03

- **Estado:** requiere correcciones (reauditoría)
- **Objetivo:** corregir los dos hallazgos ALTO de la auditoría del 2026-11-17, evaluar el MEDIO y dejar el backend listo para la verificación final. Sin cambios de esquema, dependencias, frontend ni commit.
- **Archivos modificados:**
  - `app/domain/nombres_dns.py` (nuevo): regla de conversión IDNA compartida. Usa solo la biblioteca estándar.
  - `app/application/dns_lookup.py`: `normalizar_dominio` usa la regla compartida. Las validaciones previas no cambian.
  - `app/persistence/incorporacion_dns.py`: **intervención en persistencia, Agente 04 debe revisarla.** `canonizar_dominio` usa la misma regla. Motivo: sin ella, una entidad DOMINIO existente `straße.de` coincidía con una incorporación de `strasse.de` y se reutilizaba la entidad de otro dominio. Es el único cambio en esa capa.
  - `app/application/service.py`: cerrojo de módulo `_PUBLICACION_GRAFO`. `reconstruir_grafo` y `_refresh_after_write` cargan y publican bajo él, a través de `_cargar_y_publicar`.
  - Pruebas nuevas: `tests/domain/test_nombres_dns.py` (15), `tests/api/test_dns_idna_api.py` (8) y `tests/application/test_concurrencia_grafo.py` (6).
  - Pruebas ampliadas: `tests/application/test_dns_lookup.py` (+6), `tests/application/test_incorporacion_servicio_dns.py` (+1 caso).
  - `tests/persistence/test_incorporacion_dns.py`: se quitó `straße.de` de la lista de equivalencias, que fijaba el defecto, y se añadió `test_stra_e_sharp_s_no_se_canonicaliza_como_strasse`.
  - Documentación: `docs/agents/DECISIONS.md` (D-20 y D-21; P-05 y P-06 actualizados), `docs/agents/BACKLOG.md`, `docs/frontend.md` (un párrafo en OSINT DNS) y esta entrega.
- **Contratos o decisiones relevantes:**
  - Sin cambios de forma en la API. Cambio de comportamiento: un dominio con transformaciones IDNA no equivalentes responde **422** con `"el dominio no puede convertirse con seguridad: ..."` en `POST /api/v1/osint/dns` y en `POST /api/v1/osint/dns/incorporaciones`. Antes respondía 200 con otro nombre. La interfaz muestra ese texto sin cambios.
  - **QA-06-01, mitigado (D-20).** Se rechazan: `ß`; separadores ideográficos (`。`, `．`, `｡`); caracteres de compatibilidad, como ancho completo o ligaduras; guion blando; `ς`; `İ`. Sin cambios: ASCII, A-label `xn--` (incluido `xn--strae-oqa.de`, que no se reinterpreta) y Unicode canónicamente equivalente (`münchen.de`, forma NFD). Las etiquetas convertidas se verifican por ida y vuelta. **No es IDNA 2008**: P-06 sigue pendiente.
  - **QA-06-02, corregido dentro de un proceso (D-21).** Antes, la carga y la publicación no tenían exclusión mutua, y una reconstrucción leída antes de un commit podía publicarse después de otra más reciente. Ahora el cerrojo cubre carga y publicación: el último snapshot publicado es el último leído. El cerrojo lo comparten todas las instancias del servicio del proceso. Las lecturas no lo usan. Un fallo de carga invalida el grafo como antes, y `GraphReconstructionError` e `IncorporacionPersistidaSinGrafoError` conservan su semántica.
  - **QA-06-03, evaluado, riesgo conocido.** No se modificó el CRUD. Verificado: con DOMINIO `münchen.de` y `xn--mnchen-3ya.de` creados por CRUD, la incorporación responde 409, no escribe nada y no elige ninguno. P-05 sigue pendiente.
- **Pruebas ejecutadas y resultados:**
  - Reproducción de QA-06-02 **antes** de la corrección: `pytest tests/application/test_concurrencia_grafo.py`, con el servicio original: 3 fallidas y 2 aprobadas. Las fallidas comprueban que la segunda carga no arranca mientras la primera publica, y lo que falla es esa comprobación.
  - Síntoma directo, con script temporal fuera del repositorio: sin cerrojo, grafo con 1 entidad frente a 2 en SQLite. Con cerrojo, 2 y 2.
  - Mutación de QA-06-01: un plugin temporal que restaura `encode("idna")` hace fallar 15 pruebas. Incluye las de `straße.de` en consulta, incorporación y persistencia, y la de no reutilizar la entidad equivocada.
  - Estrés: 16 hilos con 5 creaciones CRUD cada uno: 80 aprobadas, 0 errores de SQLite, grafo igual a la base (80 entidades).
  - `pytest tests/application/test_concurrencia_grafo.py tests/persistence/test_incorporacion_dns.py`, repetido cinco veces: 60 aprobadas en cada ejecución.
  - `pytest -q` (suite completa): **293 aprobadas, 1 omitida**. La auditoría registró 257 aprobadas y 1 omitida.
  - `ruff check .`: sin errores. `bandit -q -c bandit.yaml -r app`: sin hallazgos. `git -c core.whitespace=cr-at-eol diff --check`: código 0.
- **No probado:**
  - Multiproceso (uvicorn con varios workers), reinicio durante una escritura, WAL, base grande y rendimiento de la búsqueda lineal.
  - CRUD e incorporación entre procesos.
  - Interfaz en navegador: no se cambió el frontend.
  - IDNA 2008, y las letras que IDNA 2003 acepta y 2008 no.
  - La comprobación negativa de concurrencia usa un espera de 0,3 s. Es una ausencia de evento, no una medición de tiempo; si el equipo está muy cargado, la prueba puede tardar más, pero no cambia su resultado.
- **Pendientes, riesgos y bloqueos:**
  - **Agente 06 verificó:** QA-06-02 dentro de un proceso y QA-06-03 con 409 seguro. La reauditoría detectó que D-20 no rechaza `İ` mayúscula cuando la aplicación/persistencia ejecutan `lower()` antes de la regla compartida, y que A-labels inválidas se aceptan. Ver la reauditoría final al inicio de este archivo.
  - **Riesgo multiproceso (QA-06-02):** cada proceso mantiene su copia del grafo. Con varios workers, cada uno quedaría atrasado frente a los otros. El cerrojo no lo resuelve. Mientras el despliegue use un solo proceso, la garantía vale. Si se necesita más de uno, hace falta una decisión de arquitectura.
  - **Riesgo de rendimiento:** la recarga ocurre bajo el cerrojo, así que las escrituras concurrentes se serializan con ella. Aceptable a escala académica; no medido.
  - **P-06 sigue abierto.** Los usuarios deben escribir la forma `xn--` de un nombre con ß. La A-label correcta depende del registro, así que conviene confirmarla antes de documentarla como ejemplo.
  - **Agente 04:** revisar la intervención en `canonizar_dominio` y los cambios en `tests/persistence/test_incorporacion_dns.py`.
  - **Agente 05:** no se requiere cambio. Si se quiere, el texto del 422 puede acortarse.
  - **Agente 07:** `docs/frontend.md` tiene un párrafo nuevo. La afirmación de "listo para publicación" debe esperar la reauditoría.
  - Sin commit, sin push, sin cambios de esquema ni de dependencias.

### 2026-11-17 · Agente 06 -> Coordinación, Agentes 03, 04, 05 y 07 · Auditoría integral DNS

- **Estado:** requiere correcciones
- **Objetivo:** auditar de forma independiente la incorporación DNS A/AAAA, `osint.js`, persistencia, regresiones del MVP y preparación para documentación/publicación.
- **Archivos modificados:** `docs/agents/auditoria-integral-dns.md`, `docs/agents/HANDOFF.md` y `docs/agents/BACKLOG.md`. Sin cambios en lógica, esquema o pruebas.
- **Contratos o decisiones relevantes:** se verificó la declaración de procedencia, la exclusión de CNAME/MX/NS y el conflicto seguro 409 ante dominios ambiguos. P-05 permanece sujeto a decisión; P-06 tiene un defecto concreto de IDNA 2003.
- **Pruebas ejecutadas y resultados:**
  - `.\.venv\Scripts\python.exe -m pytest -q`: 257 aprobadas, 1 omitida.
  - Ruff check, Bandit para `app` y `tests`, `pip check` y cinco `node --check`: sin errores/hallazgos.
  - Ruff format check: 21 archivos reformateables, 71 ya formateados; no bloqueante según la configuración.
  - Navegador local con SQLite temporal y DNS simulado: éxito, selección, confirmación, cancelación, Escape, doble clic, 422, 409, SQLite ocupado real, 503 con persistencia confirmada simulado, red, timeout, JSON malformado, XSS, restauración de sesión y cuatro anchos responsive.
  - Reproducción adicional: `straße.de` se normaliza a `strasse.de`; una carrera concurrente puede dejar el grafo en memoria atrasado. Ambas se describen con pasos y resultados en el informe.
  - `pip-audit` no se ejecutó por la prohibición de consultar Internet. `git -c core.whitespace=cr-at-eol diff --check` y `git status --short` se ejecutarán tras actualizar esta entrega.
- **No probado:** CI de GitHub, WAL, concurrencia entre procesos, base grande y reinicio durante una solicitud.
- **Pendientes, riesgos y bloqueos:**
  - **Agente 03:** resolver QA-06-01 (IDNA) y QA-06-02 (publicación concurrente del grafo), con pruebas deterministas.
  - **Agentes 03/04 y usuario:** decidir alcance de P-05. Las entidades equivalentes existentes causan 409 seguro.
  - **Agente 05:** posible mejora no bloqueante al texto de “Posible duplicado” para registros ya incorporados.
  - Veredicto: **REQUIERE CORRECCIONES**. No aprobar el cierre ni la preparación de publicación hasta resolver los dos hallazgos ALTO.

### 2026-11-17 · Agente 05 → Agente 06 · Interfaz de incorporación DNS A/AAAA al grafo

- **Estado:** listo para revisión
- **Objetivo:** permitir elegir registros DNS A y AAAA revisados, confirmar el lote, enviarlo a
  `POST /api/v1/osint/dns/incorporaciones`, mostrar creados frente a reutilizados, actualizar el
  grafo y recuperarse de los errores. Sin cambios en backend, esquema, dependencias ni commits.
- **Archivos modificados:**
  - `app/frontend/osint.js`: reescrito completo (archivo sin seguimiento en git, no hay diff
    contra HEAD). Conserva la consulta y la vista previa; agrega selección, confirmación, envío,
    resultado y recuperación.
  - `app/frontend/osint-incorporacion.js` (nuevo): lógica pura sin DOM ni red. Construye el lote,
    valida la respuesta, resume creados y reutilizados y clasifica fallos.
  - `app/frontend/index.html`: sección "Incorporar al grafo" dentro de la vista previa y script
    `osint-incorporacion.js` antes de `osint.js`.
  - `app/frontend/osint.css`: estilos del panel, la nota y el resultado.
  - `app/frontend/app.js`: `api()` conserva `error.persistencia` del cuerpo de error; `refresh()`
    dispara el evento `mmg:datos-actualizados` tras una actualización correcta. Cambios aditivos.
  - `tests/api/osint_incorporacion_harness.js` (nuevo): harness en Node con DOM mínimo y Cytoscape
    simulado. Ejecuta `app.js`, `osint-incorporacion.js` y `osint.js` con respuestas fijas.
  - `tests/api/test_osint_incorporacion_frontend.py` (nuevo): 3 pruebas (página, ausencia de
    `innerHTML`, y escenarios del harness).
  - `docs/frontend.md`, `docs/agents/BACKLOG.md`, `docs/agents/DECISIONS.md` (D-19, P-01) y esta entrega.
- **Contratos o decisiones relevantes:**
  - Endpoint usado: `POST /api/v1/osint/dns/incorporaciones`. Cuerpo: `dominio` y `registros`
    con `tipo`, `valor`, `fuente` y `consultado_en` tomados del registro consultado. Sin CNAME, MX
    ni NS; sin lote vacío; máximo 100 registros. No hay normalización en JavaScript.
  - Revisado e Incorporar son controles separados (D-19). Incorporar exige revisión previa.
  - Confirmación en línea, sin modal (D-09). Foco: título al abrir, resultado al enviar, botón
    "Revisar incorporación" al cancelar, y botón "Actualizar grafo" tras un fallo incierto.
  - Tras éxito, `refresh({selection: state.selection})` (mismo mecanismo que "Actualizar"). Conserva
    layout y selección. Un fallo al actualizar deja el estado de recuperación.
  - Estado "pendiente de grafo" (`graphPending`): tras red, timeout, respuesta malformada, HTTP
    distinto de 422/409/503 y 503 con `persistencia: confirmada`, no se permite otro envío hasta
    actualizar el grafo con éxito.
  - Procedencia: siempre presentada como "Declarada por el cliente. El servidor no verificó esta
    consulta".
  - Persistencia en `sessionStorage` (`mmg.osint.preview`) de `reviewed`, `selected` e
    `incorporated`. Una consulta nueva o "Limpiar" descarta todo lo de la vista anterior.
- **Pruebas ejecutadas y resultados:**
  - `.\.venv\Scripts\python.exe -m pytest -q` (suite completa, con cambios de otras entregas sin commit): **257 aprobadas, 1 omitida**. Línea base previa a esta etapa: 254 aprobadas, 1 omitida.
  - `.\.venv\Scripts\python.exe -m pytest -q tests/api/test_osint_incorporacion_frontend.py tests/api/test_osint_frontend.py tests/api/test_frontend.py`: 9 aprobadas.
  - `node --check` sobre `app.js`, `osint.js`, `osint-incorporacion.js` y el harness: sin errores.
  - `ruff check tests/api/test_osint_incorporacion_frontend.py`: "All checks passed!". No se tocó ningún archivo Python de `app/`.
  - `git -c core.whitespace=cr-at-eol diff --check`: sin avisos, código de salida 0.
  - Navegador real (Playwright sobre la página servida por uvicorn en base temporal fuera del repo):
    consulta con la respuesta DNS **simulada** por interceptación (sin Internet), revisión y
    selección de 2 A y 1 AAAA, panel de confirmación con foco en el título, envío real a la API
    local, resultado con "Creadas: 3 · Reutilizadas: 0" en las tres categorías, foco en el título
    del resultado, grafo actualizado a "4 entidades · 3 relaciones" y "Datos actualizados.".
    Captura del resultado revisada.
- **No probado:**
  - En navegador: los caminos de error (422, 409, 503 por bloqueo, 503 con `persistencia:
    confirmada`, red, timeout y malformado) y Escape/Cancelar. Solo cubiertos por el harness.
  - Diseño responsive a 700 px y 900 px; contraste medido. Solo se revisó la captura de escritorio.
  - Concurrencia entre pestañas y reinicio del servidor durante una incorporación.
  - Cytoscape real: el harness simula la API; el posicionamiento real no se verificó en el harness.
- **Pendientes, riesgos y bloqueos:**
  - **Para el Agente 06, revisar:**
    1. Tras una incorporación exitosa, los registros recién creados aparecen como "Posible
       duplicado". Es la heurística previa de la vista previa, no un error de datos. Decidir si se
       ajusta el texto para registros marcados como "Incorporado".
    2. El mensaje del backend para `persistencia: confirmada` dice "Reintente la misma incorporación
       para recuperarlo". La interfaz **no** muestra ese texto: ofrece "Actualizar grafo" (regla del
       encargo). La entrega del Agente 03 pedía ofrecer reintento, lo que contradice la regla. Hay
       que decidir cuál vale. Si se reintenta, el backend reutiliza todo y responde 200.
    3. `incorporated` persiste en `sessionStorage`. Si el grafo cambia por otra vía (CRUD de otra
       pestaña), el marcado puede quedar obsoleto. P-04 (eliminar desde la interfaz) sigue pendiente.
    4. `osint.js` quedó reescrito completo, sin historial en git. Conviene revisar el diff contra la
       versión de la conversación anterior antes de aprobar.
    5. Errores HTTP sin cuerpo JSON no tienen `status` en `api()`: se tratan como incierto (conservador).
    6. El harness usa un DOM mínimo; si cambia el HTML, actualizar `matches()` o los selectores.
  - Sin bloqueos del backend. Ninguna dependencia nueva. Sin commit ni push.
- **Qué se aprueba:** el flujo de selección y confirmación, el resultado y la recuperación ante fallos,
  según las pruebas automatizadas. La verificación en navegador cubre solo el camino feliz.

### 2026-11-17 · Agente 04 → Agentes 03, 05 y 06 · Cierre de persistencia DNS: equivalencias IDNA y robustez

- **Estado:** listo para revisión
- **Objetivo:** corregir el riesgo de duplicados IDNA señalado por el Agente 03, cubrir con pruebas
  la matriz de persistencia pedida y revisar la capa transaccional. Sin cambios de esquema, sin
  dependencias, sin cambios en API, servicio ni frontend, sin commit.
- **Archivos modificados:**
  - `app/persistence/incorporacion_dns.py`: canonicalización IDNA, validación y canonicalización del lote.
  - `tests/persistence/test_incorporacion_dns.py`: 55 pruebas (antes 27).
  - `docs/agents/DECISIONS.md` (D-16, D-17, D-18; P-01 resuelto; P-05 y P-06 nuevos),
    `docs/agents/BACKLOG.md` y este archivo.
  - Sin cambios: `database.py`, `errors.py`, `repositories.py`, `mappers.py`, `schema.py`, CRUD,
    `app/application`, `app/api` y frontend.
- **Contratos o decisiones relevantes:**
  - **Defecto IDNA corregido.** `canonizar_dominio(valor)` hace: recorte de espacios, minúsculas,
    quita un único punto final, `encode("idna")` a ASCII, y valida que cada etiqueta cumpla
    `^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$` con longitud total de hasta 253. Si algo falla, lanza
    `ValueError`. Es la misma regla que `normalizar_dominio` de la aplicación; las pruebas de
    equivalencia comparan ambas funciones. No se importa código de aplicación, para no invertir capas.
  - Las entidades DOMINIO existentes se comparan por `valor` y por `valor_normalizado`, ambos
    canonicalizados. Una entidad que coincide por los dos campos cuenta una vez. Una coincidencia
    única se reutiliza; varias lanzan `CoincidenciaAmbiguaError` (409) antes de escribir. Ninguna
    entidad existente se modifica. Un valor existente que no es un nombre IDNA válido no coincide.
  - Los dominios nuevos se guardan en forma canónica ASCII.
  - **Cambio de contrato, compatible:** `LoteDnsIncorporacion.dominio` y las IP aceptan cualquier forma
    equivalente (Unicode, mayúsculas, punto final, IPv6 abreviada). La persistencia canonicaliza antes
    de buscar y escribe la forma canónica. La aplicación sigue canonicalizando: el Agente 03 no
    necesita cambios.
  - **Otros defectos corregidos**, demostrados con pruebas que fallaban antes de la corrección
    (19 fallos en la ejecución previa):
    - La persistencia aceptaba etiquetas inválidas (`a b.com`, `-a.com`, `example.com/ruta`) y podía
      crear DOMINIO inválidos. Ahora se rechazan con `LoteDnsInvalidoError`, que la aplicación ya
      traduce a `IncorporacionDnsInvalidaError`.
    - La persistencia aceptaba IPv6 con zona (`fe80::1%eth0`). Ahora se rechaza. La aplicación ya lo
      rechazaba; la persistencia era la última defensa.
    - La fuente con espacios de borde se rechazaba; ahora se recorta, igual que en la aplicación.
  - Procedencia: sin cambios. `evidencia.fuente` lleva el prefijo `declarada por el cliente: ` (D-18).
- **Matriz de persistencia pedida y dónde está:**
  - Unicode frente a punycode, en ambos sentidos: `test_dominio_en_unicode_se_guarda_en_forma_canonica`,
    `test_consulta_en_punycode_reutiliza_dominio_creado_en_unicode` y la prueba parametrizada
    `test_reutiliza_dominio_guardado_en_cualquier_representacion`.
  - Unicode existente y consulta posterior en punycode: la prueba anterior.
  - Punycode existente y consulta equivalente, incluida punycode en mayúsculas: la misma prueba parametrizada.
  - Forma descompuesta (NFD) de la `ü`: prueba parametrizada.
  - Mayúsculas y punto final: `MÜNCHEN.de.` y espacios de borde en la prueba parametrizada.
  - Ambigüedad y rollback: `test_unicode_y_punycode_existentes_son_ambiguos_y_revierten` y
    `test_coincidencias_de_ipv6_ambiguas_revierten_el_dominio_creado`.
  - Idempotencia de entidades, relaciones y evidencias: `test_repetir_el_lote_no_duplica_nada` y
    `test_registro_repetido_dentro_del_mismo_lote_reutiliza_relacion_y_evidencia`.
  - Reutilización de entidades de CRUD: prueba parametrizada de reutilización y
    `test_entidad_con_valor_y_valor_normalizado_equivalentes_cuenta_una_vez`.
  - Concurrencia entre sesiones: `test_dos_sesiones_concurrentes_no_duplican_el_lote` y
    `test_escritura_ajena_en_curso_hace_esperar_al_lote`.
  - SQLite ocupado en `BEGIN IMMEDIATE`: `test_base_ocupada_devuelve_error_sin_escritura_parcial`.
  - Bloqueo en `COMMIT`, de forma determinista: `test_commit_bloqueado_por_lector_revierte_y_el_reintento_funciona`.
    Un lector con SHARED impide el COMMIT del lote; el lote revierte, sin filas, y el reintento tras liberar
    el lector funciona.
  - Compatibilidad con CRUD: la suite completa, y `test_conexion_del_pool_vuelve_al_modo_por_defecto`
    (la conexión devuelta al pool queda en modo por defecto, no en AUTOCOMMIT).
  - Cierre de sesiones: `test_cada_fallo_devuelve_la_conexion_al_pool`.
- **Pruebas ejecutadas y resultados:**
  - `pytest tests/persistence/test_incorporacion_dns.py -q`: 55 aprobadas.
  - `pytest tests/persistence -q`: 92 aprobadas.
  - `pytest -q` (suite completa, con cambios sin commit de otros agentes): 254 aprobadas, 1 omitida.
  - Las cuatro pruebas de concurrencia y bloqueo, repetidas tres veces: 4 aprobadas en cada ejecución.
  - `ruff check app/persistence tests/persistence/test_incorporacion_dns.py`: sin errores.
  - `git -c core.whitespace=cr-at-eol diff --check`: sin avisos, código de salida 0.
  - Verificación HTTP en base temporal, fuera del repositorio: un DOMINIO `münchen.de` creado por CRUD
    (201). Incorporar `München.DE.` respondió 200 con el dominio `reutilizada` (id 1). Incorporar la
    punycode después también respondió 200 y `reutilizada`. Con dos entidades equivalentes existentes,
    el endpoint respondió 409 y no se creó ninguna entidad.
- **No probado:**
  - Concurrencia entre procesos. Solo hay hilos con dos conexiones en el mismo proceso.
  - Modo WAL y la base de producción, que no se abrió.
  - CRUD escribiendo en paralelo con un lote. Solo se probó con un lector SHARED.
  - Rendimiento con muchas entidades: la búsqueda es lineal por tipo y ocurre dentro del lock.
  - IDNA 2008. Ver P-06.
  - Mutación del código para confirmar que cada prueba falla sin su corrección.
- **Pendientes, riesgos y bloqueos:**
  - **P-06 (decisión del usuario y del Agente 03):** Python implementa IDNA 2003. `straße.de` se
    canonicaliza como `strasse.de`, que es otro nombre DNS. La forma IDNA 2008 `xn--strae-oqa.de` no
    se decodifica con el codec de la biblioteca estándar, así que no se empareja con `straße.de`. La
    aplicación ya consulta `strasse.de` para `straße.de`. Hacer IDNA 2008 exige una biblioteca no
    aprobada como dependencia. Sin cambios en esta etapa.
  - **P-05 (decisión del usuario):** los CRUD manuales siguen comparando texto exacto y pueden crear un
    DOMINIO en Unicode junto a uno equivalente en punycode. El lote no crea duplicados por esa causa:
    si encuentra dos equivalentes, responde ambigüedad (409).
  - **Agente 05:** el lote puede reutilizar una entidad guardada en Unicode. Su `valor` no cambia, así que
    la interfaz no debe asumir que el valor mostrado es ASCII. Los estados y la procedencia siguen igual.
  - **Agente 03:** revisar el tratamiento de `straße` (P-06) en `normalizar_dominio` y en las consultas
    DNS. No se encontró otro cambio necesario en la aplicación.
  - **Agente 06:** revisar la matriz de arriba, en particular NFD, ß (P-06), ambigüedad, reintento tras
    bloqueo y la devolución de conexiones al pool. El lock escanea todas las entidades del tipo.
  - Sin commit ni push.

### 2026-11-16 · Agente 03 → Agente 05 (y 06) · Servicio y API de incorporación DNS A/AAAA

- **Estado:** listo para revisión
- **Objetivo:** implementar el caso de uso y el endpoint `POST /api/v1/osint/dns/incorporaciones`
  sobre `IncorporacionDnsRepository.incorporar_lote()` del Agente 04. Solo backend: sin frontend,
  sin cambios de esquema, sin dependencias, sin commit.
- **Archivos modificados:**
  - `app/application/incorporacion_dns.py` (nuevo): validación, canonicalización, deduplicación,
    errores de aplicación y `IncorporacionDnsService`.
  - `app/application/service.py`: método público `refrescar_tras_escritura()` que delega en
    `_refresh_after_write()`. Cambio aditivo.
  - `app/api/dns_schemas.py`: esquemas de entrada y salida de incorporación. Los esquemas de consulta no cambian.
  - `app/api/dns_routes.py`: ruta `POST /dns/incorporaciones`. La consulta DNS no cambia.
  - `app/api/main.py`: registro de `app.state.incorporacion_dns_service` y manejadores HTTP de los
    errores nuevos. Cambio aditivo; no se tocaron los manejadores existentes.
  - `tests/application/test_incorporacion_servicio_dns.py` (nuevo): 31 pruebas.
  - `tests/api/test_incorporacion_dns_api.py` (nuevo): 22 pruebas.
  - `docs/agents/HANDOFF.md` y `docs/agents/BACKLOG.md`.
  - Sin cambios en `app/persistence`, en el esquema SQLite ni en el frontend.
- **Contratos o decisiones relevantes:**

  Entrada (`application/json`):

  ```json
  {
    "dominio": "example.com",
    "registros": [
      {
        "tipo": "A",
        "valor": "192.0.2.1",
        "fuente": "google-public-dns-doh",
        "consultado_en": "2026-11-16T12:00:00Z"
      }
    ]
  }
  ```

  - `registros`: entre 1 y 100 elementos. `tipo` solo `"A"` o `"AAAA"`, en mayúsculas.
  - `valor`: IP. Se canonicaliza con `ipaddress`, así que `2001:DB8::1` se guarda como `2001:db8::1`.
    Un registro A exige IPv4 y un AAAA exige IPv6. Se rechazan zonas IPv6 (`%eth0`).
  - `dominio`: se canonicaliza con `normalizar_dominio` (IDNA, minúsculas, sin punto final).
    `München.DE.` se guarda como `xn--mnchen-3ya.de`.
  - `fuente`: se recortan espacios. Debe tener de 1 a 100 caracteres imprimibles.
  - `consultado_en`: obligatoria, con zona horaria. Se guarda en UTC.
  - Los registros idénticos (mismo tipo, IP, fuente y fecha) se incorporan una sola vez.

  Respuesta `200` (ejemplo real, obtenido con el endpoint en una base temporal):

  ```json
  {
    "dominio": {"id": 1, "estado": "creada"},
    "resultados": [
      {
        "tipo": "A",
        "valor": "192.0.2.1",
        "entidad": {"id": 2, "estado": "creada"},
        "relacion": {"id": 1, "estado": "creada"},
        "evidencia": {"id": 1, "estado": "creada"},
        "procedencia": {
          "declarada_por": "cliente",
          "fuente": "google-public-dns-doh",
          "consultado_en": "2026-11-16T12:00:00Z"
        }
      }
    ]
  }
  ```

  Diferencias respecto de la propuesta del HANDOFF anterior:
  - Se agregó `procedencia` a cada resultado, para presentar la fuente y la fecha como declaradas.
  - `dominio` no devuelve el nombre canónico; el cliente ya conoce el que envió.
  - La incorporación no exige un grafo vigente antes de escribir, a diferencia de los CRUD. Así un
    reintento tras un fallo de reconstrucción recupera el grafo.
  - Los lotes de más de 100 registros se rechazan con 422.
  - Una `ForeignKeyConstraintError` se responde como 500, no como 404 del manejador global.

  Errores:

  | Caso | HTTP | Cuerpo |
  |---|---|---|
  | Forma inválida: JSON, tipo de campo, lista vacía o de más de 100 elementos, `fuente` o `valor` vacíos, `consultado_en` no parseable | 422 | Formato estándar de FastAPI |
  | Dominio o IP no válidos, tipo distinto de A/AAAA, versión IP incompatible, zona IPv6, fecha sin zona | 422 | `{"detail": "registros[i]: ..."}` o `{"detail": "Dominio no válido: ..."}` |
  | Dos o más coincidencias canónicas para el dominio o una IP | 409 | `{"detail": "Hay N entidades ... equivalentes ..."}` |
  | Conflicto de unicidad (defensa final) | 409 | `{"detail": "El lote duplicaría ..."}` |
  | SQLite ocupado por otra escritura | 503 | `{"detail": "La base de datos está ocupada ... el lote no se aplicó."}` |
  | Falla de reconstrucción **después** del commit | 503 | `{"detail": "Los datos de la incorporación sí se guardaron, pero el grafo no pudo reconstruirse. Reintente la misma incorporación para recuperarlo.", "persistencia": "confirmada"}` |
  | Referencia interna inconsistente (FK) | 500 | `{"detail": "Ocurrió un error interno ..."}` |

  Los errores de las cuatro primeras filas no dejan filas: la validación ocurre antes de escribir, y
  el repositorio revierte el lote completo. Ante `persistencia: confirmada`, la respuesta no habla de
  rollback. El reintento idéntico responde `200` con todos los estados en `reutilizada`.

  Procedencia: en la base queda `evidencia.fuente = "declarada por el cliente: <fuente>"`. La
  respuesta la presenta con `declarada_por: "cliente"`. El servidor no verifica que Google haya respondido.
- **Pruebas ejecutadas y resultados:**
  - `.venv\Scripts\python.exe -m pytest tests/application/test_incorporacion_servicio_dns.py -q`: 31 aprobadas.
  - `.venv\Scripts\python.exe -m pytest tests/api/test_incorporacion_dns_api.py -q`: 22 aprobadas.
  - `.venv\Scripts\python.exe -m pytest -q` (suite completa, con cambios sin commit de otros agentes):
    226 aprobadas, 1 omitida. La línea base previa era 173 aprobadas y 1 omitida.
  - `ruff check` sobre los archivos Python tocados y nuevos: sin errores.
  - `git -c core.whitespace=cr-at-eol diff --check`: sin avisos, código de salida 0.
  - Las pruebas usan bases temporales (`tmp_path`). No se consultó Internet: el endpoint no llama al
    proveedor DNS y las pruebas comprueban que el proveedor no se usa.
  - Verificación manual con base temporal fuera del repositorio: respuesta 200 real, transcrita arriba.
- **No probado:**
  - Concurrencia entre procesos. Solo se probó `BEGIN IMMEDIATE` ocupado con una conexión externa.
  - Un `COMMIT` ocupado dentro de la API.
  - La rama de FK inexistente (500) solo con repositorio falso. No hay prueba de API.
  - La interfaz: `app/frontend/osint.js` no se adaptó. No hay pruebas de navegador.
  - Revisión del Agente 06. Esta entrega no está aprobada.
- **Pendientes, riesgos y bloqueos:**
  - **Agente 05:** adaptar la vista para seleccionar, confirmar y enviar `A` y `AAAA`. Mostrar los
    estados `creada` y `reutilizada`. Presentar la procedencia como declarada. Ante `409`, pedir una
    resolución explícita; el endpoint no ofrece elegir entre coincidencias. Ante `503` con
    `persistencia: confirmada`, ofrecer reintentar sin hablar de deshacer.
  - **Riesgo de duplicados (persistencia, Agente 04 y usuario):** `canonizar_dominio` solo normaliza
    mayúsculas y punto final. Si un DOMINIO ya existe con letras Unicode (por ejemplo `münchen.de`,
    creado por CRUD), la incorporación IDNA `xn--mnchen-3ya.de` no lo reconoce y crea otro DOMINIO.
    Verificado en base temporal: `HTTP 200`, `estado: creada`. Requiere decisión antes de tocar la
    canonicalización. No se modificó la persistencia.
  - **P-01 y P-02 siguen pendientes en DECISIONS.md.** No se actualizó ese archivo: la ficha del
    Agente 03 pide registrar primero una decisión cuando cambia un contrato. Se solicita decidirlo.
  - Confianza en fuente y fecha: son declaradas y no se valida que la fecha no sea futura.
  - La prueba de fallo de reconstrucción usa `app.state.graph_service._graph_loader`, un atributo
    privado, solo para simular el fallo.

### 2026-11-16 · Agente 04 → Agente 03 y coordinación · Implementación de incorporación DNS transaccional

- **Estado:** listo para revisión
- **Objetivo:** persistir un lote DNS A/AAAA ya validado en una única transacción
  `BEGIN IMMEDIATE`, reutilizando o creando DOMINIO, IP, `APUNTA_A` y evidencias, con
  rollback completo ante error. Sin cambios de esquema, sin dependencias, sin tocar la
  API, la aplicación ni el frontend.
- **Archivos modificados:**
  - `app/persistence/database.py`: nueva `transaccion_inmediata` y `es_bloqueo_sqlite`.
    `session_scope`, el engine y los eventos no cambian.
  - `app/persistence/errors.py`: al final, `DatabaseBusyError` y `CoincidenciaAmbiguaError`.
    Ambas heredan de `RepositoryError`.
  - `app/persistence/incorporacion_dns.py` (nuevo): tipos, validación e
    `IncorporacionDnsRepository`.
  - `tests/persistence/test_incorporacion_dns.py` (nuevo): 27 pruebas.
  - `docs/agents/HANDOFF.md`.
  - Sin cambios: `repositories.py`, `mappers.py` y `schema.py`. Los cambios sin commit
    en `repositories.py` y `mappers.py` son de otros agentes y se preservaron.
- **Contratos o decisiones relevantes:**
  - Interfaz para el Agente 03:

    ```python
    from app.persistence.incorporacion_dns import (
        IncorporacionDnsRepository,
        LoteDnsIncorporacion,
        RegistroDnsIncorporacion,
    )

    repo = IncorporacionDnsRepository(session_factory)
    resultado = repo.incorporar_lote(
        LoteDnsIncorporacion(
            dominio="example.com",  # minúsculas, sin punto final
            registros=(
                RegistroDnsIncorporacion(
                    tipo="A",  # "A" o "AAAA"
                    valor="192.0.2.1",  # IP en forma canónica (ipaddress)
                    fuente="google-public-dns-doh",  # declarada por el cliente
                    consultado_en=datetime(2025, 1, 1, 12, tzinfo=timezone.utc),
                ),
            ),
        )
    )
    ```

  - Salida: `resultado.dominio` y, por cada `resultado.resultados[i]`, `tipo`, `valor`,
    `entidad`, `relacion` y `evidencia`. Cada objeto tiene `id` y `estado`, que es
    `"creada"` o `"reutilizada"`.
  - Validación previa a la transacción: `LoteDnsInvalidoError(ValueError)` si el lote
    está vacío, si el dominio o la IP no son canónicos, si el tipo no coincide con la
    versión IP, si la fuente está vacía o tiene espacios de borde, o si la fecha no tiene
    zona horaria. El Agente 03 debe canonicalizar antes; la persistencia no normaliza.
  - La fecha se guarda en UTC (`isoformat()`), así que la idempotencia no depende del
    desfase del cliente.
  - La procedencia se guarda como `evidencia.fuente = "declarada por el cliente: <fuente>"`
    (constante `PREFIJO_PROCEDENCIA_DECLARADA`). Interfaz y respuesta deben presentarla
    como declarada, no como verificada por el servidor.
  - La descripción de la evidencia es `"Consulta DNS <tipo> de <dominio>"`. La relación
    `APUNTA_A` se crea sin fecha.
  - Coincidencias: se comparan `valor` y `valor_normalizado` de cada entidad del tipo,
    canonicalizados (dominio: minúsculas y sin punto final; IP: `ipaddress`). Un valor no
    interpretable nunca coincide. Una coincidencia única se reutiliza y varias lanzan
    `CoincidenciaAmbiguaError`. No se modifican entidades existentes.
  - Idempotencia: relación por (origen, destino, `APUNTA_A`); evidencia por (relación,
    fuente, fecha UTC, descripción). Repetir el lote, o repetir una IP dentro del mismo
    lote, reutiliza todo.
  - Concurrencia: `BEGIN IMMEDIATE` con el timeout actual (5 s por defecto del driver).
    Sin `BEGIN` diferido ni candado en proceso. Las consultas DNS no van dentro de la
    transacción.
  - Desviación respecto de la propuesta: no extraje los `create` de los repositorios CRUD
    a funciones con `Session`. El lote reutiliza `_resolve_entity_type_id`,
    `_resolve_relation_type_id` y `_translate_integrity_error` sin modificarlos, así los
    contratos CRUD quedan intactos.
- **Errores para la capa API (propuesta de mapeo):**

  | Clase | Origen | HTTP propuesto |
  |---|---|---|
  | `LoteDnsInvalidoError` | validación previa, sin escritura | 422 |
  | `CoincidenciaAmbiguaError` | dos o más coincidencias canónicas | 409 |
  | `UniqueConstraintError` | conflicto de unicidad (defensa final) | 409 |
  | `DatabaseBusyError` | `SQLITE_BUSY` o `SQLITE_LOCKED` en `BEGIN` o `COMMIT` | 503 |
  | `ForeignKeyConstraintError` | referencia inexistente, solo por inconsistencia interna | 500 |
  | `RepositoryError` u otra `IntegrityConstraintError` | otro fallo de persistencia | 500 |
  | `GraphReconstructionError` (servicio) | falla tras el commit | 503 con `persistencia: confirmada` |

- **Para el servicio (Agente 03):** el repositorio no reconstruye el grafo. Después de un
  resultado exitoso, el servicio debe llamar a `_refresh_after_write()`. Si falla, la
  persistencia ya está confirmada: responder con error explícito, sin hablar de rollback.
  Un reintento idéntico recupera el grafo sin duplicar nada.
- **Pruebas ejecutadas y resultados:**
  - `pytest tests/persistence/test_incorporacion_dns.py -q`: 27 aprobadas.
  - Las tres pruebas de concurrencia repetidas 10 veces: 3 aprobadas en cada repetición.
  - `pytest tests/persistence -q`: 64 aprobadas.
  - `pytest -q` (suite completa, con cambios sin commit de otros agentes): 173 aprobadas,
    1 omitida.
  - `ruff check` sobre los cuatro archivos Python tocados: sin errores.
  - `git -c core.whitespace=cr-at-eol diff --check`: sin avisos, código de salida 0.
  - Las bases fueron temporales (`tmp_path`). No se abrió ni modificó la base de
    desarrollo ni la de producción.
- **No probado:**
  - Concurrencia entre procesos. Solo hay hilos con dos conexiones en el mismo proceso.
  - Modo WAL y el archivo de producción.
  - CRUD concurrente con el lote.
  - Una prueba dedicada a `COMMIT` ocupado. El bloqueo se prueba en `BEGIN`.
  - Rendimiento con muchas entidades: la búsqueda es lineal por tipo, dentro del lock.
  - Equivalencia con la canonicalización real de dominios IDNA del Agente 03.
  - Mutación del código para confirmar que las pruebas fallan sin el lock.
  - La API y el servicio: no se ejecutaron porque no cambiaron.
- **Pendientes, riesgos y bloqueos:**
  - Agente 03: integrar el caso de uso en el servicio, el endpoint y el mapeo de errores.
    Confirmar que la canonicalización coincide con la de `canonizar_dominio` y `canonizar_ip`.
  - Agente 05: mostrar la procedencia como declarada y los estados `creada` y `reutilizada`.
  - Agente 06: revisar el caso de ambigüedad y la idempotencia antes de aprobar.
  - Pendiente de decisión (P-01, P-02 en `DECISIONS.md`): la regla de identidad y la
    confianza en fuente y fecha declaradas. No actualicé `DECISIONS.md`, que es de otra
    especialidad.
  - Datos existentes en producción podrían tener variantes canónicas duplicadas. No
    revisado; requiere consulta de solo lectura con autorización.

### 2026-11-16 · Agente 04 → Agente 03 y coordinación · Validación del diseño transaccional DNS

- **Estado:** listo para revisión
- **Objetivo:** validar con un experimento aislado el lote atómico para incorporar
  A/AAAA (P-01) y proponer la interfaz de persistencia. No se implementó código del
  repositorio ni se tocó la base de producción.
- **Archivos modificados:** solo `docs/agents/HANDOFF.md`. El experimento está fuera del
  repositorio: `%TEMP%\mmg-exp04\exp_transacciones.py`, con bases temporales y el
  esquema real del proyecto en modo lectura. No se instalaron dependencias ni se hizo
  commit.
- **Contratos o decisiones relevantes:** ninguno cambia. Sin cambios de esquema SQLite,
  sin dependencias nuevas, sin cambios en `session_scope` ni en el engine global.

#### 1. Resultados reales del experimento

Entorno: Python 3.13.3, SQLite 3.49.1, SQLAlchemy 2.1.4. Ejecutado con
`.venv\Scripts\python.exe -I exp_transacciones.py`, el 2026-11-16.

| Caso | Resultado observado |
|---|---|
| `sqlite3.connect` por defecto | `busy_timeout` = 5000 ms |
| Engine del proyecto (`create_sqlite_engine`) | `busy_timeout` 5000 ms, `foreign_keys` 1, `journal_mode` delete (base temporal nueva) |
| R1: c2 `BEGIN IMMEDIATE` con c1 escribiendo (timeout 0,5 s) | `SQLITE_BUSY` «database is locked» tras ~0,6 s; tras el ROLLBACK de c1, c2 entra |
| R2: c1 lee con `BEGIN` diferido, c2 tiene RESERVED, c1 escribe (timeout 5 s) | `SQLITE_BUSY` **inmediato** (0,00 s): no espera el timeout |
| R2b: c2 `COMMIT` mientras c1 sigue leyendo | `SQLITE_BUSY` tras el timeout (~0,6 s); se resuelve con ROLLBACK de c1 |
| R3: FK inexistente dentro de `BEGIN IMMEDIATE` y ROLLBACK | `SQLITE_CONSTRAINT_FOREIGNKEY`; queda solo lo confirmado antes |
| 2a: carrera con la sesión actual (SELECT previo, INSERT después) | Un hilo «creada», el otro `UniqueConstraintError` (409); no hay reutilización |
| 2b: sesión con `BEGIN IMMEDIATE` (comprobar y luego insertar) | El segundo hilo espera ~0,54 s y reutiliza la fila |
| 2c: escritor con `busy_timeout` 300 ms | `OperationalError` `SQLITE_BUSY` tras ~0,42 s; sin escritura parcial |
| 2d: lote con FK inexistente, con UNIQUE y con excepción Python tras flush | Los tres revierten por completo. FK → `ForeignKeyConstraintError`; UNIQUE → `UniqueConstraintError` |
| 2d: lote sin error | commit completo (entidad, IP, relación) |
| 2e: excepción tras el commit (simula fallo de reconstrucción) | Los datos siguen persistidos |
| 2f: dos pasadas idénticas del lote | Pasada 1: 4 creadas. Pasada 2: 4 reutilizadas. Totales: entidad 2, relación 1, evidencia 1 |
| 2f: dos coincidencias canónicas (`Example.COM.` y `EXAMPLE.com`) | Ambigüedad detectada; lote revertido. La unicidad SQL admite ambos textos |

Correcciones a lo registrado antes:

- La entrega 03→04 y la ficha dicen que no hay `busy_timeout`. No hay `PRAGMA`
  explícito, pero el driver aplica **5 s por defecto** (verificado en el engine). Hoy un
  bloqueo espera hasta 5 s y luego cae en `RepositoryError`, porque `OperationalError`
  no es `IntegrityError`; la API responde 500.
- El modo de journal verificado es `delete` en una base nueva. **No se abrió el archivo
  de producción**, así que su modo no está verificado.

#### 2. Diseño recomendado

a. **Sesión compartida sin tocar `session_scope`.** Extraer la lógica de `create` a
   funciones internas `_crear_entidad(session, data)`, `_crear_relacion(session, data)` y
   `_crear_evidencia(session, data)`. Los métodos públicos conservan firma y
   comportamiento; cada uno abre su sesión y llama a la función interna.
b. **Transacción inmediata por sesión.** `sesion.connection(execution_options={"isolation_level": "AUTOCOMMIT"})`
   seguido de `BEGIN IMMEDIATE` manual. Verificado: commit y rollback de la sesión
   funcionan con esta vía. No usar `isolation_level` ni eventos globales en el engine:
   cambiarían todos los repositorios. La nueva función debe llamar a
   `assert_foreign_keys_enabled`, como hace `session_scope`.
c. **Orden dentro de la transacción.** Validar entrada, normalizar dominio e IP y, si
   corresponde, consultar DNS **antes** de abrir la transacción. Dentro: leer candidatos
   canónicos del tipo, detectar ambigüedad, crear o reutilizar entidad, relación y
   evidencia, y luego commit. Las consultas de candidatos deben ir dentro del lock; si
   se hacen antes, hay carrera.
d. **Serialización.** `BEGIN IMMEDIATE` serializa escritores del mismo archivo (hilos o
   procesos); no hace falta un candado en el servicio. Las restricciones únicas quedan
   como última defensa.
e. **Nunca `BEGIN` diferido para el lote.** R2 muestra que un lector que escribe después
   falla de inmediato, sin esperar el timeout.

#### 3. Interfaz propuesta (sin implementar)

```python
# app/persistence/database.py: nueva función, sin cambiar session_scope
@contextmanager
def transaccion_inmediata(session_factory) -> Generator[Session, None, None]: ...

# app/persistence/repositories.py
@dataclass(slots=True)
class RegistroDnsIncorporacion:
    ip: str            # forma canónica, calculada por el Agente 03 (ipaddress)
    fuente: str
    fecha: datetime
    descripcion: str

@dataclass(slots=True)
class LoteDnsIncorporacion:
    dominio: str       # forma canónica, calculada por el Agente 03 (normalizar_dominio)
    registros: tuple[RegistroDnsIncorporacion, ...]

class IncorporacionDnsRepository:
    def incorporar_lote(self, lote: LoteDnsIncorporacion) -> ResultadoIncorporacionDns: ...
```

`ResultadoIncorporacionDns` devuelve, para el dominio y para cada registro, el ID y el
estado (`creada` o `reutilizada`) de entidad IP, relación y evidencia. El repositorio no
reconstruye el grafo: eso lo hace el servicio después del commit.

Clasificación de errores propuesta:

| Origen | Clase | HTTP propuesto |
|---|---|---|
| UNIQUE dentro del lote (defensa final) | `UniqueConstraintError` (existente) | 409 |
| FK inexistente (solo por inconsistencia interna) | `ForeignKeyConstraintError` (existente) | 404 o 500; decidir con Agente 03 |
| `SQLITE_BUSY` o `SQLITE_LOCKED` en `BEGIN IMMEDIATE` o `COMMIT` | nueva `DatabaseBusyError(RepositoryError)` | 503 |
| Coincidencias canónicas múltiples | nueva `CoincidenciaAmbiguaError(RepositoryError)` | 409 |
| Otro `SQLAlchemyError` | `RepositoryError` (existente) | 500 |
| Excepción Python | se revierte y se relanza sin envolver | 500 |
| Fallo de reconstrucción después del commit | `GraphReconstructionError` (servicio) | 503 con `persistencia: confirmada` |

#### 4. Qué pasa si falla la reconstrucción después del commit

La persistencia ya quedó confirmada (verificado en 2e). El servicio actual
(`_refresh_after_write`) invalida el grafo en memoria y lanza error; las consultas
siguientes fallan hasta `reconstruir_grafo()`. La respuesta debe decir que la persistencia
**sí se confirmó** y no hablar de rollback. Un reintento idéntico reutiliza todo (2f) y
no duplica evidencias: sirve para recuperar el grafo.

#### 5. Archivos que requerirán modificación

- Agente 04: `app/persistence/database.py` (`transaccion_inmediata`),
  `app/persistence/repositories.py` (funciones internas y `IncorporacionDnsRepository`),
  `app/persistence/errors.py` (`DatabaseBusyError`, `CoincidenciaAmbiguaError`; hoy hay
  cambios sin commit de otros agentes: preservarlos).
- Agente 03: `app/application/service.py` (caso de uso y reconstrucción única),
  `app/api/dns_routes.py`, `app/api/dns_schemas.py`, `app/api/main.py` (mapeo 409/503).
- Agente 05: `app/frontend/osint.js` y la confirmación de selección.
- Pruebas: `tests/persistence/test_incorporacion_dns.py` (nuevo), `tests/application`,
  `tests/api`.

#### 6. Pruebas necesarias

- **Atomicidad:** FK, UNIQUE, excepción Python y fallo en mitad del lote (con IP ya creada)
  no dejan filas nuevas. Usar `tmp_path`.
- **Concurrencia:** dos hilos con el mismo dominio o IP: una «creada» y otra
  «reutilizada», sin `UniqueConstraintError`. Con `busy_timeout` corto, el lote bloqueado
  responde `DatabaseBusyError` sin escritura parcial. Probar también un CRUD concurrente.
- **Idempotencia:** dos pasadas idénticas; reintento tras fallo de reconstrucción sin
  evidencias duplicadas.
- **Ambigüedad:** dos coincidencias canónicas rechazan todo el lote sin escritura.
- **Clasificación:** cada excepción nueva, y el mapeo HTTP (409, 503, 500).
- **Regresión CRUD:** `tests/persistence` (37 aprobadas hoy) y la suite completa.
- **Servicio:** loader que falla después del commit: 503 con persistencia confirmada y
  recuperación con reintento.

- **Pruebas ejecutadas y resultados:** `.venv\Scripts\python.exe -I exp_transacciones.py`
  desde `%TEMP%\mmg-exp04`, código de salida 0; resultados en la tabla de la sección 1.
  No se ejecutó `pytest` en esta entrega porque no cambió código del repositorio.
- **No probado:** multiproceso; modo WAL; archivo de producción; CRUD concurrente;
  canonicalización real de `normalizar_dominio` y de IP (el experimento usa
  `strip().lower().rstrip('.')`); fechas `datetime` en evidencias (el experimento compara
  texto); COMMIT con `SQLITE_BUSY` dentro de SQLAlchemy; implementación.
- **Pendientes, riesgos y bloqueos:**
  - Bloqueado hasta la aprobación de P-01 y de la regla local de identidad (P-02).
  - El lote mantiene el lock durante la validación en base: debe ser pequeño y sin I/O
    externo.
  - El `busy_timeout` de 5 s es implícito. Decidir si se fija explícitamente; afecta a
    todos los repositorios.
  - Datos ya guardados en producción podrían tener variantes canónicas duplicadas o
    ambiguas. No revisado: requiere una consulta de solo lectura con autorización.
  - Si un CRUD futuro abre `BEGIN` diferido, leer y luego escribir puede fallar de
    inmediato contra el lote (R2).
  - Sin decidir: si la fuente y la fecha declaradas por el cliente bastan para la
    trazabilidad (ver la entrega 03→04).

### 2026-11-16 · Agente 03 → Agente 04 (nuevo) · Contrato de persistencia para incorporación DNS A/AAAA

- **Estado:** aprobado por el usuario; implementado por el Agente 04 (ver la entrega más reciente)
- **Objetivo:** que el nuevo Agente 04 diseñe y, con autorización del usuario,
  implemente el soporte de persistencia que necesita la propuesta de
  incorporación DNS de la entrega siguiente de este archivo (P-01). Registrada
  por el Agente 04 saliente al cerrar su chat; **no se implementó nada**.
- **Archivos modificados:** solo documentación: `docs/agents/agent-04-persistence.md`
  (sección «Continuidad técnica») y este archivo.
- **Requisitos del contrato:**
  1. Una única transacción para crear o reutilizar dominio, IP, relación y
     evidencia.
  2. Rollback completo ante cualquier error.
  3. Búsqueda por valor canónico que permita detectar múltiples coincidencias.
  4. Reutilización de relaciones existentes sin duplicarlas.
  5. Creación de evidencias dentro de la transacción.
  6. Protección frente a incorporaciones concurrentes.
  7. Clasificación correcta de errores de integridad.
  8. Sin cambios en el esquema SQLite.
  9. Sin dependencias nuevas.
  10. Compatibilidad con las operaciones CRUD actuales.
- **Punto de partida verificado en el código:**
  - Cada método de repositorio abre y confirma su propia transacción
    (`session_scope` en `app/persistence/database.py`); no hay forma de
    compartir sesión entre `EntidadRepository`, `RelacionRepository` y
    `EvidenciaRepository`.
  - No hay `BEGIN IMMEDIATE`, `busy_timeout` ni bloqueo en
    `GraphApplicationService`.
  - Unicidad: entidad `(tipo_entidad_id, valor_normalizado)` y relación
    `(origen_id, destino_id, tipo_relacion_id)`; evidencia sin unicidad.
  - Errores existentes: `UniqueConstraintError`, `ForeignKeyConstraintError`,
    `IntegrityConstraintError`, `RecordNotFoundError`, `DataMappingError`,
    `RepositoryError`. Un `IntegrityConstraintError` genérico hoy responde 500.
- **Interfaces y archivos que probablemente cambien (propuesta, a validar):**
  - `app/persistence/repositories.py`: extraer la lógica de `create` a
    funciones internas que reciban una `Session`, usadas por los métodos
    actuales (que conservan firma y comportamiento) y por la operación nueva.
  - Operación transaccional nueva, en `repositories.py` o en un módulo propio
    de `app/persistence`: recibe el lote ya validado por el Agente 03 y ejecuta
    todo dentro de un único `session_scope`. Devuelve, por objeto, el registro
    y si fue creado o reutilizado.
  - Búsqueda canónica: cargar los candidatos del tipo dentro de la sesión y
    compararlos en Python con la forma canónica que provea el Agente 03. SQL no
    puede igualar variantes de mayúsculas, punto final o IPv6 equivalente.
    Devolver la lista completa de coincidencias para que la capa superior
    rechace las ambiguas. No modificar entidades existentes.
  - Concurrencia: iniciar la transacción con un bloqueo de escritura
    (`BEGIN IMMEDIATE` u otro mecanismo equivalente de SQLite) antes de
    comprobar y escribir, y, si hace falta, un candado en proceso en el
    servicio. La técnica exacta con el driver `sqlite3` y SQLAlchemy requiere un
    experimento previo con bases temporales; no está verificada. Las
    restricciones únicas siguen como última defensa.
  - Evidencias: reutilizar la existente con misma relación, fuente, fecha y
    descripción dentro de la transacción; comparar fechas con el mismo formato
    que `serialize_temporal` (`app/persistence/mappers.py`). Sin unicidad en la
    tabla, la idempotencia depende del bloqueo de escritura.
  - `app/persistence/errors.py`: evaluar un error específico para base
    bloqueada o fallo transaccional y un error de coincidencias múltiples, y
    distinguir conflictos por entidad, relación o evidencia, indicando el
    registro causante. Cualquier error nuevo debe heredar de uno existente.
  - Fuera de `app/persistence` (Agente 03): `app/application/service.py`
    (nuevo caso de uso, reconstrucción única del grafo tras el commit y
    manejo de fallo posterior al commit), `app/api/dns_routes.py`,
    `app/api/dns_schemas.py` y `app/api/main.py` (traducción HTTP de errores
    nuevos). El Agente 05 adapta `app/frontend/osint.js`.
  - Pruebas: `tests/persistence` (nuevo archivo para la transacción; cobertura
    de rollback en cada paso, reutilización, ambigüedad, concurrencia con dos
    conexiones a una base temporal, clasificación de errores y no regresión de
    CRUD) y, del lado del Agente 03, `tests/application` y `tests/api`.
- **Pruebas ejecutadas y resultados:** `python -m pytest tests/persistence -q`:
  37 aprobadas, 0 fallidas, 0 omitidas (2026-11-16). No se ejecutó el resto de la
  suite.
- **No probado:** transacción compartida, concurrencia, rollback de lote y
  reutilización: nada de esto existe aún.
- **Pendientes, riesgos y bloqueos:**
  - Bloqueado por la aprobación de P-01 y de la regla local de identidad
    asociada a P-02 (Agente 03 y usuario). No empezar a implementar sin
    autorización expresa.
  - Primero, que el Agente 03 confirme la función de forma canónica de dominio e
    IP y si el lote llega ya validado.
  - Riesgo: `BEGIN IMMEDIATE` con pysqlite y SQLAlchemy puede interactuar con
    el control de transacciones del driver; validar con un experimento antes de
    tocar `database.py`, porque un cambio allí afecta a todos los repositorios.
  - Riesgo: la búsqueda canónica es lineal por tipo; aceptable a escala
    académica, no medida.
  - Riesgo: hay un solo grafo en memoria; otras escrituras concurrentes pueden
    dejarlo desactualizado hasta la siguiente reconstrucción.
  - Riesgo: `IntegrityConstraintError` genérico responde 500 en la API.
  - El árbol de trabajo tiene cambios sin commit de otros agentes, incluidos
    `app/persistence/errors.py`, `app/persistence/mappers.py` y
    `app/domain/entidad.py`; preservarlos.

### 2026-11-16 · Agente 03 → Agentes 04, 05 y 06 · Propuesta de incorporación DNS A/AAAA

- **Estado:** listo para revisión
- **Objetivo:** diseñar la incorporación explícita de registros revisados, sin
  implementar funcionalidad ni alterar la consulta DNS existente.
- **Archivos modificados:** `docs/agents/HANDOFF.md` y `docs/agents/DECISIONS.md`.
- **Contratos o decisiones relevantes:** propuesta sujeta a aprobación de P-01
  y coordinación con Agentes 04 y 05; P-02 sigue pendiente. No cambia SQLite.

  1. El frontend envía solo A y AAAA seleccionados, tras confirmación expresa.
     El backend vuelve a validar el dominio con `normalizar_dominio`, cada IP
     con `ipaddress` y la correspondencia A/IPv4 o AAAA/IPv6. Rechaza lista
     vacía, tipos no admitidos, fecha sin zona horaria y metadatos inválidos;
     deduplica selecciones idénticas y no incorpora estados vacíos ni errores.
     No consulta DNS de nuevo.
  2. Propuesta de identidad, pendiente de P-02: comparar las formas canónicas
     DNS e IP con `valor` y `valor_normalizado` de entidades del mismo tipo,
     sin modificar las existentes. Si hay una sola coincidencia, reutilizarla;
     si hay varias, rechazar todo el lote con 409 para resolución explícita.
     Si no hay coincidencias, crear `DOMINIO` o `IP` con `valor` y
     `valor_normalizado` iguales a la forma canónica. La comparación debe
     contemplar dominio IDNA, mayúsculas y punto final e IPv6 equivalente,
     sin tratar un valor existente no interpretable como coincidencia. Esta
     regla local propuesta no aprueba una normalización global.
  3. Por cada IP crear o reutilizar la terna dirigida
     `DOMINIO --APUNTA_A--> IP`, sin cambiar datos ni evidencias previas.
     A y AAAA representan direcciones obtenidas para la consulta; la relación
     indica resolución, no implica propiedad ni conexión directa verificable.
  4. Adjuntar a la relación `Evidencia` con `fuente`, `fecha` igual a
     `consultado_en` y `descripcion` que identifique tipo y dominio consultado.
     Propuesta de reintento idempotente: reutilizar evidencia con la misma
     relación, fuente, instante y descripción; una consulta posterior con otro
     instante agrega otra evidencia. Las evidencias previas no se alteran.
     La fuente y la fecha recibidas del cliente son **declaradas**, no prueba
     verificable de que Google respondió: la consulta actual no emite un token
     ni guarda resultados. Definir si esta trazabilidad declarada alcanza antes
     de implementar; no atribuirle autenticidad al proveedor.
  5. Propuesta: lote completo atómico, con una única sesión y transacción para
     entidad origen, IP, relaciones y evidencias. Validar todo antes de
     escribir; cualquier error revierte el lote y se identifica el registro
     causante cuando sea posible. Los repositorios actuales abren y confirman
     transacciones propias: encadenar sus `create` no ofrece esta garantía.
     Coordinar con Agente 04 operaciones con sesión compartida, sin cambiar el
     esquema ni romper contratos existentes. Serializar la comprobación y
     escritura frente a incorporaciones concurrentes; conservar las restricciones
     únicas como última defensa y clasificar conflictos o claves foráneas por
     su causa. La tabla de evidencias no tiene restricción de unicidad.
  6. Tras confirmar la transacción, reconstruir una vez el grafo. Si falla la
     reconstrucción, invalidar la proyección como hace el servicio actual y
     responder con error explícito que indique que la persistencia **sí fue
     confirmada**; no afirmar rollback. Un reintento idéntico debe reutilizar
     los datos y permitir recuperar el grafo, sin duplicar evidencias.
  7. Endpoint nuevo propuesto: `POST /api/v1/osint/dns/incorporaciones`.
     El contrato y los nombres requieren acuerdo con Agente 05. Ejemplo:

     ```json
     {
       "dominio": "example.com",
       "registros": [
         {
           "tipo": "A",
           "valor": "192.0.2.1",
           "fuente": "google-public-dns-doh",
           "consultado_en": "2025-01-01T12:00:00Z"
         },
         {
           "tipo": "AAAA",
           "valor": "2001:db8::1",
           "fuente": "google-public-dns-doh",
           "consultado_en": "2025-01-01T12:00:00Z"
         }
       ]
     }
     ```

     Respuesta propuesta, HTTP 200 solo después de confirmar y reconstruir:

     ```json
     {
       "dominio": {"id": 1, "estado": "reutilizada"},
       "resultados": [
         {"tipo": "A", "valor": "192.0.2.1", "entidad": {"id": 2, "estado": "creada"}, "relacion": {"id": 3, "estado": "creada"}, "evidencia": {"id": 4, "estado": "creada"}},
         {"tipo": "AAAA", "valor": "2001:db8::1", "entidad": {"id": 5, "estado": "reutilizada"}, "relacion": {"id": 6, "estado": "reutilizada"}, "evidencia": {"id": 7, "estado": "reutilizada"}}
       ]
     }
     ```

     Los estados `creada` y `reutilizada` se refieren a cada objeto. Propuesta
     de errores: 422 para datos inválidos, 409 para ambigüedad o conflicto de
     unicidad no recuperable, 404 para referencias explícitas inexistentes si
     se incorporan al contrato, y 500 para fallos internos. Las claves foráneas
     se clasifican según su causa, no automáticamente como unicidad. Para
     fallo de reconstrucción posterior al commit, proponer 503 con
     `{"detail":"Grafo no disponible","persistencia":"confirmada"}`; su
     integración con los manejadores existentes requiere acuerdo. Sin fallo,
     ningún resultado individual queda a medio guardar.

- **Archivos previstos para una implementación posterior:** servicio de
  aplicación y `app/application/service.py`; `app/persistence/repositories.py`
  y posiblemente errores o unidad transaccional, con Agente 04;
  `app/api/dns_routes.py`, `app/api/dns_schemas.py` y eventualmente
  `app/api/main.py`; pruebas de aplicación, persistencia y API. El Agente 05
  deberá adaptar `app/frontend/osint.js` y la interfaz tras acordar el contrato.
- **Pruebas ejecutadas y resultados:** inspección estática del código y
  `git status --short --branch`; rama `feature/project-expansion` con cambios
  pendientes. No se ejecutaron pruebas: entrega documental.
- **No probado:** concurrencia, rollback, recuperación tras commit, contrato
  propuesto y comportamiento del frontend; todavía no están implementados.
- **Pendientes, riesgos y bloqueos:** aprobar P-01 y la regla local asociada a
  P-02; decidir la confianza aceptable en fuente/fecha declaradas y los límites
  del lote. La vista actual marca «Revisado», no confirma incorporación; hay
  que acordar la selección y confirmación con Agente 05. La respuesta DNS actual
  descarta el nombre de cada `Answer` y CNAME intermedios: no permite afirmar
  que el dominio consultado es el propietario directo del registro A/AAAA.
  La unicidad SQLite compara el texto persistido, por lo que la búsqueda
  canónica y los casos ambiguos requieren coordinación; otras escrituras
  concurrentes pueden afectar la proyección del grafo. Agente 06 debe revisar
  los casos de duplicados, fallos y reintentos antes de aprobar.

### 2026-11-04 · Agente 05 → Agente 06 · Correcciones UX de OSINT DNS

- **Estado:** listo para revisión
- **Objetivo:** dos mejoras acotadas tras la auditoría aprobada del Agente 06.
  1. Si la respuesta HTTP es exitosa pero el cuerpo no es JSON válido, mostrar
     un mensaje amigable en español sin exponer el mensaje del parser.
  2. Al terminar la consulta DNS (éxito, error o timeout), devolver el foco al
     botón "Consultar DNS"; si estuviera deshabilitado, al campo Dominio.
- **Archivos modificados:** `app/frontend/osint.js`.
- **Contratos o decisiones relevantes:** ninguno cambió. No se tocó backend,
  contratos de API, SQLite, modelos ni el uso de `sessionStorage`.
- **Pruebas ejecutadas y resultados:**
  - `pytest -q`: 146 aprobadas y 1 omitida.
  - `node --check app/frontend/osint.js`: pasó.
  - Navegador, con respuestas simuladas del endpoint y el timeout reducido a
    0,3 s para la prueba: JSON malformado, HTML con HTTP 200, HTTP 500, error de
    red, timeout y éxito válido. En todos los casos el foco quedó en el botón
    "Consultar DNS".
  - `git diff --check` sobre `osint.js`: sin avisos.
- **No probado:** no se agregó una prueba automatizada específica para estas dos
  correcciones. El foco con el botón deshabilitado (rama hacia el campo Dominio)
  no se ejercitó.
- **Pendientes, riesgos y bloqueos:** sugerida una prueba automatizada para
  ambos comportamientos. Sin bloqueos.
