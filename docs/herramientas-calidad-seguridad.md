# Herramientas de calidad y seguridad

Guía práctica para ejecutar, interpretar y reutilizar los controles de Mini-Maltego.
Las herramientas están acotadas al proyecto: se instalan en `.venv` y en la carpeta
del repositorio, nunca de forma global.

## 1. Qué resuelve cada herramienta

| Herramienta | Problema que resuelve | Dónde se configura |
| --- | --- | --- |
| **Ruff** | Errores reales (imports sin uso, nombres indefinidos, sintaxis) y formato uniforme. | `ruff.toml` |
| **Bandit** | Patrones inseguros en el código Python (por ejemplo, `eval`, `subprocess` con `shell=True`, SQL armado con texto). | `bandit.yaml` y opciones de la línea de comandos |
| **pip-audit** | Vulnerabilidades conocidas en las dependencias declaradas. | `requirements.txt` y `requirements-dev.txt` |
| **pytest** | Regresiones: la suite confirma que el comportamiento existente sigue igual. | `tests/` |
| **GitHub Actions** | Ejecuta los controles anteriores en cada push y pull request. | `.github/workflows/calidad.yml` |
| **Anti-Slop** | Reglas para agentes de programación e interfaces: evita texto, comentarios y diseño genéricos. No verifica seguridad ni corrección. | `.agents/skills/`, referenciadas desde `AGENTS.md` |

## 2. Entorno y alcance de instalación

- **Python:** el proyecto usa `.venv` con Python 3.13. Las herramientas Python se instalan
  solo en ese entorno con `pip`.
- **Node.js y npm:** se requieren solo para instalar Anti-Slop con `npx`. La aplicación
  no depende de Node.
- **Dependencias separadas:**
  - `requirements.txt`: solo lo necesario para ejecutar la aplicación (FastAPI, SQLAlchemy, uvicorn).
  - `requirements-dev.txt`: incluye `requirements.txt` y agrega pytest, httpx2, Ruff, Bandit y pip-audit.

## 3. Instalar en un proyecto nuevo

