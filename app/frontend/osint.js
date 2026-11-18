"use strict";

// Vista previa de OSINT DNS. La consulta solo lee. La incorporación envía el lote elegido a
// POST /api/v1/osint/dns/incorporaciones y luego actualiza el grafo con refresh(). Depende de
// $, api, message, refresh y state de app.js, y de las funciones de osint-incorporacion.js.
(() => {
  const dnsTypes = {
    A: "dirección IPv4",
    AAAA: "dirección IPv6",
    CNAME: "alias de otro nombre",
    MX: "servidores de correo",
    NS: "servidores de nombres",
  };
  // Tipo de entidad equivalente, solo para detectar duplicados en la vista previa.
  const equivalentEntityType = { A: "IP", AAAA: "IP", CNAME: "DOMINIO", MX: "DOMINIO", NS: "DOMINIO" };
  const statusInfo = {
    ok: ["Encontrado", "ok", ""],
    encontrado: ["Encontrado", "ok", ""],
    sin_registros: ["Sin registros", "neutral", "La consulta funcionó, pero el dominio no publica registros de este tipo. No se genera ninguna entidad."],
    dominio_inexistente: ["Dominio inexistente", "warn", "El proveedor indica que el dominio no existe."],
    error_timeout: ["Error de timeout", "error", "El proveedor no respondió a tiempo. Podés reintentar la consulta."],
    error_red: ["Error de red", "error", "El servidor no pudo conectarse con el proveedor DNS."],
    error_http: ["Error HTTP", "error", "El proveedor respondió con un error HTTP."],
    error_respuesta: ["Error de respuesta", "error", "La respuesta del proveedor no era válida y se ignoró."],
    error_dns: ["Error DNS", "error", "El proveedor devolvió un código de error DNS."],
  };
  const storageKey = "mmg.osint.preview";
  const requestTimeoutMs = 40000;
  const incorporationTimeoutMs = 30000;
  const maxDomainLength = 512;

  let busy = false;
  let incorporating = false;
  // Un fallo dejó el grafo sin confirmar: no se envía otro lote hasta actualizarlo.
  let graphPending = false;
  // reviewed, selected e incorporated son Set de claves de registro (ver recordKey).
  let preview = null; // { result, reviewed, selected, incorporated }

  function el(tag, attributes = {}, ...children) {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attributes)) {
      if (name === "className") node.className = value;
      else if (name === "text") node.textContent = value;
      else node.setAttribute(name, value);
    }
    node.append(...children);
    return node;
  }

  function plural(count, singular, pluralForm) {
    return `${count} ${count === 1 ? singular : pluralForm}`;
  }

  function isText(value) { return typeof value === "string"; }
  function isCount(value) { return Number.isInteger(value) && value >= 0; }

  // La respuesta es externa: se valida la forma completa antes de mostrarla.
  function validResult(data) {
    if (!data || typeof data !== "object") return false;
    if (!isText(data.dominio) || !isText(data.fuente) || !isText(data.consultado_en)) return false;
    if (!Array.isArray(data.registros) || !Array.isArray(data.estados)) return false;
    const recordsOk = data.registros.every((r) => r && isText(r.tipo) && isText(r.valor)
      && isText(r.estado) && isText(r.fuente) && isText(r.consultado_en)
      && (r.prioridad === null || r.prioridad === undefined || isCount(r.prioridad)));
    const statesOk = data.estados.every((s) => s && isText(s.tipo) && isText(s.estado) && isCount(s.descartados));
    return recordsOk && statesOk;
  }

  function formatDate(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleString("es-AR", { dateStyle: "medium", timeStyle: "long" });
  }

  function timeElement(iso) {
    return el("time", { datetime: iso, title: iso, text: formatDate(iso) });
  }

  function badge(code) {
    const [label, tone] = statusInfo[code] || [`Estado desconocido: ${code}`, "neutral"];
    return el("span", { className: `osint-badge osint-${tone}`, text: label });
  }

  function comparable(value) {
    return typeof value === "string" ? value.trim().toLowerCase().replace(/\.$/, "") : "";
  }

  // undefined: entidades sin cargar; null: sin coincidencia; objeto: entidad existente.
  function findEntity(entityType, value) {
    if (typeof state === "undefined" || !state.ready) return undefined;
    const wanted = comparable(value);
    return state.entities.find((entity) => entity.tipo === entityType
      && (comparable(entity.valor_normalizado) === wanted || comparable(entity.valor) === wanted)) || null;
  }

  function dupeText(entityType, value) {
    const match = findEntity(entityType, value);
    if (match === undefined) return ["unknown", "Comparación no disponible: las entidades aún no se cargaron."];
    if (match === null) return ["none", "Sin coincidencia con las entidades existentes."];
    return ["dupe", `Posible duplicado: ya existe la entidad #${match.id} (${match.valor}).`];
  }

  function dupeNode(entityType, value) {
    const node = el("p", { className: "osint-dupe", "data-entity-type": entityType, "data-value": value });
    paintDupe(node);
    return node;
  }

  function paintDupe(node) {
    const [kind, text] = dupeText(node.dataset.entityType, node.dataset.value);
    node.dataset.kind = kind;
    node.textContent = text;
  }

  function selectedRecords() {
    if (!preview) return [];
    return preview.result.registros.filter((record) => esIncorporable(record) && preview.selected.has(recordKey(record)));
  }

  // Los controles de incorporación reflejan el estado: sin revisión no hay selección posible.
  function updateIncorporation() {
    const records = selectedRecords();
    const countA = records.filter((record) => record.tipo === "A").length;
    const countAAAA = records.filter((record) => record.tipo === "AAAA").length;
    $("#osint-incorporate-count").textContent = records.length
      ? `Seleccionados para incorporar: ${plural(records.length, "registro", "registros")} (A: ${countA}, AAAA: ${countAAAA}).`
      : "No hay registros seleccionados para incorporar.";
    $("#osint-incorporate-open").disabled = !records.length || incorporating || graphPending;
    $("#osint-incorporate-refresh").hidden = !graphPending;
    if (!preview) return;
    for (const input of $("#osint-preview").querySelectorAll("input[data-incorporar]")) {
      const key = input.dataset.key;
      input.disabled = incorporating || !preview.reviewed.has(key) || preview.incorporated.has(key);
      input.checked = preview.selected.has(key);
    }
  }

  function updateCounters() {
    const root = $("#osint-preview");
    const dupes = root.querySelectorAll(".osint-dupe[data-kind=dupe]").length;
    const duplicateCounter = root.querySelector("#osint-dupe-count");
    if (duplicateCounter) duplicateCounter.textContent = String(dupes);
    const reviewCounter = root.querySelector("#osint-review-count");
    if (reviewCounter && preview) {
      reviewCounter.textContent = `${preview.reviewed.size} de ${preview.result.registros.length}`;
    }
    updateIncorporation();
  }

  function updateDuplicates() {
    for (const node of $("#osint-preview").querySelectorAll(".osint-dupe")) paintDupe(node);
    updateCounters();
  }

  function persist() {
    try {
      if (!preview) sessionStorage.removeItem(storageKey);
      else sessionStorage.setItem(storageKey, JSON.stringify({
        result: preview.result,
        reviewed: [...preview.reviewed],
        selected: [...preview.selected],
        incorporated: [...preview.incorporated],
      }));
    } catch (error) {
      // Sin sessionStorage la vista previa solo dura mientras la página siga abierta.
    }
  }

  function restore() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey) || "null");
      if (saved && validResult(saved.result) && Array.isArray(saved.reviewed)) {
        const keys = new Set(saved.result.registros.map(recordKey));
        const incorporable = new Set(saved.result.registros.filter(esIncorporable).map(recordKey));
        const within = (list, allowed) => (Array.isArray(list) ? list.filter((key) => allowed.has(key)) : []);
        const reviewed = new Set(saved.reviewed.filter((key) => keys.has(key)));
        preview = {
          result: saved.result,
          reviewed,
          selected: new Set(within(saved.selected, incorporable).filter((key) => reviewed.has(key))),
          incorporated: new Set(within(saved.incorporated, incorporable)),
        };
        return true;
      }
    } catch (error) {
      sessionStorage.removeItem(storageKey);
    }
    return false;
  }

  function definitionList(items) {
    const list = el("dl", { className: "osint-summary" });
    for (const [label, value] of items) list.append(el("div", {}, el("dt", { text: label }), el("dd", {}, value)));
    return list;
  }

  function summary(result) {
    const errors = result.estados.filter((item) => item.estado.startsWith("error_")).length;
    return definitionList([
      ["Dominio consultado", el("span", { text: result.dominio })],
      ["Fuente", el("span", { text: result.fuente })],
      ["Consultado", timeElement(result.consultado_en)],
      ["Registros encontrados", el("span", { text: String(result.registros.length) })],
      ["Tipos con error", el("span", { text: `${errors} de ${result.estados.length}` })],
      ["Posibles duplicados", el("span", { id: "osint-dupe-count", text: "0" })],
      ["Revisados", el("span", { id: "osint-review-count", text: "" })],
    ]);
  }

  // Solo A y AAAA pueden incorporarse. CNAME, MX y NS se muestran sin control de selección.
  function incorporationControl(record, key) {
    if (!esIncorporable(record)) {
      return el("p", { className: "osint-note", text: "No incorporable todavía: solo se incorporan A y AAAA." });
    }
    const checkbox = el("input", { type: "checkbox", "data-key": key, "data-incorporar": "" });
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) preview.selected.add(key);
      else preview.selected.delete(key);
      persist();
      updateCounters();
    });
    return el("label", { className: "osint-review" }, checkbox, " Incorporar al grafo",
      el("span", { className: "visually-hidden", text: `: ${record.tipo} ${record.valor}` }));
  }

  function recordItem(record) {
    const key = recordKey(record);
    const checkbox = el("input", { type: "checkbox", "data-key": key, "data-revisado": "" });
    checkbox.checked = preview.reviewed.has(key);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        preview.reviewed.add(key);
      } else {
        preview.reviewed.delete(key);
        preview.selected.delete(key);
      }
      persist();
      updateCounters();
    });
    const label = el("label", { className: "osint-review" }, checkbox, " Revisado",
      el("span", { className: "visually-hidden", text: `: ${record.tipo} ${record.valor}` }));
    const meta = el("p", { className: "osint-meta" }, record.fuente, " · ", timeElement(record.consultado_en));
    const head = el("div", { className: "osint-record-head" }, el("strong", { className: "osint-value", text: record.valor }), badge(record.estado));
    if (record.prioridad !== null && record.prioridad !== undefined) {
      head.append(el("span", { className: "osint-priority", text: `Prioridad ${record.prioridad}` }));
    }
    if (preview.incorporated.has(key)) head.append(el("span", { className: "osint-badge osint-ok", text: "Incorporado" }));
    const entityType = equivalentEntityType[record.tipo];
    const item = el("li", {}, head, meta);
    if (entityType) item.append(dupeNode(entityType, record.valor));
    item.append(el("div", { className: "osint-review-row" }, label, incorporationControl(record, key)));
    return item;
  }

  function group(result, status, index) {
    const records = result.registros.filter((record) => record.tipo === status.tipo);
    const [, , explanation] = statusInfo[status.estado] || [];
    const titleId = `osint-group-${index}`;
    const title = el("h3", { id: titleId }, status.tipo, " ", el("span", { className: "muted", text: dnsTypes[status.tipo] ? `· ${dnsTypes[status.tipo]}` : "" }));
    const section = el("section", { className: "osint-group", "aria-labelledby": titleId },
      el("div", { className: "osint-group-head" }, title, badge(status.estado)),
      el("p", { className: "osint-meta" },
        `Registros: ${records.length} · Descartados por validación: ${status.descartados}`));
    if (explanation) section.append(el("p", { className: "osint-explain", text: explanation }));
    else if (!statusInfo[status.estado]) section.append(el("p", { className: "osint-explain", text: "El servidor informó un estado que esta vista no reconoce." }));
    if (records.length) {
      const list = el("ul", { className: "osint-records" });
      for (const record of records) list.append(recordItem(record));
      section.append(list);
    }
    return section;
  }

  function render() {
    const root = $("#osint-preview");
    if (!preview) {
      root.replaceChildren(el("p", { className: "muted", text: "Todavía no hay una consulta. Ingresá un dominio y elegí los tipos de registro." }));
      return;
    }
    const { result } = preview;
    const orderedTypes = Object.keys(dnsTypes);
    const statuses = [...result.estados];
    for (const record of result.registros) {
      if (!statuses.some((status) => status.tipo === record.tipo)) statuses.push({ tipo: record.tipo, estado: record.estado, descartados: 0 });
    }
    statuses.sort((a, b) => orderedTypes.indexOf(a.tipo) - orderedTypes.indexOf(b.tipo));

    const domainEntity = dupeNode("DOMINIO", result.dominio);
    domainEntity.classList.add("osint-domain-dupe");
    const clear = el("button", { type: "button", id: "osint-clear", text: "Limpiar vista previa" });
    clear.addEventListener("click", () => {
      closeConfirm(false);
      preview = null;
      persist();
      render();
      resetIncorporationOutput();
      message($("#osint-message"), "");
      $("#osint-domain").focus();
    });
    root.replaceChildren(
      el("p", { className: "osint-banner", text: "No se guardó nada. No se crearon entidades, relaciones ni evidencias." }),
      summary(result),
      domainEntity,
      el("p", { className: "field-help", text: "Los duplicados se detectan por tipo equivalente (A y AAAA con IP; CNAME, MX y NS con Dominio) y por valor sin distinguir mayúsculas. La política de normalización aún no está definida." }),
      ...statuses.map((status, index) => group(result, status, index)),
      clear,
    );
    updateCounters();
  }

  function setBusy(value) {
    busy = value;
    $("#osint-controls").disabled = value;
    $("#osint-submit").textContent = value ? "Consultando…" : "Consultar DNS";
    $("#osint-preview").setAttribute("aria-busy", String(value));
    $("#osint-preview").classList.toggle("is-loading", value);
  }

  // Durante la incorporación se bloquean la consulta y la selección: el lote enviado debe coincidir con la vista.
  function setIncorporating(value) {
    incorporating = value;
    $("#osint-controls").disabled = value;
    $("#osint-incorporate-open").textContent = value ? "Incorporando…" : "Revisar incorporación";
    const clear = $("#osint-clear");
    if (clear) clear.disabled = value;
    $("#osint-preview").setAttribute("aria-busy", String(value));
    $("#osint-preview").classList.toggle("is-loading", value);
    updateIncorporation();
  }

  function explainError(error, timedOut) {
    if (timedOut) return "La consulta tardó demasiado y se canceló. Probá de nuevo en unos minutos.";
    if (error instanceof SyntaxError) return "El servidor respondió, pero la respuesta no se pudo interpretar. Probá de nuevo más tarde.";
    if (!error.status) return error.message;
    if (error.status === 422) return `El servidor rechazó la consulta: ${error.message}`;
    if (error.status >= 500) return `El servidor no pudo completar la consulta (HTTP ${error.status}). Probá de nuevo más tarde.`;
    return `La consulta falló (HTTP ${error.status}): ${error.message}`;
  }

  function resetIncorporationOutput() {
    $("#osint-incorporate-result").replaceChildren();
    if (!graphPending) message($("#osint-incorporate-message"), "");
  }

  function closeConfirm(restoreFocus) {
    const panel = $("#osint-confirm");
    panel.hidden = true;
    panel.replaceChildren();
    if (restoreFocus) $("#osint-incorporate-open").focus();
  }

  // El panel se abre con un clic deliberado y el foco va al título: nada se envía hasta confirmar.
  function openConfirm() {
    if (!preview || incorporating) return;
    const output = $("#osint-incorporate-message");
    const solicitud = construirSolicitudIncorporacion(preview.result, preview.selected);
    const invalid = motivoSolicitudInvalida(solicitud);
    if (invalid) {
      message(output, invalid, "error");
      return;
    }
    const types = incorporableTypes
      .map((tipo) => ({ tipo, total: solicitud.registros.filter((record) => record.tipo === tipo).length }))
      .filter((item) => item.total)
      .map((item) => `${item.total} ${item.tipo}`)
      .join(" y ");
    const fuentes = [...new Set(solicitud.registros.map((record) => record.fuente))].join(", ");
    const consultas = [...new Set(solicitud.registros.map((record) => formatDate(record.consultado_en)))].join(", ");
    const heading = el("h4", { id: "osint-confirm-title", tabindex: "-1", text: "Confirmar incorporación al grafo" });
    const send = el("button", { type: "button", className: "primary", id: "osint-confirm-send", text: "Confirmar incorporación" });
    send.addEventListener("click", incorporate);
    const cancel = el("button", { type: "button", id: "osint-confirm-cancel", text: "Cancelar" });
    cancel.addEventListener("click", () => closeConfirm(true));
    $("#osint-confirm").replaceChildren(
      heading,
      el("p", {}, "Dominio de origen: ", el("strong", { text: solicitud.dominio })),
      el("p", { text: `Se incorporarán ${plural(solicitud.registros.length, "registro", "registros")}: ${types}.` }),
      el("ul", { className: "osint-confirm-list" }, ...solicitud.registros.map((record) => el("li", { text: `${record.tipo} ${record.valor}` }))),
      el("p", { className: "field-help", text: "Se crearán o reutilizarán en el grafo el dominio, las direcciones IP, las relaciones APUNTA_A y las evidencias. Lo que ya existe se reutiliza." }),
      el("p", { className: "field-help", text: `Procedencia declarada por el cliente, no verificada por el servidor. Fuente: ${fuentes}. Consulta: ${consultas}.` }),
      el("div", { className: "osint-confirm-actions" }, send, cancel),
    );
    $("#osint-confirm").hidden = false;
    heading.focus();
  }

  function markIncorporated(keys) {
    for (const key of keys) {
      preview.incorporated.add(key);
      preview.selected.delete(key);
    }
    persist();
    render();
  }

  function renderIncorporationResult(resumen) {
    const describe = (item) => `Creadas: ${item.creados} · Reutilizadas: ${item.reutilizados}`;
    const title = el("h4", { id: "osint-result-title", tabindex: "-1", text: "Resultado de la incorporación" });
    const list = el("ul", { className: "osint-incorporate-list" },
      ...resumen.registros.map((record) => el("li", {
        text: `${record.tipo} ${record.valor}: entidad ${record.entidad}, relación ${record.relacion}, evidencia ${record.evidencia}.`,
      })));
    $("#osint-incorporate-result").replaceChildren(title, definitionList([
      ["Dominio", `${preview.result.dominio}: ${resumen.dominio === "creada" ? "creado" : "reutilizado"}`],
      ["Entidades IP", describe(resumen.entidades)],
      ["Relaciones APUNTA_A", describe(resumen.relaciones)],
      ["Evidencias", describe(resumen.evidencias)],
      ["Procedencia", `Declarada por el cliente. Fuente: ${resumen.fuentes.join(", ")}. Consulta: ${resumen.consultados.map(formatDate).join(", ")}. El servidor no verificó esta consulta.`],
    ]), list);
  }

  function causaIncierta(error, timedOut) {
    if (timedOut) return "La respuesta tardó demasiado.";
    if (error.status) return `El servidor respondió con HTTP ${error.status} y no confirmó el resultado.`;
    return "No se recibió una respuesta válida del servidor.";
  }

  // El detalle lo escribe el backend, a veces sin punto final.
  function frase(text) {
    return /[.!?]$/.test(text) ? text : `${text}.`;
  }

  function mensajeFallo(kind, error, timedOut) {
    if (kind === "validacion") return `El servidor rechazó el lote. No se incorporó nada. Detalle: ${frase(error.message)} Revisá la selección.`;
    if (kind === "conflicto") return `Existe un conflicto o una ambigüedad con entidades del grafo. El lote no se incorporó. Detalle: ${frase(error.message)} Revisá las entidades duplicadas antes de reintentar.`;
    if (kind === "ocupada") return "La base de datos está ocupada por otra operación. El lote no se incorporó. Podés volver a intentarlo en unos segundos.";
    if (kind === "guardado_sin_grafo") return "Los datos del lote se guardaron, pero no se pudo actualizar la visualización del grafo. Usá Actualizar grafo para recuperarla; no hace falta volver a incorporar el lote.";
    return `${causaIncierta(error, timedOut)} No se puede confirmar si el lote se guardó. Usá Actualizar grafo para comprobarlo antes de reintentar; los registros que ya estén en el grafo aparecen como posible duplicado.`;
  }


  async function incorporate() {
    if (incorporating || !preview) return;
    const solicitud = construirSolicitudIncorporacion(preview.result, preview.selected);
    const output = $("#osint-incorporate-message");
    const invalid = motivoSolicitudInvalida(solicitud);
    if (invalid) {
      message(output, invalid, "error");
      return;
    }
    const sentKeys = selectedRecords().map(recordKey);
    const controller = new AbortController();
    let timedOut = false;
    const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, incorporationTimeoutMs);
    let succeeded = false;
    closeConfirm(false);
    setIncorporating(true);
    message(output, `Incorporando ${plural(solicitud.registros.length, "registro", "registros")} de ${solicitud.dominio}…`);
    try {
      const response = await api("/osint/dns/incorporaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(solicitud),
        signal: controller.signal,
      });
      if (!respuestaIncorporacionValida(response)) throw new Error("La respuesta no tiene el formato esperado.");
      markIncorporated(sentKeys);
      renderIncorporationResult(resumirIncorporacion(response));
      succeeded = true;
      message(output, "Actualizando el grafo…");
      graphPending = !(await refresh({ selection: state.selection }));
      if (graphPending) {
        message(output, "Los datos se guardaron, pero no se pudo actualizar el grafo. Usá Actualizar grafo para recuperarlo.", "error");
      } else {
        message(output, "Incorporación completada. El grafo muestra los datos guardados.", "success");
      }
    } catch (error) {
      const kind = clasificarFalloIncorporacion(error);
      if (kind === "guardado_sin_grafo") markIncorporated(sentKeys);
      if (kind === "guardado_sin_grafo" || kind === "incierto") graphPending = true;
      message(output, mensajeFallo(kind, error, timedOut), "error");
    } finally {
      window.clearTimeout(timer);
      setIncorporating(false);
      if (graphPending) $("#osint-incorporate-refresh").focus();
      else if (succeeded) $("#osint-result-title").focus();
      else $("#osint-incorporate-open").focus();
    }
  }

  // Refresca el grafo sin reintentar el lote: el reintento solo se permite tras ver el estado real.
  async function recoverGraph() {
    const output = $("#osint-incorporate-message");
    const button = $("#osint-incorporate-refresh");
    button.disabled = true;
    message(output, "Actualizando el grafo…");
    const refreshed = await refresh({ selection: state.selection });
    button.disabled = false;
    if (refreshed) {
      if (!$("#osint-incorporate-open").disabled) $("#osint-incorporate-open").focus();
      return;
    }
    message(output, "No se pudo actualizar el grafo. Revisá que el servidor esté en ejecución y probá de nuevo.", "error");
    button.focus();
  }

  // Cualquier actualización del grafo cierra el estado pendiente, no solo la de recuperación.
  function onGraphUpdated() {
    if (!graphPending) return;
    graphPending = false;
    updateIncorporation();
    message($("#osint-incorporate-message"), "El grafo se actualizó. Ya podés revisar la incorporación.", "success");
  }

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const output = $("#osint-message");
    const domain = $("#osint-domain").value.trim();
    const types = Object.keys(dnsTypes).filter((type) => $(`#osint-type-${type}`).checked);
    if (!domain) { message(output, "Ingresá un dominio.", "error"); $("#osint-domain").focus(); return; }
    if (domain.length > maxDomainLength) { message(output, `El dominio no puede superar ${maxDomainLength} caracteres.`, "error"); $("#osint-domain").focus(); return; }
    if (!types.length) { message(output, "Elegí al menos un tipo de registro.", "error"); $("#osint-type-A").focus(); return; }

    closeConfirm(false);
    setBusy(true);
    message(output, `Consultando ${domain}. Puede tardar unos segundos.`);
    const controller = new AbortController();
    let timedOut = false;
    const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, requestTimeoutMs);
    try {
      const result = await api("/osint/dns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dominio: domain, tipos: types }),
        signal: controller.signal,
      });
      if (!validResult(result)) throw new Error("El servidor devolvió una respuesta con un formato inesperado.");
      // Una consulta nueva descarta la selección anterior: no se conserva nada de la vista previa vieja.
      preview = { result, reviewed: new Set(), selected: new Set(), incorporated: new Set() };
      persist();
      render();
      resetIncorporationOutput();
      const errors = result.estados.filter((item) => item.estado.startsWith("error_")).length;
      message(output,
        `Consulta completada: ${plural(result.registros.length, "registro", "registros")} en ${plural(result.estados.length, "tipo consultado", "tipos consultados")}`
        + (errors ? `; ${plural(errors, "tipo con error", "tipos con error")}.` : "."),
        errors ? "" : "success");
    } catch (error) {
      message(output, explainError(error, timedOut), "error");
    } finally {
      window.clearTimeout(timer);
      setBusy(false);
      const submitButton = $("#osint-submit");
      (submitButton.disabled ? $("#osint-domain") : submitButton).focus();
    }
  }

  $("#osint-form").addEventListener("submit", submit);
  $("#osint-incorporate-open").addEventListener("click", openConfirm);
  $("#osint-incorporate-refresh").addEventListener("click", recoverGraph);
  $("#osint-confirm").addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeConfirm(true);
  });
  document.addEventListener("mmg:datos-actualizados", onGraphUpdated);
  new MutationObserver(() => { if (preview) updateDuplicates(); })
    .observe($("#entity-list"), { childList: true });
  if (restore()) {
    $("#osint-domain").value = preview.result.dominio;
    message($("#osint-message"), "Se restauró la última vista previa de esta sesión.");
  }
  render();
})();
