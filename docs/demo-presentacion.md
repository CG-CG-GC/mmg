# Demostración guiada para la defensa

Este recorrido se puede ejecutar en vivo en unos 12 a 15 minutos. Usa una base de
demostración separada, creada por un script, de modo que tus datos reales no se
modifican. Para la explicación oral, consultá [presentacion-oral.md](presentacion-oral.md).
El manual de referencia está en [manual-usuario.md](manual-usuario.md).

Los valores de ejemplo corresponden a una base nueva creada con el script. Los
identificadores (`#1`, `#8`, `#10`) dependen de esa base; si cambian, las
listas de la interfaz muestran el número real.

## Paso 0. Preparar el entorno (antes de la clase)

Hacelo al menos una vez antes de la exposición. Desde la raíz del proyecto, en
PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado esperado: `No broken requirements found.` y `368 passed, 1 skipped`.
Si `pytest` falla, no sigas con la demostración: primero corregí el entorno.

Luego creá la base de demostración:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_demo.py
```

El script imprime la ruta del archivo nuevo, algo como
`C:\Users\...\AppData\Local\Temp\mmg-demo-xxxxxxxx.sqlite3`. Copiala: la vas a
usar en el paso 1.

Resultado esperado:

- `Entidades: 9 · Relaciones: 9 · Evidencias: 2`.
- Ningún cambio en `data\mmg.sqlite3`.

**Cada ejecución del script crea una base nueva.** Nunca reutiliza un archivo
existente, así que no hay duplicados. Si necesitás repetir la demo con la misma
ruta, primero borrá ese archivo a mano; el script se niega a sobrescribirlo y
también se niega a usar `data\mmg.sqlite3`.

## Paso 1. Iniciar el servidor

En una terminal de VS Code, reemplazando la ruta por la que imprimió el script:

```powershell
$env:MMG_DATABASE_PATH = "C:\Users\...\AppData\Local\Temp\mmg-demo-xxxxxxxx.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Resultado esperado: la terminal muestra que el servidor está escuchando en
`http://127.0.0.1:8000`. Dejala abierta durante toda la demostración.

Si la activación de PowerShell está bloqueada, no hace falta activar el entorno:
los comandos ya usan la ruta completa.

## Paso 2. Abrir la aplicación

1. En el navegador, abrí `http://127.0.0.1:8000/`.
2. Verificá el estado: `http://127.0.0.1:8000/health` debe mostrar `{"status":"ok"}`.
3. Resultado esperado en la página: el mensaje **Datos actualizados.** y el contador
   **9 entidades · 9 relaciones**.

Mostrá el grafo y señalá las flechas. Explicá que la dirección importa.

## Paso 3. Crear una entidad

Entradas exactas, en **03 / Entidades**:

| Campo | Valor |
| --- | --- |
| Tipo | Persona |
| Valor | `Carla Demo` |
| Valor normalizado | `carla-demo` |
| Descripción | `Persona ficticia creada durante la demostración.` |

1. Hacé clic en **Crear entidad**.
2. Aceptá **"Esta acción guardará datos en el proyecto. ¿Continuar?"**.

Resultado esperado: **"Entidad creada."**, el contador pasa a **10 entidades** y
aparece `Carla Demo · Persona (#10)` en las listas.

Explicá qué significa `valor_normalizado`: el sistema no lo calcula; lo ingresa el usuario.

## Paso 4. Crear una relación

Entradas exactas, en **04 / Relaciones**:

| Campo | Valor |
| --- | --- |
| Origen | `Carla Demo · Persona (#10)` |
| Tipo | Pertenece a |
| Destino | `Universidad Demo · Organización (#4)` |
| Descripción | `Carla pertenece a la universidad ficticia.` |

1. Hacé clic en **Crear relación** y aceptá la confirmación.

Resultado esperado: **"Relación creada."** y el contador **10 entidades · 10 relaciones**.