1. Crear el entorno y las dependencias de desarrollo (PowerShell, desde la raíz):

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```

2. Copiar `ruff.toml`, `bandit.yaml` y `.github/workflows/calidad.yml`. Ajustar:
   - `line-length` y `target-version` de `ruff.toml` según la convención del equipo.
   - Las rutas `app` y `tests` y los branches del workflow.
   - La versión de Python del workflow.

3. Instalar Anti-Slop solo para el proyecto (sin `-g`, que sería global):

   ```powershell
   npx skills add miqdadbadjuber/anti-slop -s antislop -s antislop-code -s antislop-ui --copy -y
   ```

   - `--copy` evita enlaces simbólicos en el repositorio.
   - Este método copia las carpetas `antislop*` en `.agents/skills/` y `.claude/skills/`
     y crea `skills-lock.json` en la raíz. En Mini-Maltego, `.agents/skills/` es la ubicación
     versionada y usada por el puntero de VS Code; la copia de `.claude/skills/` es regenerable
     y no se necesita para ese flujo. No escribe el puntero en `AGENTS.md`: ese paso se hace
     a mano (paso 4). No usar `npx antislop-ai` sin revisión: su opción
     "Everywhere" escribe en el home, fuera del proyecto.
   - Para actualizar: `npx skills update -p -y`.
   - Para quitar: borrar las carpetas `antislop*` de `.agents/skills/` y `.claude/skills/`,
     el bloque `antislop` de `AGENTS.md` y `skills-lock.json`, si ya no hay otras skills.

4. Agregar el puntero a `AGENTS.md` en la raíz. Si el archivo ya existe, agregar el bloque
   al final sin modificar el contenido previo. Plantilla:

   ```md
   <!-- antislop:start -->
   ## antislop

   Para trabajo de interfaz, textos o comentarios de código, aplicá las reglas de antislop:

   - Núcleo, siempre: `.agents/skills/antislop/SKILL.md`
   - Interfaz visual (`app/frontend/`): `.agents/skills/antislop-ui/SKILL.md`
   - Comentarios de código: `.agents/skills/antislop-code/SKILL.md`

   Estas reglas no reemplazan las pruebas ni los controles de `docs/herramientas-calidad-seguridad.md`.
   <!-- antislop:end -->
   ```

   Ajustar las rutas de la plantilla a las skills realmente instaladas en el proyecto.
   Los marcadores permiten reconocer el bloque y reemplazarlo en vez de duplicarlo.

## 4. Configuración

### Ruff (`ruff.toml`)

- `line-length = 100`: el código existente usa líneas de hasta 111 caracteres. Con el valor
  por defecto (88) habría 28 archivos que reformatear; con 100 hay 14.
- `select = ["E4", "E7", "E9", "F", "B"]`: errores reales y patrones de bugs.
- `I` (orden de imports) **no** está activado: reordenar imports obliga a tocar archivos
  sin aportar seguridad ni corrección. Puede activarse en un cambio dedicado.
- El formato (`ruff format`) se verifica en CI pero **no bloquea** todavía. Se vuelve bloqueante
  después de formatear el repositorio en un cambio aparte y revisado.

### Bandit (`bandit.yaml`)

- Excluye `.venv`, `.git`, cachés, `data/` y las carpetas de skills. Esto evita escanear
  código de terceros si alguien ejecuta `-r .`.
- Se analiza la aplicación (`app`) sin excepciones.
- Las pruebas (`tests`) se analizan con `-s B101`, porque `assert` es el mecanismo normal
  de las pruebas y generaría ruido sin riesgo real.

### pip-audit

- Audita los archivos declarados (`-r requirements-dev.txt`), no el `.venv` completo. Así el
  resultado es reproducible y no mezcla paquetes instalados a mano.
- Para detectar paquetes instalados y no declarados, ejecutar `python -m pip_audit` sin `-r`
  y revisar cada hallazgo. Hoy no hay hallazgos en el `.venv`.

## 5. Comandos

Desde la raíz del proyecto (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m bandit -c bandit.yaml -r app
.\.venv\Scripts\python.exe -m bandit -c bandit.yaml -r tests -s B101
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt --progress-spinner off
.\.venv\Scripts\python.exe -m pytest -q
```

El workflow ejecuta exactamente estos comandos en Linux con Python 3.13. El paso de formato
tiene `continue-on-error: true`.

## 6. Interpretar los resultados

- **Ruff**
  - `F401`: import sin uso. Eliminarlo a mano.
  - `F821`: nombre indefinido; es un error real.
  - `E9`: error de sintaxis o de lectura de archivos; bloquea.
  - `B`: patrón propenso a bugs; revisar el caso antes de corregir.
  - `# noqa: CODIGO` solo con un motivo escrito al lado.
  - No usar `ruff check --fix` sobre todo el repositorio. Si se necesita un fix, revisar `ruff check --diff <archivo>`.
- **Ruff format**: "N files would be reformatted" es informativo. Para ver los cambios de un archivo, usar `ruff format --diff <archivo>`.
- **Bandit**
  - Cada hallazgo indica severidad y confianza. Un hallazgo de severidad alta o confianza alta en `app/` debe corregirse o justificarse.
  - `B101` en `tests/` es esperado.
  - `# nosec` solo con justificación y el código de la regla, nunca como silencio general.
- **pip-audit**
  - Indica paquete, versión, identificador de vulnerabilidad y versión corregida, si existe.
  - Corrección: subir el límite mínimo en `requirements*.txt` a la versión corregida, sin
    cambiar otros paquetes, y repetir la auditoría y la suite.
  - "No known vulnerabilities found" es el resultado esperado.
- **pytest**: cualquier fallo es regresión hasta demostrar lo contrario. No marcar pruebas como omitidas para pasar el control.

## 7. Integración con agentes de VS Code y GitHub

- Anti-Slop y el puntero de `AGENTS.md`: Copilot y Codex leen `AGENTS.md` desde la raíz del
  repositorio (según la documentación de VS Code, sin configuración adicional en el harness de Copilot).
  El puntero indica dónde están las skills, así que el agente las abre cuando la tarea lo requiere.
  Para confirmar que se aplica, pedir al agente algo que solo respondería la regla (por ejemplo,
  "¿qué dice la regla R-02 de antislop?"). Las instrucciones se cargan al iniciar una sesión;
  si no aparecen, abrir una sesión nueva.