Explicá: la relación `Carla → Pertenece a → Universidad` es una flecha de Carla
hacia la universidad. Si la invertís, sería otra relación.

## Paso 5. Seleccionar, inspeccionar y editar

1. Abrí **Explorar elementos en una lista** y hacé clic en `Ana Demo · Persona (#1)`.
   Resultado: el inspector muestra tipo, valor, valor normalizado y descripción.
2. Hacé clic en la relación `Ana Demo · Persona (#1) → Trabaja en → Laboratorio Ejemplo`.
   Resultado: el inspector muestra origen, tipo, destino, fecha y **Evidencias 1**.
3. Seleccioná `Carla Demo · Persona (#10)`, hacé clic en **Editar entidad** y, en
   **Descripción**, escribí `Persona ficticia. Descripción actualizada en la demostración.`
4. Hacé clic en **Guardar cambios** y aceptá la confirmación.

Resultado esperado: **"Entidad #10 actualizada."**. El identificador no cambia.

## Paso 6. Mostrar distintos layouts

En **Distribución**, elegí en orden y observá el grafo después de cada cambio:

1. Fuerzas · agrupa lo conectado.
2. Jerárquica · sigue la dirección. Es la más clara para explicar las flechas.
3. Concéntrica · centro por grado.
4. Círculo · orden uniforme.
5. Cuadrícula · lectura ordenada.

Resultado esperado: solo cambian las posiciones. Los contadores y las listas no
cambian. Dejá **Jerárquica** para los pasos siguientes.

## Paso 7. Ejecutar BFS

En **05 / Algoritmos**:

| Campo | Valor |
| --- | --- |
| Algoritmo | BFS · recorrido por niveles |
| Entidad inicial | `Ana Demo · Persona (#1)` |

Hacé clic en **Ejecutar algoritmo**.

Resultado esperado, en la lista del resultado:

- Ana Demo · nivel 0.
- Laboratorio Ejemplo, correo y usuario · nivel 1.
- Universidad Demo, portal · nivel 2.
- `example.com` · nivel 3.

Explicá que BFS usa una cola (FIFO) y que el nivel es la cantidad mínima de
relaciones. Mostrá que el grafo resalta los nodos visitados.

## Paso 8. Ejecutar DFS

| Campo | Valor |
| --- | --- |
| Algoritmo | DFS · recorrido en profundidad |
| Entidad inicial | `Ana Demo · Persona (#1)` |

Hacé clic en **Ejecutar algoritmo**.

Resultado esperado en la lista: el orden de visita baja por una rama (Laboratorio,
Universidad, portal, `example.com`) antes de volver a Ana y visitar correo y usuario.

Explicá la diferencia con BFS: DFS entra en profundidad y usa la pila de llamadas
(recursión). Mencioná la limitación de la sección 27 del manual si preguntan.

## Paso 9. Encontrar un camino más corto

| Campo | Valor |
| --- | --- |
| Algoritmo | Camino más corto · por cantidad de relaciones |
| Entidad inicial | `Ana Demo · Persona (#1)` |
| Entidad destino | `example.com · Dominio (#8)` |

Hacé clic en **Ejecutar algoritmo**.

Resultado esperado: **"Camino dirigido encontrado: 3 relación(es)."** con la lista
Ana Demo → Laboratorio Ejemplo → portal → example.com. El grafo resalta esas
relaciones.

Para mostrar que la dirección importa, invertí origen y destino (origen `example.com`,
destino `Ana Demo`). Resultado esperado: **"No existe un camino dirigido entre las
entidades seleccionadas."**

## Paso 10. Consultar un dominio de demostración

En **06 / OSINT DNS**:

| Campo | Valor |
| --- | --- |
| Dominio | `example.com` |
| Tipos | A, AAAA, CNAME, MX y NS (todos marcados) |

Hacé clic en **Consultar DNS**.

**Antes de la clase, decidí qué modo usás:**

- **Con red (consulta real):** la vista previa muestra lo que devuelva Google
  Public DNS en ese momento. Los valores pueden ser distintos de los de las capturas.
  No prometas valores concretos.
- **Sin red:** según el código, la vista muestra **Error de red** o **Error de timeout**
  por tipo. Esto no se pudo verificar en esta entrega porque no se consultó Internet;
  probalo antes de la clase. Si ocurre, explicá que es el comportamiento esperado:
  el servidor no inventa datos y lo informa por tipo.

Las capturas del manual usan una respuesta **simulada** que el navegador interceptó
(fuente `simulacion-demo-sin-red`). Esa simulación no se puede reproducir en vivo
sin una herramienta de interceptación. Decilo si lo mostrás: nunca presentes esas
capturas como datos obtenidos en vivo de Internet.

Resultado esperado: el aviso **"No se guardó nada. No se crearon entidades,
relaciones ni evidencias."** y, por tipo, el estado y los registros.

## Paso 11. Revisar los resultados DNS

Revisá cada registro:

- el valor (IP, nombre de host o prioridad en MX);
- el estado (Encontrado o Sin registros);
- la fuente y la fecha;
- la marca **Posible duplicado**, si aparece.

Con la base de demostración, `example.com` aparece como **Posible duplicado: ya
existe la entidad #8**. Explicá que es una heurística de la vista, no una decisión
del servidor.

## Paso 12. Seleccionar A y AAAA

Solo A y AAAA se pueden incorporar. Para cada uno, en orden:

1. Marcá **Revisado**.
2. Marcá **Incorporar al grafo**.

Resultado esperado: **"Seleccionados para incorporar: 2 registros (A: 1, AAAA: 1)."**.
Mostrá que MX y NS no tienen control de incorporación.

## Paso 13. Confirmar la incorporación

1. Hacé clic en **Revisar incorporación**. Resultado: un panel con el dominio de
   origen, los dos registros y la procedencia declarada por el cliente.
2. Hacé clic en **Confirmar incorporación**.

Resultado esperado: **"Incorporación completada. El grafo muestra los datos
guardados."** y el panel de resultado:

- Dominio `example.com`: **reutilizado** (ya existía como #8).
- Entidades IP: **Creadas: 2 · Reutilizadas: 0**.
- Relaciones APUNTA_A: **Creadas: 2 · Reutilizadas: 0**.
- Evidencias: **Creadas: 2 · Reutilizadas: 0**.
- Procedencia: *Declarada por el cliente ... El servidor no verificó esta consulta.*

Explicá la transacción: el lote se guarda completo o nada.

## Paso 14. Mostrar el grafo actualizado

Resultado esperado: el contador pasa a **12 entidades · 12 relaciones**. Aparecen
las IP nuevas conectadas a `example.com` con la relación **Apunta a**.

Mostrá también los contadores por tipo: IP pasa a 3 y Apunta a a 4.

## Paso 15. Mostrar cómo se evita duplicar elementos

Tres demostraciones, en este orden:

1. **En el CRUD:** en **03 / Entidades**, elegí Tipo **Dominio**, Valor `example.com`,
   Valor normalizado `example.com`, y hacé clic en **Crear entidad** (aceptá la
   confirmación). Resultado: **"Ya existe una entidad con el mismo tipo y valor
   normalizado."** (409). No se crea nada.
2. **En la incorporación:** el dominio se reutilizó en el paso 13 en lugar de crear
   uno nuevo.
3. **Por API (repetición del mismo lote):** en otra terminal de PowerShell, con el
   servidor en marcha:

   ```powershell
   $b = @{ dominio = "example.com"; registros = @(
     @{ tipo = "A"; valor = "192.0.2.1"; fuente = "simulacion-demo-sin-red"; consultado_en = "2026-11-18T12:00:00Z" },
     @{ tipo = "AAAA"; valor = "2001:db8::1"; fuente = "simulacion-demo-sin-red"; consultado_en = "2026-11-18T12:00:00Z" }
   ) } | ConvertTo-Json -Depth 5
   Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/osint/dns/incorporaciones -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($b))
   ```

   Resultado esperado: el dominio, las entidades, las relaciones y las evidencias
   figuran como `reutilizada`. El grafo sigue con 12 entidades.

   Este comando repite datos de la simulación. Si usás consulta real en el paso 10,
   reemplazá los valores por los que mostró la vista previa, o no lo ejecutes.

## Paso 16. Explicar las evidencias y la procedencia

Mostrá la relación de Ana que tiene evidencia. En el navegador, abrí
`http://127.0.0.1:8000/api/v1/relaciones/1`. Resultado esperado: un JSON con
`"evidencias":[{"id":1,"fuente":"Ficha ficticia de la demostración", ...}]`.

Explicá la diferencia entre:

- **Evidencia:** registro de una fuente asociada a una relación.
- **Procedencia declarada:** la fuente y la fecha las informó el cliente. Las
  evidencias de la incorporación llevan el prefijo `declarada por el cliente: `.
  El servidor no volvió a consultar el DNS.

## Paso 17. Reiniciar y comprobar la persistencia

1. En la terminal del servidor, presioná `Ctrl+C`.
2. Iniciá de nuevo el mismo comando del paso 1 (con la misma variable `MMG_DATABASE_PATH`).
3. Actualizá la página.

Resultado esperado: los 12 elementos y las relaciones siguen presentes. El grafo
se reconstruye desde SQLite.

## Conclusiones académicas (cierre, 1 minuto)

- Un grafo dirigido representa relaciones con sentido, y las flechas condicionan
  los recorridos.
- BFS encuentra el camino con menor cantidad de relaciones; DFS recorre en
  profundidad. Ambos son O(V + E) en tiempo.
- La persistencia usa restricciones SQL y transacciones para evitar datos a medias.
- La incorporación DNS separa consulta, revisión y escritura; deja trazabilidad y
  declara lo que no verifica.
- Las limitaciones (IDNA 2008, CRUD con equivalencias, un solo proceso, CNAME/MX/NS
  sin incorporación, DFS recursivo) están documentadas.

## Plan alternativo si falla algo

| Falla | Qué hacer |
| --- | --- |
| El servidor no inicia: puerto ocupado | Usá otro puerto: `--port 8001` y abrí `http://127.0.0.1:8001/`. |
| El servidor no inicia: `MMG_DATABASE_PATH` no existe o no es escribible | Ejecutá de nuevo `scripts\preparar_demo.py` y usá la ruta nueva que imprime. |
| PowerShell bloquea la activación del entorno | No la uses: el comando con la ruta completa `.\.venv\Scripts\python.exe` funciona igual. |
| La página no carga o dice "No se pudo conectar con el servidor" | Revisá que la terminal del servidor siga abierta. Reiniciala con el paso 1. |
| No hay red o la consulta DNS falla | Seguí el paso 10 en modo sin red. Mostrá las capturas de [manual-usuario.md](manual-usuario.md) (figuras 13 a 18) como respaldo, aclarando que son simulaciones. |
| El navegador no abre o muestra una página en blanco | Usá otro navegador o recargá con `F5`. Si persiste, mostrá el JSON de `/api/v1/grafo` en la pestaña. |
| Un clic no hace nada | Revisá el mensaje en la barra de estado; si la base no responde, reiniciá el servidor. |
| Se alteró la base de la demo | Ejecutá `scripts\preparar_demo.py` de nuevo: crea una base nueva sin tocar la anterior. |

Si el navegador falla por completo, las pruebas automatizadas y las capturas
respaldan lo que se explica: podés mostrar `pytest` (368 aprobadas) y el manual.