- Antes de cerrar un cambio, pedir al agente que ejecute los comandos de la sección 5
  y que informe el resultado real. Un agente no debe declarar un control como aprobado si no lo ejecutó.
- Anti-Slop puede preguntar en cada sesión si se aplica "durante" o "después" del trabajo.
  Guardar esa preferencia con `npx antislop-ai --mode during` escribe en `%APPDATA%`
  (fuera del proyecto, afecta a todos los proyectos). Es una decisión del usuario y no
  la aplica este proyecto.
- GitHub, requisito antes de integrar en `main` (pendiente hasta que el workflow se suba y se ejecute):
  1. Subir la rama con el workflow y esperar a que el job termine al menos una vez.
     GitHub solo ofrece como control requerido un check que ya se haya ejecutado.
  2. Settings > Rules > Rulesets (o Settings > Branches, según la interfaz de GitHub vigente; los nombres de menú pueden variar) > crear una regla para `main`.
  3. Activar "Require status checks to pass" y seleccionar **"Lint, seguridad y pruebas"**.
  4. Opcional: activar "Require branches to be up to date before merging".
  5. Guardar. Sin esta regla, el workflow informa pero no impide el merge.

## 8. Controles antes de cada commit y pull request

**Antes de cada commit** (rápido):

1. `ruff check .`
2. `bandit -c bandit.yaml -r app`
3. `pytest -q`
4. `git diff --check` y revisar que no se incluyan `data/`, `*.sqlite3` ni secretos.

**Antes de cada pull request** (completo):

1. Todo lo anterior, más `bandit -c bandit.yaml -r tests -s B101` y `pip_audit`.
2. `ruff format --check` sobre los archivos cambiados (`ruff format --check <archivos>`).
3. Confirmar que el workflow "Calidad y seguridad" está verde en el PR.

## 9. Qué es reutilizable y qué es específico de Mini-Maltego

| Reutilizable en otro proyecto | Específico de Mini-Maltego |
| --- | --- |
| Estructura de `ruff.toml`, `bandit.yaml` y el workflow. | Rutas `app` y `tests`, y `-s B101` para pruebas. |
| División `requirements.txt` / `requirements-dev.txt`. | Versiones concretas de FastAPI, SQLAlchemy y uvicorn. |
| Orden de controles antes de commit y PR. | Límite de 100 columnas, elegido para el código actual. |
| Instalación de Anti-Slop con `npx skills add ... --copy`. | Skills `antislop-ui` y `antislop-code` elegidas para este proyecto. |
| Plantilla de puntero en `AGENTS.md` con marcadores `antislop:start/end`. | Rutas de las skills instaladas en este proyecto. |
| Uso de `.venv` local y no global. | Tests que usan `MMG_DATABASE_PATH` temporal para proteger `data/mmg.sqlite3`. |

## 10. Línea base (31/10/2026)

| Control | Estado actual del worktree | Estado commiteado (HEAD + archivos de esta tarea) |
| --- | --- | --- |
| `ruff check .` | Sin errores (bloqueante). | Sin errores. |
| `ruff format --check .` | 14 archivos pendientes (informativo). | No evaluado. |
| `bandit ... -r app` | Sin hallazgos. | Sin hallazgos. |
| `bandit ... -r tests -s B101` | Sin hallazgos. | Sin hallazgos. |
| `pip_audit -r requirements-dev.txt` | Sin vulnerabilidades conocidas. | No evaluado. |
| `pip_audit` (entorno completo) | Sin vulnerabilidades (tras desinstalar `pypdf`). | No aplica. |
| `pytest -q` | 84 aprobadas, 0 fallidas. | 61 aprobadas, 0 fallidas. |

La diferencia de pruebas se debe a `tests/persistence/test_*_update.py`, que no están commiteados.
Estos valores son una referencia. Cada cambio debe volver a ejecutar los controles.

Pendiente de GitHub: el workflow "Calidad y seguridad" aún no se ejecutó en GitHub; las
verificaciones de esta tabla son locales (Windows).
